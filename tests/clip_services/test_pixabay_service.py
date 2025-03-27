import json

from src.clip_services.pixabay_service import PixabayService
from src.models.schema import VideoAspect, VideoClip
from tests import JSONS_DIR

service = PixabayService("")


def test__parse_one():
    search_item = json.loads(JSONS_DIR.joinpath("pixabay-search-item.json").read_text())
    item = service._parse_one(search_item, VideoAspect.landscape)
    assert item == VideoClip(
        provider="pixabay",
        original_id="125",
        url="https://pixabay.com/videos/id-125/",
        video_file_url="https://cdn.pixabay.com/video/2015/08/08/125-135736646_large.mp4",
        thumbnail="https://cdn.pixabay.com/video/2015/08/08/125-135736646_large.jpg",
        width=1920,
        height=1080,
        size=6615235,
        content_type="",
        duration=12,
        description="flowers, yellow, blossom"
    )
