from dataclasses import dataclass, field

from src.utils.env_utils import get_str, get_int, get_bool

@dataclass
class AppConfig:
    host = get_str("SERVER_HOST", "0.0.0.0")
    port = get_int("SERVER_PORT", 8000)
    reload = get_bool("SERVER_RELOAD", True)
    tz = get_str("SERVER_TZ", "UTC")


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