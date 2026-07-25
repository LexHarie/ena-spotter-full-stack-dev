from dataclasses import replace

from conftest import make_route

from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind

MILE_M = 1609


def test_fuel_is_scheduled_before_each_thousand_miles(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=1200,
        first_distance_m=900 * MILE_M,
        second_distance_m=1300 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    fuel_events = [event for event in events if event.kind == EventKind.FUEL]

    assert len(fuel_events) == 2
    assert all(event.duration_minutes == 30 for event in fuel_events)
    assert fuel_events[0].route_start_m <= 1000 * MILE_M
    assert fuel_events[1].route_start_m <= 2000 * MILE_M


def test_fuel_resets_the_eight_hour_break_counter(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=0,
        second_minutes=600,
        first_distance_m=0,
        second_distance_m=1340 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]

    assert EventKind.FUEL in kinds
    assert EventKind.BREAK not in kinds


def test_exhausted_cycle_starts_with_a_thirty_four_hour_restart(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=70 * 60)
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )

    events = build_schedule(request, route)

    assert events[0].kind == EventKind.CYCLE_RESTART
    assert events[0].duration_minutes == 34 * 60
    assert events[0].cycle_used_after_minutes == 0


def test_service_is_not_split_when_cycle_capacity_is_too_small(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=69 * 60 + 30)
    route = make_route(
        locations,
        first_minutes=30,
        second_minutes=30,
    )

    events = build_schedule(request, route)
    pickup_index = next(
        index for index, event in enumerate(events) if event.kind == EventKind.PICKUP
    )

    assert events[pickup_index - 1].kind == EventKind.CYCLE_RESTART
    assert events[pickup_index].duration_minutes == 60


def test_dropoff_waits_for_restart_when_only_thirty_cycle_minutes_remain(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=68 * 60)
    route = make_route(
        locations,
        first_minutes=15,
        second_minutes=15,
    )

    events = build_schedule(request, route)
    dropoff_index = next(
        index for index, event in enumerate(events) if event.kind == EventKind.DROPOFF
    )

    assert events[dropoff_index - 1].kind == EventKind.CYCLE_RESTART
    assert events[dropoff_index].duration_minutes == 60


def test_fuel_and_pickup_time_can_trigger_fourteen_hour_rest(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=60,
        first_distance_m=5100 * MILE_M,
        second_distance_m=100 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    for index, event in enumerate(events):
        if event.kind != EventKind.DAILY_REST:
            continue
        shift_elapsed = sum(
            prior.duration_minutes
            for prior in events[:index]
            if prior.kind != EventKind.CYCLE_RESTART
        )
        driving_before_rest = sum(
            prior.duration_minutes for prior in events[:index] if prior.kind == EventKind.DRIVING
        )
        assert shift_elapsed == 14 * 60
        assert driving_before_rest < 11 * 60
        break
    else:
        raise AssertionError("Expected a daily rest before additional driving.")
