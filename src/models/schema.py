import warnings
from pydantic import Field
from enum import Enum
from typing import Any, List, Optional, Union

import pydantic
from pydantic import BaseModel

from src.constants.enums import GenderType, SubtitlePosition, VoiceType

# 忽略 Pydantic 的特定警告
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="Field name.*shadows an attribute in parent.*",
)


class VideoConcatMode(str, Enum):
    random = "random"
    sequential = "sequential"


class VideoTransitionMode(str, Enum):
    none = None
    shuffle = "Shuffle"
    fade_in = "FadeIn"
    fade_out = "FadeOut"
    slide_in = "SlideIn"
    slide_out = "SlideOut"


class VideoAspect(str, Enum):
    landscape = "16:9"
    portrait = "9:16"
    square = "1:1"

    def to_resolution(self):
        if self == VideoAspect.landscape.value:
            return 1920, 1080
        elif self == VideoAspect.portrait.value:
            return 1080, 1920
        elif self == VideoAspect.square.value:
            return 1080, 1080
        return 1080, 1920


class _Config:
    arbitrary_types_allowed = True


@pydantic.dataclasses.dataclass(config=_Config)
class MaterialInfo:
    provider: str = "pexels"
    url: str = ""
    duration: int = 0


@pydantic.dataclasses.dataclass(config=_Config)
class VideoClip:
    provider: str
    original_id: str
    url: str
    video_file_url: str
    duration: int
    thumbnail: str
    width: int
    height: int
    size: int
    content_type: str
    description: str


class AudioRequest(BaseModel):
    video_script: str = "Wise men speak because they have something to say, fools because they have to say something."
    video_language: Optional[str] = ""
    voice_name: Optional[str] = "en-US-AvaMultilingualNeural"
    voice_volume: Optional[float] = 1.0
    bgm_type: Optional[str] = "random"
    bgm_file: Optional[str] = ""
    bgm_volume: Optional[float] = 0.2


class SubtitleRequest(AudioRequest):
    subtitle_enabled: bool = True

    font_name: Optional[str] = "JosefinSans-Light.ttf"
    text_fore_color: Optional[str] = "#FFFFFF"
    text_background_color: Optional[str] = ""
    font_size: int = 60
    stroke_color: Optional[str] = "#000000"
    stroke_width: int = 2


class VideoRequest(SubtitleRequest):
    video_subject: str
    video_terms: Optional[str] = ""
    video_source: Optional[str] = "pexels"
    video_aspect: Optional[VideoAspect] = VideoAspect.landscape.value
    video_concat_mode: Optional[VideoConcatMode] = VideoConcatMode.random.value
    video_transition_mode: Optional[VideoTransitionMode] = None
    video_clip_duration: Optional[int] = 5
    video_count: Optional[int] = 1
    video_materials: Optional[List[MaterialInfo]] = (
        None  # Materials used to generate the video
    )

    subtitle_position: SubtitlePosition = SubtitlePosition.BOTTOM
    subtitle_custom_position: int = 70
    n_threads: Optional[int] = 2
    paragraph_number: Optional[int] = 1


class SubtitleStyle(BaseModel):
    position: SubtitlePosition
    custom_position: int
    font_path: str
    font_size: int
    text_fore_color: str
    text_background_color: str
    stroke_color: str
    stroke_width: int


class VideoDimension(BaseModel):
    width: int
    height: int


class VoiceParams(BaseModel):
    q: Optional[str] = None
    type: Optional[VoiceType] = None
    locale: Optional[str] = None
    gender: Optional[GenderType] = None


class VoiceOut(BaseModel):
    ShortName: str
    SampleRateHertz: str
    Gender: str
    Locale: str
    WordsPerMinute: Optional[int] = None


class VideoScriptParams:
    """
    {
      "video_subject": "春天的花海",
      "video_language": "",
      "paragraph_number": 1
    }
    """

    video_subject: Optional[str] = "春天的花海"
    video_language: Optional[str] = ""
    paragraph_number: Optional[int] = 1


class VideoTermsParams:
    """
    {
      "video_subject": "",
      "video_script": "",
      "amount": 5
    }
    """

    video_subject: Optional[str] = "春天的花海"
    video_script: Optional[str] = (
        "春天的花海，如诗如画般展现在眼前。万物复苏的季节里，大地披上了一袭绚丽多彩的盛装。金黄的迎春、粉嫩的樱花、洁白的梨花、艳丽的郁金香……"
    )
    amount: Optional[int] = 5


class BaseResponse(BaseModel):
    status: int = 200
    message: Optional[str] = "success"
    data: Any = None


class TaskQueryRequest(BaseModel):
    pass


class VideoScriptRequest(VideoScriptParams, BaseModel):
    pass


class VideoTermsRequest(VideoTermsParams, BaseModel):
    pass


class TaskLiteOut(BaseModel):
    id: str
    status: str
    params: dict

    # convert uuid to string for id
    @pydantic.field_validator("id", mode="before")
    def convert_uuid_to_str(cls, value):
        if isinstance(value, str):
            return value
        return str(value)

    class Config:
        arbitrary_types_allowed = True
        from_attributes = True
        populate_by_name = True
        use_enum_values = True

class TaskOut(TaskLiteOut):
    result: Optional[dict] = None
    failed_reason: Optional[str] = None


class TaskIdOut(BaseModel):
    task_id: str


class TaskStatusOut(BaseModel):
    task_id: str
    status: str


######################################################################################################
######################################################################################################
######################################################################################################
######################################################################################################
class TaskResponse(BaseResponse):
    class TaskResponseData(BaseModel):
        task_id: str

    data: TaskResponseData

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {"task_id": "6c85c8cc-a77a-42b9-bc30-947815aa0558"},
            },
        }


class TaskQueryResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "state": 1,
                    "progress": 100,
                    "videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/final-1.mp4"
                    ],
                    "combined_videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/combined-1.mp4"
                    ],
                },
            },
        }


class TaskDeletionResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "state": 1,
                    "progress": 100,
                    "videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/final-1.mp4"
                    ],
                    "combined_videos": [
                        "http://127.0.0.1:8080/tasks/6c85c8cc-a77a-42b9-bc30-947815aa0558/combined-1.mp4"
                    ],
                },
            },
        }


class VideoScriptResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "video_script": "春天的花海，是大自然的一幅美丽画卷。在这个季节里，大地复苏，万物生长，花朵争相绽放，形成了一片五彩斑斓的花海..."
                },
            },
        }


class VideoTermsResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {"video_terms": ["sky", "tree"]},
            },
        }


class BgmRetrieveResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {
                    "files": [
                        {
                            "name": "output013.mp3",
                            "size": 1891269,
                            "file": "/storage/resource/songs/output013.mp3",
                        }
                    ]
                },
            },
        }


class BgmUploadResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "message": "success",
                "data": {"file": "/storage/resource/songs/example.mp3"},
            },
        }
