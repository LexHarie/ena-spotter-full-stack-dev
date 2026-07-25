from dataclasses import replace

from conftest import make_route

from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind, RouteStep


def test_break_is_inserted_after_eight_cumulative_driving_hours(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=540,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]
    break_event = events[kinds.index(EventKind.BREAK)]

    assert break_event.duration_minutes == 30
    assert (
        sum(
            event.duration_minutes
            for event in events[: kinds.index(EventKind.BREAK)]
            if event.kind == EventKind.DRIVING
        )
        == 480
    )


def test_exactly_eight_hours_before_pickup_needs_no_extra_break(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=480,
        second_minutes=0,
        second_distance_m=0,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.BREAK not in [event.kind for event in events]


def test_pickup_service_satisfies_the_non_driving_break(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=450,
        second_minutes=450,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.BREAK not in [event.kind for event in events]


def test_daily_rest_is_inserted_before_twelfth_driving_hour(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]
    rest_event = events[kinds.index(EventKind.DAILY_REST)]

    assert rest_event.duration_minutes == 600
    driving_before_rest = sum(
        event.duration_minutes
        for event in events[: kinds.index(EventKind.DAILY_REST)]
        if event.kind == EventKind.DRIVING
    )
    assert driving_before_rest == 660


def test_exactly_eleven_driving_hours_needs_no_daily_rest(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.DAILY_REST not in [event.kind for event in events]
    assert sum(event.duration_minutes for event in events if event.kind == EventKind.DRIVING) == 660


def test_all_transitions_remain_on_quarter_hours(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=180,
    )

    events = build_schedule(trip_request, route)

    assert all(event.start_at.minute % 15 == 0 for event in events)
    assert all(event.end_at.minute % 15 == 0 for event in events)


def test_driving_events_stop_at_provider_route_step_boundaries(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=60,
    )
    first_leg = route.legs[0]
    split_first_leg = replace(
        first_leg,
        steps=(
            RouteStep(
                "Continue on I-55",
                "I-55 S",
                150_000,
                60,
                0,
                1,
            ),
            RouteStep(
                "Take the St. Louis exit",
                "I-55 S",
                150_000,
                60,
                0,
                1,
            ),
        ),
    )
    route = replace(
        route,
        legs=(split_first_leg, route.legs[1]),
    )

    events = build_schedule(trip_request, route)
    pickup_index = next(
        index for index, event in enumerate(events) if event.kind == EventKind.PICKUP
    )

    assert [
        event.duration_minutes for event in events[:pickup_index] if event.kind == EventKind.DRIVING
    ] == [60, 60]
