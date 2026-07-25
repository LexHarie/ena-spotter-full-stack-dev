from datetime import timedelta

from trips.domain.types import (
    DutyEvent,
    DutyStatus,
    EventKind,
    Location,
    NormalizedRoute,
    RouteLeg,
    TripRequest,
)

PICKUP_MINUTES = 60
DROPOFF_MINUTES = 60
BREAK_AFTER_DRIVING_MINUTES = 8 * 60
MAX_DRIVING_MINUTES = 11 * 60
MAX_SHIFT_MINUTES = 14 * 60
BREAK_MINUTES = 30
DAILY_REST_MINUTES = 10 * 60
MAX_CYCLE_MINUTES = 70 * 60
CYCLE_RESTART_MINUTES = 34 * 60
FUEL_INTERVAL_M = round(1000 * 1609.344)
FUEL_MINUTES = 30


class Scheduler:
    def __init__(self, request: TripRequest, route: NormalizedRoute) -> None:
        self.request = request
        self.route = route
        self.now = request.starts_at
        self.route_progress_m = 0
        self.cycle_used_minutes = request.cycle_used_minutes
        self.events: list[DutyEvent] = []
        self.shift_elapsed_minutes = 0
        self.shift_driving_minutes = 0
        self.driving_since_break_minutes = 0
        self.next_fuel_at_m = FUEL_INTERVAL_M

    def _append(
        self,
        kind: EventKind,
        status: DutyStatus,
        duration_minutes: int,
        route_end_m: int,
        location: Location,
        remark: str,
    ) -> None:
        start = self.now
        end = start + timedelta(minutes=duration_minutes)
        cycle_before = self.cycle_used_minutes
        if status in {DutyStatus.DRIVING, DutyStatus.ON_DUTY}:
            self.cycle_used_minutes += duration_minutes
        self.events.append(
            DutyEvent(
                id=f"event-{len(self.events) + 1:03d}",
                kind=kind,
                duty_status=status,
                start_at=start,
                end_at=end,
                route_start_m=self.route_progress_m,
                route_end_m=route_end_m,
                location=location,
                remark=remark,
                cycle_used_before_minutes=cycle_before,
                cycle_used_after_minutes=self.cycle_used_minutes,
            )
        )
        self.now = end
        self.route_progress_m = route_end_m

    def _drive_leg(self, leg: RouteLeg) -> None:
        for step in leg.steps:
            remaining_minutes = step.duration_minutes
            remaining_distance_m = step.distance_m
            while remaining_minutes:
                if self.cycle_used_minutes >= MAX_CYCLE_MINUTES:
                    self._take_cycle_restart()
                if (
                    self.shift_driving_minutes >= MAX_DRIVING_MINUTES
                    or self.shift_elapsed_minutes >= MAX_SHIFT_MINUTES
                ):
                    self._take_daily_rest()
                if (
                    self.route_progress_m >= self.next_fuel_at_m
                    and self.route_progress_m < self.route.distance_m
                ):
                    self._take_fuel_stop()
                if self.driving_since_break_minutes >= BREAK_AFTER_DRIVING_MINUTES:
                    self._take_break()

                capacity = min(
                    remaining_minutes,
                    BREAK_AFTER_DRIVING_MINUTES - self.driving_since_break_minutes,
                    MAX_DRIVING_MINUTES - self.shift_driving_minutes,
                    MAX_SHIFT_MINUTES - self.shift_elapsed_minutes,
                    MAX_CYCLE_MINUTES - self.cycle_used_minutes,
                )
                distance_until_fuel = self.next_fuel_at_m - self.route_progress_m
                if 0 < distance_until_fuel < remaining_distance_m:
                    minutes_until_fuel = (
                        remaining_minutes * distance_until_fuel
                    ) // remaining_distance_m
                    quarter_minutes = (minutes_until_fuel // 15) * 15
                    if quarter_minutes == 0:
                        self._take_fuel_stop()
                        continue
                    capacity = min(capacity, quarter_minutes)
                if capacity <= 0:
                    continue
                chunk_distance_m = (
                    remaining_distance_m
                    if capacity == remaining_minutes
                    else (remaining_distance_m * capacity) // remaining_minutes
                )
                self._append(
                    EventKind.DRIVING,
                    DutyStatus.DRIVING,
                    capacity,
                    self.route_progress_m + chunk_distance_m,
                    leg.start,
                    step.instruction or f"Drive toward {leg.end.label}",
                )
                self.shift_elapsed_minutes += capacity
                self.shift_driving_minutes += capacity
                self.driving_since_break_minutes += capacity
                remaining_minutes -= capacity
                remaining_distance_m -= chunk_distance_m

    def _take_break(self) -> None:
        self._append(
            EventKind.BREAK,
            DutyStatus.OFF_DUTY,
            BREAK_MINUTES,
            self.route_progress_m,
            self.events[-1].location,
            "30-minute break",
        )
        self.shift_elapsed_minutes += BREAK_MINUTES
        self.driving_since_break_minutes = 0

    def _take_daily_rest(self) -> None:
        self._append(
            EventKind.DAILY_REST,
            DutyStatus.SLEEPER_BERTH,
            DAILY_REST_MINUTES,
            self.route_progress_m,
            self.events[-1].location,
            "10-hour sleeper-berth rest",
        )
        self.shift_elapsed_minutes = 0
        self.shift_driving_minutes = 0
        self.driving_since_break_minutes = 0

    def _take_cycle_restart(self) -> None:
        location = self.events[-1].location if self.events else self.request.current_location
        self._append(
            EventKind.CYCLE_RESTART,
            DutyStatus.OFF_DUTY,
            CYCLE_RESTART_MINUTES,
            self.route_progress_m,
            location,
            "34-hour cycle restart",
        )
        self.cycle_used_minutes = 0
        last = self.events[-1]
        self.events[-1] = DutyEvent(
            id=last.id,
            kind=last.kind,
            duty_status=last.duty_status,
            start_at=last.start_at,
            end_at=last.end_at,
            route_start_m=last.route_start_m,
            route_end_m=last.route_end_m,
            location=last.location,
            remark=last.remark,
            cycle_used_before_minutes=last.cycle_used_before_minutes,
            cycle_used_after_minutes=0,
        )
        self.shift_elapsed_minutes = 0
        self.shift_driving_minutes = 0
        self.driving_since_break_minutes = 0

    def _take_fuel_stop(self) -> None:
        location = self.events[-1].location
        self._service(
            EventKind.FUEL,
            location,
            FUEL_MINUTES,
            "Fuel stop",
        )
        self.next_fuel_at_m = self.route_progress_m + FUEL_INTERVAL_M

    def _ensure_cycle_capacity(self, required_minutes: int) -> None:
        if self.cycle_used_minutes + required_minutes > MAX_CYCLE_MINUTES:
            self._take_cycle_restart()

    def _service(
        self,
        kind: EventKind,
        location: Location,
        duration_minutes: int,
        remark: str,
    ) -> None:
        self._ensure_cycle_capacity(duration_minutes)
        self._append(
            kind,
            DutyStatus.ON_DUTY,
            duration_minutes,
            self.route_progress_m,
            location,
            remark,
        )
        self.shift_elapsed_minutes += duration_minutes
        if duration_minutes >= BREAK_MINUTES:
            self.driving_since_break_minutes = 0

    def build(self) -> tuple[DutyEvent, ...]:
        first_leg, second_leg = self.route.legs
        self._drive_leg(first_leg)
        self._service(
            EventKind.PICKUP,
            self.request.pickup_location,
            PICKUP_MINUTES,
            "Pickup",
        )
        self._drive_leg(second_leg)
        self._service(
            EventKind.DROPOFF,
            self.request.dropoff_location,
            DROPOFF_MINUTES,
            "Drop-off",
        )
        return tuple(self.events)


def build_schedule(
    request: TripRequest,
    route: NormalizedRoute,
) -> tuple[DutyEvent, ...]:
    if len(route.legs) != 2:
        raise ValueError("A trip route must contain current-to-pickup and pickup-to-drop-off legs.")
    if (
        sum(leg.distance_m for leg in route.legs) != route.distance_m
        or sum(leg.duration_minutes for leg in route.legs) != route.driving_minutes
        or any(
            sum(step.distance_m for step in leg.steps) != leg.distance_m
            or sum(step.duration_minutes for step in leg.steps) != leg.duration_minutes
            for leg in route.legs
        )
    ):
        raise ValueError("Route leg and step totals must match the route.")
    return Scheduler(request, route).build()
