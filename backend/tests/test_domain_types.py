from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from trips.domain.types import Coordinate, DutyEvent, DutyStatus, EventKind, Location


def make_event() -> DutyEvent:
    location = Location(
        id="start",
        label="Denver, CO",
        coordinate=Coordinate(longitude=-104.9903, latitude=39.7392),
    )
    start = datetime(2026, 7, 25, 8, 0, tzinfo=UTC)
    return DutyEvent(
        id="drive-1",
        kind=EventKind.DRIVING,
        duty_status=DutyStatus.DRIVING,
        start_at=start,
        end_at=start + timedelta(minutes=45),
        route_start_m=0,
        route_end_m=50_000,
        location=location,
        remark="Drive toward pickup",
        cycle_used_before_minutes=0,
        cycle_used_after_minutes=45,
    )


def test_duty_event_reports_exact_integer_duration() -> None:
    assert make_event().duration_minutes == 45


def test_domain_records_are_immutable() -> None:
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.remark = "Changed"
