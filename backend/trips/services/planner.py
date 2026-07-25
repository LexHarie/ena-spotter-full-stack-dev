from dataclasses import replace
from zoneinfo import ZoneInfo

from trips.domain.projector import build_daily_logs
from trips.domain.scheduler import build_schedule
from trips.domain.types import (
    DutyEvent,
    Location,
    PlanningResult,
    TripRequest,
)
from trips.services.ors_client import RoutingProvider
from trips.services.route_index import RouteIndex


class TripPlanner:
    def __init__(self, provider: RoutingProvider) -> None:
        self.provider = provider

    def _event_location(
        self,
        event: DutyEvent,
        request: TripRequest,
        route_index: RouteIndex,
        pickup_progress_m: int,
        cache: dict[tuple[float, float], Location],
    ) -> Location:
        if event.route_start_m == 0:
            return request.current_location
        if event.route_start_m == pickup_progress_m:
            return request.pickup_location
        if event.route_start_m == route_index.distance_m:
            return request.dropoff_location
        coordinate = route_index.coordinate_at(event.route_start_m)
        key = (round(coordinate.longitude, 4), round(coordinate.latitude, 4))
        if key not in cache:
            cache[key] = self.provider.reverse_geocode(coordinate)
        return cache[key]

    def plan(self, request: TripRequest) -> PlanningResult:
        route = self.provider.build_route(
            (
                request.current_location,
                request.pickup_location,
                request.dropoff_location,
            )
        )
        route_index = RouteIndex(route)
        raw_events = build_schedule(request, route)
        pickup_progress_m = route.legs[0].distance_m
        cache: dict[tuple[float, float], Location] = {}
        events = tuple(
            replace(
                event,
                location=self._event_location(
                    event,
                    request,
                    route_index,
                    pickup_progress_m,
                    cache,
                ),
            )
            for event in raw_events
        )
        logs = build_daily_logs(request, route, events)
        home_zone = ZoneInfo(request.home_terminal_timezone)
        ending_offset = events[-1].end_at.astimezone(home_zone).utcoffset()
        ending_offset_minutes = (
            int(ending_offset.total_seconds() // 60)
            if ending_offset is not None
            else request.fixed_utc_offset_minutes
        )
        warnings = (
            (
                (
                    "This plan crosses a daylight-saving transition and keeps "
                    "the trip-start home-terminal UTC offset."
                ),
            )
            if ending_offset_minutes != request.fixed_utc_offset_minutes
            else ()
        )
        return PlanningResult(
            request=request,
            route=route,
            events=events,
            daily_logs=logs,
            warnings=warnings,
        )
