from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trips.domain.units import (
    ceil_datetime_to_quarter,
    ceil_minutes_to_quarter,
    hours_to_minutes,
    meters_to_miles,
)


def test_hours_to_minutes_accepts_quarter_hours() -> None:
    assert hours_to_minutes(Decimal("24.25")) == 1455


def test_hours_to_minutes_rejects_non_quarter_hours() -> None:
    with pytest.raises(ValueError, match="quarter-hour"):
        hours_to_minutes(Decimal("1.10"))


def test_ceil_minutes_to_quarter() -> None:
    assert ceil_minutes_to_quarter(61) == 75
    assert ceil_minutes_to_quarter(75) == 75


def test_ceil_datetime_to_quarter_preserves_offset() -> None:
    value = datetime(2026, 7, 25, 8, 7, tzinfo=timezone(timedelta(hours=-5)))

    assert ceil_datetime_to_quarter(value) == datetime(
        2026,
        7,
        25,
        8,
        15,
        tzinfo=timezone(timedelta(hours=-5)),
    )


def test_meters_to_miles_rounds_only_for_display() -> None:
    assert meters_to_miles(160934) == Decimal("100.00")
