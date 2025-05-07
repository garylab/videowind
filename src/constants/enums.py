from enum import StrEnum


class TaskStatus(StrEnum):
    FAILED = "FAILED"
    INIT = "INIT"
    STARTED = "STARTED"
    TERMS_GENERATED = "TERMS_GENERATED"
    AUDIO_GENERATED = "AUDIO_GENERATED"
    SUBTITLE_GENERATED = "SUBTITLE_GENERATED"
    SCRIPT_GENERATED = "SCRIPT_GENERATED"
    CLIPS_DOWNLOADED = "CLIPS_DOWNLOADED"
    VIDEO_MERGED = "VIDEO_MERGED"
    FINAL_VIDEO_GENERATED = "FINAL_VIDEO_GENERATED"


class StopAt(StrEnum):
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    SUBTITLE = "SUBTITLE"
    SCRIPT = "SCRIPT"
    TERMS = "TERMS"
    MATERIALS = "MATERIALS"


class PostStatus(StrEnum):
    FAILED = "FAILED"
    INIT = "INIT"
    PUBLISHED = "PUBLISHED"


class GenderType(StrEnum):
    MALE = "Male"
    FEMALE = "Female"


class SubtitlePosition(StrEnum):
    TOP = "TOP"
    MIDDLE = "MIDDLE"   # fallback option
    BOTTOM = "BOTTOM"
    CUSTOM = "CUSTOM"
