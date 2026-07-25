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


class Scheduler:
    def __init__(self, request: TripRequest, route: NormalizedRoute) -> None:
        self.request = request
        self.route = route
        self.now = request.starts_at
        self.route_progress_m = 0
        self.cycle_used_minutes = request.cycle_used_minutes
        self.events: list[DutyEvent] = []

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
        self._append(
            EventKind.DRIVING,
            DutyStatus.DRIVING,
            leg.duration_minutes,
            self.route_progress_m + leg.distance_m,
            leg.start,
            f"Drive toward {leg.end.label}",
        )

    def _service(
        self,
        kind: EventKind,
        location: Location,
        duration_minutes: int,
        remark: str,
    ) -> None:
        self._append(
            kind,
            DutyStatus.ON_DUTY,
            duration_minutes,
            self.route_progress_m,
            location,
            remark,
        )

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
