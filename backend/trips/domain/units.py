from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

MINUTES_PER_QUARTER = 15
METERS_PER_MILE = Decimal("1609.344")


def hours_to_minutes(hours: Decimal) -> int:
    minutes = hours * Decimal(60)
    if minutes != minutes.to_integral_value() or int(minutes) % MINUTES_PER_QUARTER:
        raise ValueError("Hours must use quarter-hour increments.")
    return int(minutes)


def ceil_minutes_to_quarter(minutes: int) -> int:
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    return ((minutes + MINUTES_PER_QUARTER - 1) // MINUTES_PER_QUARTER) * MINUTES_PER_QUARTER


def ceil_datetime_to_quarter(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("Start time must be timezone-aware.")
    floor = value.replace(second=0, microsecond=0)
    remainder = floor.minute % MINUTES_PER_QUARTER
    extra = 0 if remainder == 0 and value == floor else MINUTES_PER_QUARTER - remainder
    return floor + timedelta(minutes=extra)


def meters_to_miles(meters: int) -> Decimal:
    return (Decimal(meters) / METERS_PER_MILE).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
