import datetime

from src.models.schema import VideoRequest
from src.services.video_service import generate_video, get_bgm_file


def test_generate_video():
    video_path = "/Users/gary/works/VideoWind/storage/tasks/0196a908-e813-74a5-9a07-032fd72f9fdd/combined-1.mp4"
    audio_path = "/Users/gary/works/VideoWind/storage/tasks/0196a908-e813-74a5-9a07-032fd72f9fdd/audio.mp3"
    subtitle_path = "/Users/gary/works/VideoWind/storage/tasks/0196a908-e813-74a5-9a07-032fd72f9fdd/subtitle.srt"
    output_file = f"/Users/gary/works/VideoWind/storage/tasks/0196a908-e813-74a5-9a07-032fd72f9fdd/output-{str(datetime.datetime.now())}.mp4"
    params = VideoRequest(**{
        "video_script": "Wise men speak because they have something to say, fools because they have to say something.",
        "video_language": "",
        "voice_name": "en-US-AvaMultilingualNeural",
        "voice_volume": 1,
        "bgm_file": "",
        "bgm_volume": 0.2,
        "subtitle_enabled": True,
        "font_name": "JosefinSans-Light.ttf",
        "text_fore_color": "#FFFFFF",
        "text_background_color": "#000000",
        "font_size": 60,
        "stroke_color": "#000000",
        "stroke_width": 2,
        "video_subject": "string",
        "video_terms": "",
        "video_source": "pexels",
        "video_aspect": "9:16",
        "video_concat_mode": "random",
        "video_transition_mode": "None",
        "video_clip_duration": 5,
        "video_count": 1,
        "video_materials": [
            {
                "provider": "pexels",
                "url": "",
                "duration": 0
            }
        ],
        "subtitle_position": "BOTTOM",
        "subtitle_custom_position": 70,
        "n_threads": 2,
        "paragraph_number": 1
    })
    generate_video(video_path, audio_path, subtitle_path, output_file, params)


def test_get_bgm_file():
    assert get_bgm_file("") is None
    assert get_bgm_file("random").is_file()
    assert get_bgm_file("wrong-bgm.mp3") is None
    assert get_bgm_file("output000.mp3").is_file()

