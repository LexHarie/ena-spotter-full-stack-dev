from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class DutyStatus(StrEnum):
    OFF_DUTY = "off_duty"
    SLEEPER_BERTH = "sleeper_berth"
    DRIVING = "driving"
    ON_DUTY = "on_duty_not_driving"


class EventKind(StrEnum):
    PRE_TRIP_OFF_DUTY = "pre_trip_off_duty"
    DRIVING = "driving"
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    FUEL = "fuel"
    BREAK = "break"
    DAILY_REST = "daily_rest"
    CYCLE_RESTART = "cycle_restart"
    POST_TRIP_OFF_DUTY = "post_trip_off_duty"


@dataclass(frozen=True)
class Coordinate:
    longitude: float
    latitude: float


@dataclass(frozen=True)
class Location:
    id: str
    label: str
    coordinate: Coordinate
    country_code: str = "US"


@dataclass(frozen=True)
class RouteStep:
    instruction: str
    road_name: str
    distance_m: int
    duration_minutes: int
    geometry_start_index: int
    geometry_end_index: int


@dataclass(frozen=True)
class RouteLeg:
    start: Location
    end: Location
    distance_m: int
    duration_minutes: int
    steps: tuple[RouteStep, ...]


@dataclass(frozen=True)
class NormalizedRoute:
    geometry: tuple[Coordinate, ...]
    legs: tuple[RouteLeg, ...]
    distance_m: int
    driving_minutes: int


@dataclass(frozen=True)
class TripRequest:
    current_location: Location
    pickup_location: Location
    dropoff_location: Location
    cycle_used_minutes: int
    starts_at: datetime
    home_terminal_timezone: str
    fixed_utc_offset_minutes: int


@dataclass(frozen=True)
class DutyEvent:
    id: str
    kind: EventKind
    duty_status: DutyStatus
    start_at: datetime
    end_at: datetime
    route_start_m: int
    route_end_m: int
    location: Location
    remark: str
    cycle_used_before_minutes: int
    cycle_used_after_minutes: int

    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)


@dataclass(frozen=True)
class DailyLogSegment:
    event_id: str
    kind: EventKind
    duty_status: DutyStatus
    start_minute: int
    end_minute: int
    location: Location
    remark: str


@dataclass(frozen=True)
class DailyLog:
    date: date
    trip_day: int
    start_location: Location
    end_location: Location
    distance_m: int
    segments: tuple[DailyLogSegment, ...]
    off_duty_minutes: int
    sleeper_berth_minutes: int
    driving_minutes: int
    on_duty_minutes: int
    cycle_used_start_minutes: int
    cycle_added_minutes: int
    cycle_remaining_end_minutes: int
