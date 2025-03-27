import json

from src.clip_services.pexels_service import PexelsService
from src.models.schema import VideoAspect, VideoClip
from tests import JSONS_DIR

service = PexelsService("")


def test__parse_one():
    search_item = json.loads(JSONS_DIR.joinpath("pexels-search-item.json").read_text())
    item = service._parse_one(search_item, VideoAspect.landscape)
    assert item == VideoClip(
        provider="pexels",
        original_id="1448735",
        url="https://www.pexels.com/video/video-of-forest-1448735/",
        video_file_url="https://player.vimeo.com/external/291648067.hd.mp4?s=94998971682c6a3267e4cbd19d16a7b6c720f345&profile_id=175&oauth2_token_id=57447761",
        thumbnail="https://images.pexels.com/videos/1448735/free-video-1448735.jpg?fit=crop&w=1200&h=630&auto=compress&cs=tinysrgb",
        width=2048,
        height=1080,
        size=0,
        content_type="video/mp4",
        duration=32,
        description="Video of forest"
    )
