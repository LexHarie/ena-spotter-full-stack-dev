import json
from pathlib import Path

import httpx
import pytest

from trips.domain.types import Coordinate, Location
from trips.services.ors_client import OpenRouteServiceClient, ProviderError

FIXTURE = Path(__file__).parent / "fixtures" / "ors_route.json"


def test_build_route_normalizes_geometry_legs_and_quarter_hours() -> None:
    payload = json.loads(FIXTURE.read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "test-key"
        return httpx.Response(200, json=payload)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )
    locations = (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )

    route = client.build_route(locations)

    assert route.distance_m == 2816350
    assert route.driving_minutes == 1530
    assert len(route.geometry) == 5
    assert [leg.duration_minutes for leg in route.legs] == [270, 1260]
    assert all(sum(step.distance_m for step in leg.steps) == leg.distance_m for leg in route.legs)
    assert route.legs[1].steps[0].road_name == "I-40 W"


def test_search_locations_restricts_to_us_and_caps_results() -> None:
    payload = {
        "features": [
            {
                "properties": {
                    "id": f"id-{index}",
                    "label": f"Result {index}, USA",
                    "country_a": "USA",
                },
                "geometry": {"coordinates": [-87.6 + index / 100, 41.8]},
            }
            for index in range(7)
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["boundary.country"] == "US"
        return httpx.Response(200, json=payload)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    assert len(client.search_locations("Chicago")) == 5


def test_provider_raises_typed_error_after_transient_failure() -> None:
    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(503, json={"error": "unavailable"})
        ),
    )

    with pytest.raises(ProviderError) as error:
        client.search_locations("Chicago")

    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert error.value.retryable is True


def test_provider_retries_a_timeout_then_raises_typed_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectTimeout("timed out", request=request)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError) as error:
        client.search_locations("Chicago")

    assert attempts == 2
    assert error.value.code == "PROVIDER_UNAVAILABLE"


def test_malformed_route_response_raises_typed_provider_error() -> None:
    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"features": [{"geometry": {}}]},
            )
        ),
    )
    locations = (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )

    with pytest.raises(ProviderError) as error:
        client.build_route(locations)

    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert error.value.retryable is True
