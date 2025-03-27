from typing import List, Optional
from urllib.parse import urlencode
import requests
from loguru import logger

from src.clip_services.clip_base import ClipBase
from src.models.schema import VideoAspect, VideoClip


class PixabayService(ClipBase):
    def __init__(self, api_key: str, proxy: str = None):
        super().__init__("pixabay", api_key, proxy)

    def search_clips(self,
                     search_term: str,
                     minimum_duration: int,
                     video_aspect: VideoAspect = VideoAspect.portrait,
                     ) -> List[VideoClip]:
        params = {
            "q": search_term,
            "video_type": "all",  # Accepted values: "all", "film", "animation"
            "per_page": 50,
            "key": self.api_key,
        }
        query_url = f"https://pixabay.com/api/videos/?{urlencode(params)}"
        logger.info(f"searching videos: {query_url}, with proxies: {self.proxy}")

        try:
            r = requests.get(
                query_url, proxies=self.proxy, verify=False, timeout=(30, 60)
            )
            response = r.json()
            video_items = []
            if "hits" not in response:
                logger.error(f"search videos failed: {response}")
                return video_items

            for v in response["hits"]:
                if v["duration"] < minimum_duration:
                    continue

                if item := self._parse_one_clip(v, video_aspect):
                    video_items.append(item)

            return video_items
        except Exception as e:
            logger.error(f"search videos failed: {str(e)}")

        return []

    def _parse_one_clip(self, search_item: dict, aspect: VideoAspect) -> Optional[VideoClip]:
        aspect = VideoAspect(aspect)
        video_width, video_height = aspect.to_resolution()

        video_files = search_item["videos"]
        for video_type in search_item["videos"]:
            video = video_files[video_type]
            w = video["width"]
            h = video["height"]
            if w >= video_width and h >= video_height:
                return VideoClip(
                    provider=self.name,
                    original_id=str(search_item["id"]),
                    url=video["url"],
                    duration=search_item["duration"],
                    thumbnail=video["thumbnail"],
                    width=w,
                    height=h,
                    size=video["size"],
                    content_type="",
                    description=search_item["tags"],
                )