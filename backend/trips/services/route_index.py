from math import asin, cos, radians, sin, sqrt

from trips.domain.types import Coordinate, NormalizedRoute

EARTH_RADIUS_M = 6_371_000


def _distance_m(start: Coordinate, end: Coordinate) -> float:
    lat1 = radians(start.latitude)
    lat2 = radians(end.latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(end.longitude - start.longitude)
    haversine = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(haversine))


class RouteIndex:
    def __init__(self, route: NormalizedRoute) -> None:
        if len(route.geometry) < 2:
            raise ValueError("Route geometry requires at least two coordinates.")
        self._route = route
        cumulative = [0.0]
        for start, end in zip(
            route.geometry,
            route.geometry[1:],
            strict=False,
        ):
            cumulative.append(cumulative[-1] + _distance_m(start, end))
        self._cumulative = tuple(cumulative)
        self._geometry_distance = cumulative[-1]

    def coordinate_at(self, progress_m: int) -> Coordinate:
        if progress_m <= 0:
            return self._route.geometry[0]
        if progress_m >= self._route.distance_m:
            return self._route.geometry[-1]

        target = (progress_m / self._route.distance_m) * self._geometry_distance
        for index in range(1, len(self._cumulative)):
            if self._cumulative[index] < target:
                continue
            start_distance = self._cumulative[index - 1]
            segment_distance = self._cumulative[index] - start_distance
            ratio = 0.0 if segment_distance == 0 else (target - start_distance) / segment_distance
            start = self._route.geometry[index - 1]
            end = self._route.geometry[index]
            return Coordinate(
                longitude=start.longitude + (end.longitude - start.longitude) * ratio,
                latitude=start.latitude + (end.latitude - start.latitude) * ratio,
            )
        return self._route.geometry[-1]
