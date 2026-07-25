from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from trips.domain.types import (
    DailyLog,
    DailyLogSegment,
    DutyEvent,
    DutyStatus,
    EventKind,
    NormalizedRoute,
    TripRequest,
)

DAY_MINUTES = 24 * 60
MAX_CYCLE_MINUTES = 70 * 60


def _minute_of_day(value: datetime) -> int:
    return value.hour * 60 + value.minute


def _segment(
    event: DutyEvent,
    start_at: datetime,
    end_at: datetime,
) -> DailyLogSegment:
    end_minute = DAY_MINUTES if end_at.date() > start_at.date() else _minute_of_day(end_at)
    return DailyLogSegment(
        event_id=event.id,
        kind=event.kind,
        duty_status=event.duty_status,
        start_minute=_minute_of_day(start_at),
        end_minute=end_minute,
        location=event.location,
        remark=event.remark,
    )


def _off_duty_event(
    event_id: str,
    kind: EventKind,
    start_at: datetime,
    end_at: datetime,
    template: DutyEvent,
    cycle_used_minutes: int,
) -> DutyEvent:
    return DutyEvent(
        id=event_id,
        kind=kind,
        duty_status=DutyStatus.OFF_DUTY,
        start_at=start_at,
        end_at=end_at,
        route_start_m=template.route_start_m,
        route_end_m=template.route_start_m,
        location=template.location,
        remark="Off duty",
        cycle_used_before_minutes=cycle_used_minutes,
        cycle_used_after_minutes=cycle_used_minutes,
    )


def _cycle_at(event: DutyEvent, moment: datetime) -> int:
    if moment <= event.start_at:
        return event.cycle_used_before_minutes
    if moment >= event.end_at:
        return event.cycle_used_after_minutes
    if event.duty_status in {DutyStatus.DRIVING, DutyStatus.ON_DUTY}:
        elapsed_minutes = int((moment - event.start_at).total_seconds() // 60)
        return event.cycle_used_before_minutes + elapsed_minutes
    return event.cycle_used_before_minutes


def _distance_during(
    event: DutyEvent,
    overlap_start: datetime,
    overlap_end: datetime,
) -> int:
    distance_m = event.route_end_m - event.route_start_m
    if distance_m <= 0:
        return 0
    duration_seconds = (event.end_at - event.start_at).total_seconds()
    start_seconds = (overlap_start - event.start_at).total_seconds()
    end_seconds = (overlap_end - event.start_at).total_seconds()
    return round(distance_m * end_seconds / duration_seconds) - round(
        distance_m * start_seconds / duration_seconds
    )


def build_daily_logs(
    request: TripRequest,
    route: NormalizedRoute,
    events: tuple[DutyEvent, ...],
) -> tuple[DailyLog, ...]:
    if not events:
        raise ValueError("Cannot build daily logs without duty events.")
    fixed_zone = timezone(timedelta(minutes=request.fixed_utc_offset_minutes))
    normalized = tuple(
        DutyEvent(
            id=event.id,
            kind=event.kind,
            duty_status=event.duty_status,
            start_at=event.start_at.astimezone(fixed_zone),
            end_at=event.end_at.astimezone(fixed_zone),
            route_start_m=event.route_start_m,
            route_end_m=event.route_end_m,
            location=event.location,
            remark=event.remark,
            cycle_used_before_minutes=event.cycle_used_before_minutes,
            cycle_used_after_minutes=event.cycle_used_after_minutes,
        )
        for event in events
    )
    first_midnight = datetime.combine(
        normalized[0].start_at.date(),
        time.min,
        fixed_zone,
    )
    last_end = normalized[-1].end_at
    final_midnight = (
        last_end
        if last_end.time() == time.min
        else datetime.combine(
            last_end.date() + timedelta(days=1),
            time.min,
            fixed_zone,
        )
    )
    timeline = [
        _off_duty_event(
            "pre-trip-off-duty",
            EventKind.PRE_TRIP_OFF_DUTY,
            first_midnight,
            normalized[0].start_at,
            normalized[0],
            normalized[0].cycle_used_before_minutes,
        ),
        *normalized,
        _off_duty_event(
            "post-trip-off-duty",
            EventKind.POST_TRIP_OFF_DUTY,
            last_end,
            final_midnight,
            normalized[-1],
            normalized[-1].cycle_used_after_minutes,
        ),
    ]

    by_date: dict = defaultdict(list)
    for event in timeline:
        cursor = event.start_at
        while cursor < event.end_at:
            midnight = datetime.combine(
                cursor.date() + timedelta(days=1),
                time.min,
                fixed_zone,
            )
            segment_end = min(event.end_at, midnight)
            by_date[cursor.date()].append(_segment(event, cursor, segment_end))
            cursor = segment_end

    logs: list[DailyLog] = []
    for trip_day, (log_date, segments) in enumerate(sorted(by_date.items()), start=1):
        if (
            segments[0].start_minute != 0
            or segments[-1].end_minute != DAY_MINUTES
            or any(
                left.end_minute != right.start_minute
                for left, right in zip(
                    segments,
                    segments[1:],
                    strict=False,
                )
            )
        ):
            raise ValueError(f"Daily log {log_date} has a gap or overlap.")
        totals = defaultdict(int)
        for segment in segments:
            totals[segment.duty_status] += segment.end_minute - segment.start_minute
        total_minutes = sum(totals.values())
        if total_minutes != DAY_MINUTES:
            raise ValueError(f"Daily log {log_date} totals {total_minutes} minutes.")
        day_start = datetime.combine(log_date, time.min, fixed_zone)
        day_end = day_start + timedelta(days=1)
        day_events = [
            event for event in normalized if event.start_at < day_end and event.end_at > day_start
        ]
        cycle_start = (
            _cycle_at(day_events[0], day_start) if day_events else request.cycle_used_minutes
        )
        cycle_end = _cycle_at(day_events[-1], day_end) if day_events else cycle_start
        driving = totals[DutyStatus.DRIVING]
        on_duty = totals[DutyStatus.ON_DUTY]
        logs.append(
            DailyLog(
                date=log_date,
                trip_day=trip_day,
                start_location=segments[0].location,
                end_location=segments[-1].location,
                distance_m=sum(
                    _distance_during(
                        event,
                        max(event.start_at, day_start),
                        min(event.end_at, day_end),
                    )
                    for event in day_events
                    if event.route_end_m > event.route_start_m
                ),
                segments=tuple(segments),
                off_duty_minutes=totals[DutyStatus.OFF_DUTY],
                sleeper_berth_minutes=totals[DutyStatus.SLEEPER_BERTH],
                driving_minutes=driving,
                on_duty_minutes=on_duty,
                cycle_used_start_minutes=cycle_start,
                cycle_added_minutes=driving + on_duty,
                cycle_remaining_end_minutes=max(0, MAX_CYCLE_MINUTES - cycle_end),
            )
        )
    projected_distance_m = sum(log.distance_m for log in logs)
    if projected_distance_m != route.distance_m:
        raise ValueError("Daily-log distance does not match the normalized route.")
    return tuple(logs)
