from moviepy import VideoFileClip

from src.constants.config import config
from src.utils.subtitle_utils import VideoDimension, add_subtitle, SubtitleStyle
from tests import VIDEOS_DIR, SUBTITLES_DIR, FONTS_DIR


def test_add_subtitle():
    test_filename = "vid-708def2b38ddb0ae4f8709df51aac2e1.mp4"
    video_clip = VideoFileClip(VIDEOS_DIR.joinpath(test_filename))
    video_dimension = VideoDimension(width=1280, height=720)

    font_path = FONTS_DIR.joinpath("JosefinSans-Light.ttf").as_posix()
    subtitle_path = SUBTITLES_DIR.joinpath("subtitle-22s.srt").as_posix()
    sub_style = SubtitleStyle(
        position="bottom",
        custom_position=0,
        font_path=font_path,
        font_size=60,
        text_fore_color="#FFFFFF",
        text_background_color="#000000",
        stroke_color="#000000",
        stroke_width=2
    )
    clip = add_subtitle(video_clip, video_dimension, subtitle_path, sub_style)

    expected_output_file = config.DIR.storage_dir.joinpath(f"temp/test2-{test_filename}")
    clip.write_videofile(
        expected_output_file.as_posix(),
        audio_codec="aac",
        temp_audiofile_path=expected_output_file.parent.as_posix(),
        threads=3,
        logger=None,
        fps=30,
    )

    assert expected_output_file.exists()