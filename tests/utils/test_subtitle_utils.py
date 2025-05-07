from moviepy import VideoFileClip

from src.constants.config import DirConfig
from src.constants.enums import SubtitlePosition
from src.utils.subtitle_utils import VideoDimension, add_subtitle, SubtitleStyle
from tests import VIDEOS_DIR, SUBTITLES_DIR, FONTS_DIR

sub_style = SubtitleStyle(
    position=SubtitlePosition.BOTTOM,
    custom_position=0,
    font_path=FONTS_DIR.joinpath("JosefinSans-Light.ttf").as_posix(),
    font_size=60,
    text_fore_color="#FFFFFF",
    text_background_color="#000000",
    stroke_color="#000000",
    stroke_width=2
)


def test_add_subtitle():
    test_filename = "1280x720.mp4"
    video_clip = VideoFileClip(VIDEOS_DIR.joinpath(test_filename))
    video_dimension = VideoDimension(width=1280, height=720)
    subtitle_path = SUBTITLES_DIR.joinpath("subtitle-6s.srt").as_posix()

    clip = add_subtitle(video_clip, video_dimension, subtitle_path, sub_style)

    expected_output_file = DirConfig.storage_dir.joinpath(f"temp/test_add_subtitle-{test_filename}")
    clip.write_videofile(
        expected_output_file.as_posix(),
        audio_codec="aac",
        temp_audiofile_path=expected_output_file.parent.as_posix(),
        threads=3,
        logger=None,
        fps=30,
    )

    assert expected_output_file.exists()


def test_add_subtitle2():
    test_filename = "720x1280.mp4"
    video_clip = VideoFileClip(VIDEOS_DIR.joinpath(test_filename))
    video_dimension = VideoDimension(width=720, height=1280)
    subtitle_path = SUBTITLES_DIR.joinpath("subtitle-6s.srt").as_posix()

    clip = add_subtitle(video_clip, video_dimension, subtitle_path, sub_style)

    expected_output_file = DirConfig.storage_dir.joinpath(f"temp/test_add_subtitle2-{test_filename}")
    clip.write_videofile(
        expected_output_file.as_posix(),
        audio_codec="aac",
        temp_audiofile_path=expected_output_file.parent.as_posix(),
        threads=3,
        logger=None,
        fps=30,
    )

    assert expected_output_file.exists()