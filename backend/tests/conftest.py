from datetime import datetime, timedelta, timezone

import pytest

from trips.domain.types import (
    Coordinate,
    Location,
    NormalizedRoute,
    RouteLeg,
    RouteStep,
    TripRequest,
)


@pytest.fixture
def locations() -> tuple[Location, Location, Location]:
    return (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )


@pytest.fixture
def trip_request(locations) -> TripRequest:
    return TripRequest(
        current_location=locations[0],
        pickup_location=locations[1],
        dropoff_location=locations[2],
        cycle_used_minutes=24 * 60,
        starts_at=datetime(
            2026,
            7,
            25,
            8,
            15,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
        home_terminal_timezone="America/Chicago",
        fixed_utc_offset_minutes=-300,
    )


def make_route(
    locations: tuple[Location, Location, Location],
    *,
    first_minutes: int,
    second_minutes: int,
    first_distance_m: int = 300_000,
    second_distance_m: int = 500_000,
) -> NormalizedRoute:
    first_step = RouteStep(
        "Drive to pickup",
        "I-55 S",
        first_distance_m,
        first_minutes,
        0,
        1,
    )
    second_step = RouteStep(
        "Drive to drop-off",
        "I-40 W",
        second_distance_m,
        second_minutes,
        1,
        2,
    )
    legs = (
        RouteLeg(
            locations[0],
            locations[1],
            first_distance_m,
            first_minutes,
            (first_step,),
        ),
        RouteLeg(
            locations[1],
            locations[2],
            second_distance_m,
            second_minutes,
            (second_step,),
        ),
    )
    return NormalizedRoute(
        geometry=tuple(location.coordinate for location in locations),
        legs=legs,
        distance_m=first_distance_m + second_distance_m,
        driving_minutes=first_minutes + second_minutes,
    )
