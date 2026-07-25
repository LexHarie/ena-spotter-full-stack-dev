from datetime import datetime
from decimal import Decimal
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from trips.domain.types import Coordinate, Location, TripRequest
from trips.domain.units import ceil_datetime_to_quarter, hours_to_minutes


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
