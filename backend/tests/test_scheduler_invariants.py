from dataclasses import replace

import pytest
from conftest import make_route

from trips.domain.scheduler import FUEL_INTERVAL_M, build_schedule
from trips.domain.types import DutyStatus, EventKind


@pytest.mark.parametrize(
    (
        "cycle_used_minutes",
        "first_minutes",
        "second_minutes",
        "first_distance_m",
        "second_distance_m",
    ),
    [
        (0, 120, 180, 300_000, 500_000),
        (24 * 60, 600, 1200, 900 * 1609, 1300 * 1609),
        (70 * 60, 60, 60, 100_000, 100_000),
    ],
)
def test_generated_schedule_preserves_all_hos_and_route_invariants(
    trip_request,
    locations,
    cycle_used_minutes,
    first_minutes,
    second_minutes,
    first_distance_m,
    second_distance_m,
) -> None:
    request = replace(
        trip_request,
        cycle_used_minutes=cycle_used_minutes,
    )
    route = make_route(
        locations,
        first_minutes=first_minutes,
        second_minutes=second_minutes,
        first_distance_m=first_distance_m,
        second_distance_m=second_distance_m,
    )

    events = build_schedule(request, route)
    previous_end = request.starts_at
    previous_progress_m = 0
    previous_cycle_minutes = request.cycle_used_minutes
    shift_elapsed_minutes = 0
    shift_driving_minutes = 0
    driving_since_break_minutes = 0
    fuel_points_m = [0]

    for event in events:
        assert event.start_at == previous_end
        assert event.duration_minutes > 0
        assert event.route_start_m == previous_progress_m
        assert event.route_start_m <= event.route_end_m <= route.distance_m
        assert event.cycle_used_before_minutes == previous_cycle_minutes
        assert 0 <= event.cycle_used_after_minutes <= 70 * 60

        if event.kind == EventKind.FUEL:
            fuel_points_m.append(event.route_start_m)

        if event.kind in {
            EventKind.DAILY_REST,
            EventKind.CYCLE_RESTART,
        }:
            shift_elapsed_minutes = 0
            shift_driving_minutes = 0
            driving_since_break_minutes = 0
        elif event.duty_status == DutyStatus.DRIVING:
            assert shift_driving_minutes + event.duration_minutes <= 11 * 60
            assert shift_elapsed_minutes + event.duration_minutes <= 14 * 60
            assert driving_since_break_minutes + event.duration_minutes <= 8 * 60
            shift_elapsed_minutes += event.duration_minutes
            shift_driving_minutes += event.duration_minutes
            driving_since_break_minutes += event.duration_minutes
        else:
            shift_elapsed_minutes += event.duration_minutes
            if event.duration_minutes >= 30:
                driving_since_break_minutes = 0

        previous_end = event.end_at
        previous_progress_m = event.route_end_m
        previous_cycle_minutes = event.cycle_used_after_minutes

    fuel_points_m.append(route.distance_m)
    assert previous_progress_m == route.distance_m
    assert all(
        right - left <= FUEL_INTERVAL_M
        for left, right in zip(
            fuel_points_m,
            fuel_points_m[1:],
            strict=False,
        )
    )
    assert [event.duration_minutes for event in events if event.kind == EventKind.PICKUP] == [60]
    assert [event.duration_minutes for event in events if event.kind == EventKind.DROPOFF] == [60]
