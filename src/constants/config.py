import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from src.constants.consts import PROJECT_DIR
from src.utils.env_utils import get_bool, get_int, get_str

load_dotenv(PROJECT_DIR.joinpath(".env").as_posix())


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
    url: str = get_str("DB_URL")
    pre_ping: bool = get_bool("DB_PRE_PING", True)
    pool_size: int = get_int("DB_POOL_SIZE", 5)
    max_overflow: int = get_int("DB_MAX_OVERFLOW", 10)


@dataclass
class DirConfig:
    storage_dir: Path = PROJECT_DIR.joinpath("storage")


@dataclass
class AiConfig:
    whisper_model: str = get_str("AI_WHISPER_MODEL", "large-v3")
    whisper_device = get_str("AI_WHISPER_DEVICE", "cpu")
    whisper_compute_type = get_str("AI_WHISPER_COMPUTE_TYPE", "int8")
    whisper_download_dir = get_str("AI_WHISPER_DOWNLOAD_DIR", DirConfig.storage_dir.joinpath(f"models/whisper-large-v3"))
    azure_speech_region = get_str("AZURE_SPEECH_REGION")
    azure_speech_key = get_str("AZURE_SPEECH_KEY")


@dataclass
class WpConfig:
    url: str = get_str("WP_URL", "")
    username: str = get_str("WP_USERNAME", "")
    password: str = get_str("WP_PASSWORD", "")


@dataclass
class LlmConfig:
    provider = "openai"
    base_url: str = get_str("LLM_BASE_URL", "")
    api_key: str = get_str("LLM_API_KEY", "")
    model_name: str = get_str("LLM_MODEL_NAME", "gpt-4o")
    api_version: str = get_str("LLM_API_VERSION", "2014-01-01")


@dataclass
class ClipProviderConfig:
    provider: str = get_str("CLIP_PROVIDER", "pexels")
    pexels_api_key: str = get_str("PEXELS_API_KEY")


@dataclass
class Env:
    CLIP: ClipProviderConfig = field(default_factory=ClipProviderConfig)
    LLM: LlmConfig = field(default_factory=LlmConfig)


env = Env()