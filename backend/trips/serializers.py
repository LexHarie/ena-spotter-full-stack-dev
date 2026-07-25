from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from trips.domain.types import (
    Coordinate,
    DutyStatus,
    EventKind,
    Location,
    PlanningResult,
    TripRequest,
)
from trips.domain.units import (
    ceil_datetime_to_quarter,
    hours_to_minutes,
    meters_to_miles,
)


class LocationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=200)
    label = serializers.CharField(max_length=300)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    country_code = serializers.CharField(max_length=2)

    def validate_longitude(self, value: float) -> float:
        if not isfinite(value):
            raise serializers.ValidationError("Longitude must be finite.")
        return value

    def validate_latitude(self, value: float) -> float:
        if not isfinite(value):
            raise serializers.ValidationError("Latitude must be finite.")
        return value

    def validate_country_code(self, value: str) -> str:
        if value.upper() != "US":
            raise serializers.ValidationError("Select a United States location.")
        return "US"

    def to_domain(self, data: dict) -> Location:
        return Location(
            id=data["id"],
            label=data["label"],
            coordinate=Coordinate(data["longitude"], data["latitude"]),
            country_code=data["country_code"],
        )


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = LocationSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    current_cycle_used_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("70"),
    )
    starts_at = serializers.CharField(max_length=64)
    home_terminal_timezone = serializers.CharField(max_length=64)

    def validate_current_cycle_used_hours(self, value: Decimal) -> Decimal:
        try:
            hours_to_minutes(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        try:
            starts_at = datetime.fromisoformat(attrs["starts_at"])
        except ValueError as exc:
            raise serializers.ValidationError(
                {"starts_at": "Use an ISO 8601 timestamp with a UTC offset."}
            ) from exc
        if starts_at.utcoffset() is None:
            raise serializers.ValidationError(
                {"starts_at": "Start time must include a UTC offset."}
            )
        try:
            home_zone = ZoneInfo(attrs["home_terminal_timezone"])
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError(
                {"home_terminal_timezone": "Use a valid IANA timezone."}
            ) from exc
        if starts_at.astimezone(home_zone).utcoffset() != starts_at.utcoffset():
            raise serializers.ValidationError(
                {"starts_at": "Start offset does not match the home-terminal timezone."}
            )
        attrs["parsed_starts_at"] = ceil_datetime_to_quarter(starts_at)
        return attrs

    def to_domain(self) -> TripRequest:
        data = self.validated_data
        location_serializer = LocationSerializer()
        starts_at = data["parsed_starts_at"]
        offset = starts_at.utcoffset()
        if offset is None:
            raise ValueError("Validated start time must retain its UTC offset.")
        return TripRequest(
            current_location=location_serializer.to_domain(data["current_location"]),
            pickup_location=location_serializer.to_domain(data["pickup_location"]),
            dropoff_location=location_serializer.to_domain(data["dropoff_location"]),
            cycle_used_minutes=hours_to_minutes(data["current_cycle_used_hours"]),
            starts_at=starts_at,
            home_terminal_timezone=data["home_terminal_timezone"],
            fixed_utc_offset_minutes=int(offset.total_seconds() // 60),
        )


def _location_data(location: Location) -> dict:
    return {
        "id": location.id,
        "label": location.label,
        "longitude": location.coordinate.longitude,
        "latitude": location.coordinate.latitude,
        "country_code": location.country_code,
    }


def serialize_plan(result: PlanningResult) -> dict:
    route = result.route
    total_duration = sum(event.duration_minutes for event in result.events)
    duty_totals = {
        status: sum(
            event.duration_minutes for event in result.events if event.duty_status == status
        )
        for status in DutyStatus
    }
    longitudes = [point.longitude for point in route.geometry]
    latitudes = [point.latitude for point in route.geometry]
    stop_kinds = {
        EventKind.PICKUP,
        EventKind.DROPOFF,
        EventKind.FUEL,
        EventKind.BREAK,
        EventKind.DAILY_REST,
        EventKind.CYCLE_RESTART,
    }
    events = [
        {
            "id": event.id,
            "kind": event.kind,
            "duty_status": event.duty_status,
            "start_at": event.start_at.isoformat(),
            "end_at": event.end_at.isoformat(),
            "duration_minutes": event.duration_minutes,
            "route_start_m": event.route_start_m,
            "route_end_m": event.route_end_m,
            "location": _location_data(event.location),
            "remark": event.remark,
        }
        for event in result.events
    ]
    return {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "rule_set_version": "property-70-8-v1",
            "home_terminal_timezone": result.request.home_terminal_timezone,
            "fixed_utc_offset_minutes": result.request.fixed_utc_offset_minutes,
            "assumptions": [
                "Solo property-carrying driver",
                "70 hours in 8 days",
                "Fresh 11-hour driving and 14-hour shift clocks",
                "Thirty non-driving minutes after 8 driving hours",
                "Ten consecutive sleeper-berth hours reset shift clocks",
                "Thirty-four off-duty hours reset aggregate cycle usage",
                "No adverse-condition extension",
                "One hour each for pickup and drop-off",
                "Thirty-minute fuel stop before every 1,000 miles",
                "Trip-start home-terminal UTC offset remains fixed",
            ],
            "warnings": list(result.warnings),
        },
        "summary": {
            "starts_at": result.events[0].start_at.isoformat(),
            "ends_at": result.events[-1].end_at.isoformat(),
            "distance_m": route.distance_m,
            "distance_miles": str(meters_to_miles(route.distance_m)),
            "driving_minutes": sum(
                event.duration_minutes for event in result.events if event.kind == EventKind.DRIVING
            ),
            "on_duty_not_driving_minutes": duty_totals[DutyStatus.ON_DUTY],
            "off_duty_minutes": duty_totals[DutyStatus.OFF_DUTY],
            "sleeper_berth_minutes": duty_totals[DutyStatus.SLEEPER_BERTH],
            "total_duration_minutes": total_duration,
            "cycle_used_start_minutes": result.request.cycle_used_minutes,
            "cycle_used_end_minutes": result.events[-1].cycle_used_after_minutes,
            "cycle_restarts": sum(event.kind == EventKind.CYCLE_RESTART for event in result.events),
            "log_days": len(result.daily_logs),
            "fuel_stops": sum(event.kind == EventKind.FUEL for event in result.events),
            "rest_stops": sum(
                event.kind in {EventKind.DAILY_REST, EventKind.CYCLE_RESTART}
                for event in result.events
            ),
        },
        "route": {
            "bounds": {
                "west": min(longitudes),
                "south": min(latitudes),
                "east": max(longitudes),
                "north": max(latitudes),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[point.longitude, point.latitude] for point in route.geometry],
            },
            "legs": [
                {
                    "from": _location_data(leg.start),
                    "to": _location_data(leg.end),
                    "distance_m": leg.distance_m,
                    "duration_minutes": leg.duration_minutes,
                    "steps": [
                        {
                            "instruction": step.instruction,
                            "road_name": step.road_name,
                            "distance_m": step.distance_m,
                            "duration_minutes": step.duration_minutes,
                        }
                        for step in leg.steps
                    ],
                }
                for leg in route.legs
            ],
        },
        "events": events,
        "stops": [event for event in events if event["kind"] in stop_kinds],
        "daily_logs": [
            {
                "date": log.date.isoformat(),
                "trip_day": log.trip_day,
                "start_location": _location_data(log.start_location),
                "end_location": _location_data(log.end_location),
                "distance_m": log.distance_m,
                "totals_minutes": {
                    "off_duty": log.off_duty_minutes,
                    "sleeper_berth": log.sleeper_berth_minutes,
                    "driving": log.driving_minutes,
                    "on_duty_not_driving": log.on_duty_minutes,
                },
                "cycle": {
                    "used_at_start_minutes": log.cycle_used_start_minutes,
                    "added_minutes": log.cycle_added_minutes,
                    "remaining_at_end_minutes": log.cycle_remaining_end_minutes,
                },
                "segments": [
                    {
                        "event_id": segment.event_id,
                        "kind": segment.kind,
                        "duty_status": segment.duty_status,
                        "start_minute": segment.start_minute,
                        "end_minute": segment.end_minute,
                        "location": _location_data(segment.location),
                        "remark": segment.remark,
                    }
                    for segment in log.segments
                ],
            }
            for log in result.daily_logs
        ],
    }
