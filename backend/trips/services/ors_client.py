from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from typing import Protocol

import httpx

from trips.domain.types import (
    Coordinate,
    Location,
    NormalizedRoute,
    RouteLeg,
    RouteStep,
)
from trips.domain.units import ceil_minutes_to_quarter

ORS_BASE_URL = "https://api.openrouteservice.org"


@dataclass(frozen=True)
class ProviderError(Exception):
    code: str
    message: str
    retryable: bool
    status_code: int = 503

    def __str__(self) -> str:
        return self.message


class RoutingProvider(Protocol):
    def search_locations(self, query: str) -> tuple[Location, ...]: ...

    def build_route(
        self,
        waypoints: tuple[Location, Location, Location],
    ) -> NormalizedRoute: ...

    def reverse_geocode(self, coordinate: Coordinate) -> Location: ...


def _coordinate(raw: object) -> Coordinate:
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("Invalid coordinate.")
    longitude = float(raw[0])
    latitude = float(raw[1])
    if (
        not isfinite(longitude)
        or not isfinite(latitude)
        or not -180 <= longitude <= 180
        or not -90 <= latitude <= 90
    ):
        raise ValueError("Invalid coordinate.")
    return Coordinate(longitude, latitude)


def _nonnegative_number(value: object) -> float:
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError("Expected a finite non-negative number.")
    return number


def _parse_route_payload(
    payload: dict,
    waypoints: tuple[Location, Location, Location],
) -> NormalizedRoute:
    features = payload.get("features", [])
    if features == []:
        raise ProviderError(
            "ROUTE_NOT_FOUND",
            "No truck route was found for the selected locations.",
            False,
            422,
        )
    try:
        feature = features[0]
        geometry = tuple(_coordinate(raw) for raw in feature["geometry"]["coordinates"])
        segments = feature["properties"]["segments"]
        if len(geometry) < 2 or len(segments) != 2:
            raise ValueError("Unexpected route shape.")
        legs: list[RouteLeg] = []
        for index, segment in enumerate(segments):
            segment_distance_m = round(_nonnegative_number(segment["distance"]))
            raw_steps = segment["steps"]
            if not raw_steps and segment_distance_m:
                raise ValueError("A non-empty leg requires route steps.")
            remaining_distance_m = segment_distance_m
            normalized_steps: list[RouteStep] = []
            for step_index, step in enumerate(raw_steps):
                is_last = step_index == len(raw_steps) - 1
                raw_step_distance_m = round(_nonnegative_number(step["distance"]))
                step_distance_m = (
                    remaining_distance_m
                    if is_last
                    else min(raw_step_distance_m, remaining_distance_m)
                )
                duration_minutes = ceil_minutes_to_quarter(
                    ceil(_nonnegative_number(step["duration"]) / 60)
                )
                if step_distance_m and duration_minutes == 0:
                    raise ValueError("A moving step requires duration.")
                geometry_start_index, geometry_end_index = step["way_points"]
                if not (0 <= geometry_start_index <= geometry_end_index < len(geometry)):
                    raise ValueError("Invalid step geometry indexes.")
                normalized_steps.append(
                    RouteStep(
                        instruction=step["instruction"],
                        road_name=step.get("name", ""),
                        distance_m=step_distance_m,
                        duration_minutes=duration_minutes,
                        geometry_start_index=geometry_start_index,
                        geometry_end_index=geometry_end_index,
                    )
                )
                remaining_distance_m -= step_distance_m
            steps = tuple(normalized_steps)
            legs.append(
                RouteLeg(
                    start=waypoints[index],
                    end=waypoints[index + 1],
                    distance_m=segment_distance_m,
                    duration_minutes=sum(step.duration_minutes for step in steps),
                    steps=steps,
                )
            )
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ProviderError(
            "PROVIDER_UNAVAILABLE",
            "The routing service returned an invalid response.",
            True,
        ) from exc
    return NormalizedRoute(
        geometry=geometry,
        legs=tuple(legs),
        distance_m=sum(leg.distance_m for leg in legs),
        driving_minutes=sum(leg.duration_minutes for leg in legs),
    )


class OpenRouteServiceClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=ORS_BASE_URL,
            headers={"Authorization": api_key},
            timeout=httpx.Timeout(12.0, connect=5.0),
            transport=transport,
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        for attempt in range(2):
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                if attempt == 0:
                    continue
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service could not be reached.",
                    True,
                ) from exc

            if response.status_code == 429:
                raise ProviderError(
                    "PROVIDER_RATE_LIMITED",
                    "The routing service rate limit was reached.",
                    True,
                    429,
                )
            if response.status_code in {502, 503, 504} and attempt == 0:
                continue
            if response.status_code >= 500:
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service is temporarily unavailable.",
                    True,
                )
            if response.status_code >= 400:
                raise ProviderError(
                    "ROUTE_NOT_FOUND",
                    "No truck route was found for the selected locations.",
                    False,
                    422,
                )
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise TypeError("Provider JSON root must be an object.")
            except (TypeError, ValueError) as exc:
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service returned an invalid response.",
                    True,
                ) from exc
            return payload

        raise ProviderError(
            "PROVIDER_UNAVAILABLE",
            "The routing service is temporarily unavailable.",
            True,
        )

    def search_locations(self, query: str) -> tuple[Location, ...]:
        payload = self._request(
            "GET",
            "/geocode/search",
            params={
                "text": query,
                "boundary.country": "US",
                "size": 5,
            },
        )
        locations: list[Location] = []
        for feature in payload.get("features", [])[:5]:
            properties = feature["properties"]
            longitude, latitude = feature["geometry"]["coordinates"]
            locations.append(
                Location(
                    id=str(properties.get("id", properties["label"])),
                    label=properties["label"],
                    coordinate=Coordinate(float(longitude), float(latitude)),
                    country_code="US",
                )
            )
        return tuple(locations)

    def build_route(
        self,
        waypoints: tuple[Location, Location, Location],
    ) -> NormalizedRoute:
        payload = self._request(
            "POST",
            "/v2/directions/driving-hgv/geojson",
            json={
                "coordinates": [
                    [point.coordinate.longitude, point.coordinate.latitude] for point in waypoints
                ],
                "instructions": True,
            },
        )
        return _parse_route_payload(payload, waypoints)

    def reverse_geocode(self, coordinate: Coordinate) -> Location:
        payload = self._request(
            "GET",
            "/geocode/reverse",
            params={
                "point.lon": coordinate.longitude,
                "point.lat": coordinate.latitude,
                "size": 1,
            },
        )
        features = payload.get("features", [])
        if not features:
            return Location(
                id=f"{coordinate.longitude:.5f},{coordinate.latitude:.5f}",
                label=f"{coordinate.latitude:.5f}, {coordinate.longitude:.5f}",
                coordinate=coordinate,
            )
        feature = features[0]
        properties = feature["properties"]
        return Location(
            id=str(properties.get("id", properties["label"])),
            label=properties["label"],
            coordinate=coordinate,
            country_code="US",
        )
