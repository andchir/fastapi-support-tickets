from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.config import settings


@lru_cache
def _zone(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def app_tz() -> ZoneInfo:
    return _zone(settings.app_timezone)


def utc_now_naive() -> datetime:
    """UTC 'now' without tzinfo — for DateTime columns that store UTC."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_app_timezone(dt: datetime) -> datetime:
    """Naive values are considered UTC; result is aware in the application's timezone."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(app_tz())


def local_day_start_utc_naive(d: date) -> datetime:
    """Start of calendar day d in the application's timezone, in naive UTC."""
    local_start = datetime.combine(d, time.min, tzinfo=app_tz())
    return local_start.astimezone(UTC).replace(tzinfo=None)


def local_next_day_start_utc_naive(d: date) -> datetime:
    """Midnight of the day after d in the application's timezone, in naive UTC."""
    return local_day_start_utc_naive(d + timedelta(days=1))
