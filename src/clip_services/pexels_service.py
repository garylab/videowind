import re
from typing import List, Optional
from urllib.parse import urlencode
from loguru import logger
import requests

from src.clip_services.clip_base import ClipBase
from src.models.schema import VideoClip, VideoAspect


class PexelsService(ClipBase):
    def __init__(self, api_key: str, proxy: str = None):
        super().__init__("pexels", api_key, proxy)

    @staticmethod
    def extract_title_from_url(url):
        match = re.search(r"pexels\.com/video/([\w-]+)-\d+/", url)
        if match:
            return match.group(1).replace("-", " ").capitalize()

        return ""

    def search_clips(self,
                     search_term: str,
                     minimum_duration: int,
                     video_aspect: VideoAspect = VideoAspect.portrait,
                     ) -> List[VideoClip]:
        headers = {
            "Authorization": self.api_key,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        }

        params = {"query": search_term, "per_page": 20, "orientation": video_aspect.name}
        query_url = f"https://api.pexels.com/videos/search?{urlencode(params)}"
        logger.info(f"searching videos: {query_url}, with proxies: {self.proxy}")

        try:
            r = requests.get(
                query_url,
                headers=headers,
                proxies=self.proxy,
                verify=False,
                timeout=(30, 60),
            )
            response = r.json()
            video_items = []
            if "videos" not in response:
                logger.error(f"search videos failed: {response}")
                return video_items

            for v in response["videos"]:
                if v["duration"] < minimum_duration:
                    continue

                if item := self._parse_one(v, video_aspect):
                    video_items.append(item)

            return video_items
        except Exception as e:
            logger.error(f"search videos failed: {str(e)}")

        return []

    def _parse_one(self, search_item: dict, aspect: VideoAspect) -> Optional[VideoClip]:
        aspect = VideoAspect(aspect)
        video_width, video_height = aspect.to_resolution()

        for video in search_item["video_files"]:
            w = video["width"]
            h = video["height"]
            if w >= video_width and h >= video_height:
                return VideoClip(
                    provider=self.name,
                    original_id=str(search_item["id"]),
                    url=search_item["url"],
                    video_file_url=video["link"],
                    duration=search_item["duration"],
                    thumbnail=search_item["image"],
                    width=w,
                    height=h,
                    size=0,
                    content_type=video["file_type"],
                    description=self.extract_title_from_url(search_item["url"]),
                )
