from datetime import timedelta

from conftest import make_route

from trips.domain.scheduler import build_schedule
from trips.domain.types import DutyStatus, EventKind


def test_short_route_contains_driving_pickup_and_dropoff(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=180,
    )

    events = build_schedule(trip_request, route)

    assert [event.kind for event in events] == [
        EventKind.DRIVING,
        EventKind.PICKUP,
        EventKind.DRIVING,
        EventKind.DROPOFF,
    ]
    assert [event.duty_status for event in events] == [
        DutyStatus.DRIVING,
        DutyStatus.ON_DUTY,
        DutyStatus.DRIVING,
        DutyStatus.ON_DUTY,
    ]
    assert [event.duration_minutes for event in events] == [120, 60, 180, 60]
    assert events[-1].end_at == trip_request.starts_at + timedelta(hours=7)
    assert events[-1].cycle_used_after_minutes == 31 * 60
    assert events[-1].route_end_m == route.distance_m
