import pytest

from trips.domain.types import Coordinate, NormalizedRoute
from trips.services.route_index import RouteIndex


def test_coordinate_at_scales_provider_distance_over_geometry() -> None:
    route = NormalizedRoute(
        geometry=(
            Coordinate(0.0, 0.0),
            Coordinate(0.0, 1.0),
            Coordinate(0.0, 2.0),
        ),
        legs=(),
        distance_m=200_000,
        driving_minutes=120,
    )

    coordinate = RouteIndex(route).coordinate_at(100_000)

    assert coordinate.longitude == pytest.approx(0.0)
    assert coordinate.latitude == pytest.approx(1.0, abs=0.01)


def test_coordinate_at_clamps_route_bounds() -> None:
    route = NormalizedRoute(
        geometry=(Coordinate(-1.0, 1.0), Coordinate(1.0, 2.0)),
        legs=(),
        distance_m=100,
        driving_minutes=15,
    )
    index = RouteIndex(route)

    assert index.coordinate_at(-1) == route.geometry[0]
    assert index.coordinate_at(101) == route.geometry[-1]
