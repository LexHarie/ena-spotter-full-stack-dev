from unittest.mock import Mock, patch

from django.test import Client

from trips.domain.types import Coordinate, Location
from trips.serializers import LocationSerializer
from trips.services.ors_client import ProviderError


def test_location_search_returns_normalized_us_candidates() -> None:
    provider = Mock()
    provider.search_locations.return_value = (
        Location(
            "chicago",
            "Chicago, Cook County, Illinois, USA",
            Coordinate(-87.6298, 41.8781),
        ),
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get(
            "/api/v1/locations/search/",
            {"q": "Chicago"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "locations": [
            {
                "id": "chicago",
                "label": "Chicago, Cook County, Illinois, USA",
                "longitude": -87.6298,
                "latitude": 41.8781,
                "country_code": "US",
            }
        ]
    }


def test_short_location_query_does_not_call_provider() -> None:
    provider = Mock()

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get("/api/v1/locations/search/", {"q": "ab"})

    assert response.status_code == 200
    assert response.json() == {"locations": []}
    provider.search_locations.assert_not_called()


def test_provider_failure_uses_stable_error_envelope() -> None:
    provider = Mock()
    provider.search_locations.side_effect = ProviderError(
        "PROVIDER_RATE_LIMITED",
        "The routing service rate limit was reached.",
        True,
        429,
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get(
            "/api/v1/locations/search/",
            {"q": "Chicago"},
        )

    assert response.status_code == 429
    assert response.json()["error"] == {
        "code": "PROVIDER_RATE_LIMITED",
        "message": "The routing service rate limit was reached.",
        "field": None,
        "retryable": True,
    }


def test_location_serializer_rejects_non_finite_coordinates() -> None:
    serializer = LocationSerializer(
        data={
            "id": "invalid",
            "label": "Invalid location",
            "longitude": -87.6298,
            "latitude": float("nan"),
            "country_code": "US",
        }
    )

    assert serializer.is_valid() is False
    assert "latitude" in serializer.errors
