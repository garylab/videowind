from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src.utils.env_utils import get_bool, get_int, get_str

load_dotenv()


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
class DbConfig:
    url: str = get_str("DB_URL", "mysql+pymysql://root:12345678@127.0.0.1:3306/videowind")
    pre_ping: bool = get_bool("DB_PRE_PING", True)
    pool_size: int = get_int("DB_POOL_SIZE", 5)
    max_overflow: int = get_int("DB_MAX_OVERFLOW", 10)


@dataclass
class DirConfig:
    root_dir: Path = Path(__file__).parent.parent.parent
    storage_dir: Path = root_dir.joinpath("storage")


@dataclass
class AiConfig:
    whisper_model: str = get_str("AI_WHISPER_MODEL", "large-v3")
    whisper_device = get_str("AI_WHISPER_DEVICE", "cpu")
    whisper_compute_type = get_str("AI_WHISPER_COMPUTE_TYPE", "int8")
    whisper_download_dir = get_str("AI_WHISPER_DOWNLOAD_DIR", DirConfig.storage_dir.joinpath(f"models/whisper-large-v3"))


@dataclass
class WpConfig:
    url: str = get_str("WP_URL", "")
    username: str = get_str("WP_USERNAME", "")
    password: str = get_str("WP_PASSWORD", "")


