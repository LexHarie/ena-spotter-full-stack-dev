from unittest.mock import Mock, patch

from conftest import make_route
from django.test import Client

from trips.services.ors_client import ProviderError


def request_payload() -> dict:
    return {
        "current_location": {
            "id": "current",
            "label": "Chicago, IL",
            "longitude": -87.6298,
            "latitude": 41.8781,
            "country_code": "US",
        },
        "pickup_location": {
            "id": "pickup",
            "label": "St. Louis, MO",
            "longitude": -90.1994,
            "latitude": 38.6270,
            "country_code": "US",
        },
        "dropoff_location": {
            "id": "dropoff",
            "label": "Phoenix, AZ",
            "longitude": -112.0740,
            "latitude": 33.4484,
            "country_code": "US",
        },
        "current_cycle_used_hours": "24.00",
        "starts_at": "2026-07-25T08:15:00-05:00",
        "home_terminal_timezone": "America/Chicago",
    }


def test_plan_endpoint_returns_route_events_stops_and_daily_logs(
    locations,
) -> None:
    provider = Mock()
    provider.api_key = "test-provider-secret"
    provider.build_route.return_value = make_route(
        locations,
        first_minutes=180,
        second_minutes=720,
    )
    provider.reverse_geocode.side_effect = lambda coordinate: locations[0]

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    body = response.json()
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert body["meta"]["rule_set_version"] == "property-70-8-v1"
    assert body["meta"]["generated_at"].endswith("+00:00")
    assert body["route"]["geometry"]["type"] == "LineString"
    assert body["route"]["bounds"]["west"] < body["route"]["bounds"]["east"]
    assert body["summary"]["distance_m"] == provider.build_route.return_value.distance_m
    assert body["summary"]["cycle_used_start_minutes"] == 24 * 60
    assert body["events"]
    assert body["stops"]
    assert body["daily_logs"]
    assert "test-provider-secret" not in response.content.decode()
    assert all(sum(log["totals_minutes"].values()) == 1440 for log in body["daily_logs"])


def test_plan_endpoint_rejects_non_quarter_cycle_value() -> None:
    payload = request_payload()
    payload["current_cycle_used_hours"] = "24.10"

    response = Client().post(
        "/api/v1/trips/plan/",
        payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"]["field"] == "current_cycle_used_hours"


def test_plan_endpoint_flattens_nested_location_validation() -> None:
    payload = request_payload()
    payload["pickup_location"]["country_code"] = "CA"

    response = Client().post(
        "/api/v1/trips/plan/",
        payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Select a United States location.",
        "field": "pickup_location",
        "retryable": False,
    }


def test_plan_endpoint_preserves_typed_provider_failure() -> None:
    provider = Mock()
    provider.build_route.side_effect = ProviderError(
        "PROVIDER_UNAVAILABLE",
        "Routing is temporarily unavailable.",
        True,
        503,
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "PROVIDER_UNAVAILABLE",
        "message": "Routing is temporarily unavailable.",
        "field": None,
        "retryable": True,
    }


def test_planning_invariant_failure_returns_no_partial_plan() -> None:
    with (
        patch("trips.views.get_routing_provider", return_value=Mock()),
        patch(
            "trips.views.TripPlanner.plan",
            side_effect=ValueError("broken invariant"),
        ),
    ):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "PLANNING_INFEASIBLE",
            "message": "A compliant trip plan could not be generated.",
            "field": None,
            "retryable": False,
        }
    }


def test_plan_warns_when_fixed_offset_crosses_daylight_saving(
    locations,
) -> None:
    payload = request_payload()
    payload["starts_at"] = "2026-10-31T23:00:00-05:00"
    provider = Mock()
    provider.build_route.return_value = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )
    provider.reverse_geocode.side_effect = lambda coordinate: locations[0]

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            payload,
            content_type="application/json",
        )

    assert response.status_code == 200
    assert any("daylight-saving" in warning for warning in response.json()["meta"]["warnings"])
