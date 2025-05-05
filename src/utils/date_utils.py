from datetime import datetime
import pytz

from src.constants.config import AppConfig


tz = pytz.timezone(AppConfig.tz)


def get_now():
    return datetime.now(tz=tz)


def dt_localize(dt_from_db: datetime) -> datetime:
    return tz.localize(dt_from_db)


def get_today():
    return get_now().strftime("%Y-%m-%d")
