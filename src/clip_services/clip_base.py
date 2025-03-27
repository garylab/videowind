from abc import abstractmethod
from typing import List

from src.models.schema import VideoClip, VideoAspect


class ClipBase:
    def __init__(self, name: str, api_key: str, proxy: str = None):
        self.name = name
        self.api_key = api_key
        self.proxy = proxy

    @abstractmethod
    def search_clips(self,
                     search_term: str,
                     minimum_duration: int,
                     video_aspect: VideoAspect = VideoAspect.portrait,
                     ) -> List[VideoClip]:
        raise NotImplementedError
