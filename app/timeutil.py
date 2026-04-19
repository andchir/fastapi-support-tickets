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
    """UTC «сейчас» без tzinfo — для колонок DateTime, где хранится UTC."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_app_timezone(dt: datetime) -> datetime:
    """Наивные значения считаются UTC; результат — aware в часовом поясе приложения."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(app_tz())


def local_day_start_utc_naive(d: date) -> datetime:
    """Начало календарного дня d в часовом поясе приложения, в наивном UTC."""
    local_start = datetime.combine(d, time.min, tzinfo=app_tz())
    return local_start.astimezone(UTC).replace(tzinfo=None)


def local_next_day_start_utc_naive(d: date) -> datetime:
    """Полуночь следующего дня после d в поясе приложения, в наивном UTC."""
    return local_day_start_utc_naive(d + timedelta(days=1))
