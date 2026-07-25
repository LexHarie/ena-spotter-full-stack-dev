import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.errors import error_response
from trips.serializers import TripPlanRequestSerializer, serialize_plan
from trips.services.ors_client import ProviderError
from trips.services.planner import TripPlanner
from trips.services.provider import get_routing_provider

logger = logging.getLogger(__name__)


class HealthView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request):
        return Response({"status": "ok"})


class LocationSearchView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 3:
            return Response({"locations": []})
        if len(query) > 160:
            return error_response(
                "VALIDATION_ERROR",
                "Location search must be 160 characters or fewer.",
                status_code=status.HTTP_400_BAD_REQUEST,
                field="q",
            )
        try:
            locations = get_routing_provider().search_locations(query)
        except ProviderError as exc:
            return error_response(
                exc.code,
                exc.message,
                status_code=exc.status_code,
                retryable=exc.retryable,
            )
        return Response(
            {
                "locations": [
                    {
                        "id": location.id,
                        "label": location.label,
                        "longitude": location.coordinate.longitude,
                        "latitude": location.coordinate.latitude,
                        "country_code": location.country_code,
                    }
                    for location in locations
                ]
            }
        )


class TripPlanView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def post(self, request):
        serializer = TripPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = TripPlanner(get_routing_provider()).plan(serializer.to_domain())
        except ProviderError as exc:
            return error_response(
                exc.code,
                exc.message,
                status_code=exc.status_code,
                retryable=exc.retryable,
            )
        except ValueError:
            logger.exception(
                "Trip planning invariant failed",
                extra={
                    "home_terminal_timezone": serializer.validated_data.get(
                        "home_terminal_timezone"
                    ),
                    "current_cycle_used_hours": str(
                        serializer.validated_data.get("current_cycle_used_hours")
                    ),
                },
            )
            return error_response(
                "PLANNING_INFEASIBLE",
                "A compliant trip plan could not be generated.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                retryable=False,
            )
        response = Response(serialize_plan(result))
        response["Cache-Control"] = "no-store"
        return response
