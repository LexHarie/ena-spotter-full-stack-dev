from dataclasses import replace
from datetime import datetime, timedelta, timezone

from conftest import make_route

from trips.domain.projector import build_daily_logs
from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind


def test_each_projected_day_has_exactly_1440_minutes(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            22,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=600,
    )
    events = build_schedule(request, route)

    logs = build_daily_logs(request, route, events)

    assert len(logs) >= 2
    assert logs[0].cycle_used_start_minutes == 24 * 60
    assert logs[0].cycle_added_minutes == 90
    assert logs[0].cycle_remaining_end_minutes == 70 * 60 - (24 * 60 + 90)
    assert sum(log.distance_m for log in logs) == route.distance_m
    for event in events:
        assert (
            sum(
                segment.end_minute - segment.start_minute
                for log in logs
                for segment in log.segments
                if segment.event_id == event.id
            )
            == event.duration_minutes
        )
    for log in logs:
        assert (
            log.off_duty_minutes
            + log.sleeper_berth_minutes
            + log.driving_minutes
            + log.on_duty_minutes
        ) == 1440
        assert log.segments[0].start_minute == 0
        assert log.segments[-1].end_minute == 1440
        assert all(
            left.end_minute == right.start_minute
            for left, right in zip(
                log.segments,
                log.segments[1:],
                strict=False,
            )
        )


def test_projection_splits_an_event_at_midnight(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            23,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=60,
    )

    logs = build_daily_logs(request, route, build_schedule(request, route))

    assert logs[0].segments[-1].end_minute == 1440
    assert logs[1].segments[0].start_minute == 0
    assert logs[0].segments[-1].event_id == logs[1].segments[0].event_id


def test_trip_ending_at_midnight_does_not_create_an_extra_day(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            20,
            0,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )

    logs = build_daily_logs(request, route, build_schedule(request, route))

    assert len(logs) == 1
    assert logs[0].date.isoformat() == "2026-07-25"
    assert logs[0].segments[-1].end_minute == 1440


def test_thirty_four_hour_restart_is_split_across_every_midnight(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        cycle_used_minutes=70 * 60,
        starts_at=datetime(
            2026,
            7,
            25,
            23,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )
    events = build_schedule(request, route)

    logs = build_daily_logs(request, route, events)
    restart = next(event for event in events if event.kind == EventKind.CYCLE_RESTART)
    restart_segments = [
        segment for log in logs for segment in log.segments if segment.event_id == restart.id
    ]

    assert len(restart_segments) == 3
    assert sum(segment.end_minute - segment.start_minute for segment in restart_segments) == 34 * 60
