import os

from trips.services.ors_client import OpenRouteServiceClient, RoutingProvider


def get_routing_provider() -> RoutingProvider:
    api_key = os.environ.get("ORS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ORS_API_KEY is required.")
    return OpenRouteServiceClient(api_key)
