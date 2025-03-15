from dataclasses import dataclass, field

from src.utils.env_utils import get_str, get_int, get_bool

@dataclass
class AppConfig:
    name = get_str("APP_NAME", "VideoWind")
    description = get_str("APP_DESCRIPTION", "A video processing service")
    version = get_str("APP_VERSION", "0.0.1")

    host = get_str("APP_HOST", "0.0.0.0")
    port = get_int("APP_PORT", 8000)
    reload = get_bool("APP_RELOAD", True)
    debug_mode = get_bool("APP_DEBUG_MODE", True)
    tz = get_str("APP_TZ", "UTC")


@dataclass
class DatabaseConfig:
    url: str = get_str("DB_URL", "mysql+pymysql://root:12345678@127.0.0.1:3306/videowind")
    pre_ping: bool = get_bool("DB_PRE_PING", True)
    pool_size: int = get_int("DB_POOL_SIZE", 5)
    max_overflow: int = get_int("DB_MAX_OVERFLOW", 10)


@dataclass
class Config:
    APP: AppConfig = field(default_factory=AppConfig)
    DB: DatabaseConfig = field(default_factory=DatabaseConfig)



config = Config()