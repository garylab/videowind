from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy import CompositeVideoClip
from moviepy import TextClip, VideoFileClip
from pydantic import BaseModel
from PIL import ImageFont


class SubtitleStyle(BaseModel):
    position: str
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


def add_subtitle(video_clip: VideoFileClip, video_dimension: VideoDimension,  subtitle_path: str, sub_style: SubtitleStyle):
    def make_textclip(text: str):
        return TextClip(
            text=text,
            font=sub_style.font_path,
            font_size=sub_style.font_size,
        )

    sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8", make_textclip=make_textclip)

    text_clips = []
    for item in sub.subtitles:
        clip = create_text_clip(subtitle_item=item, video_dimension=video_dimension, sub_style=sub_style)
        text_clips.append(clip)

    return CompositeVideoClip([video_clip, *text_clips])


def create_text_clip(subtitle_item, video_dimension: VideoDimension, sub_style: SubtitleStyle):
    phrase = subtitle_item[1]
    max_width = video_dimension.width * 0.9
    wrapped_txt, txt_height = wrap_text(
        phrase, max_width=max_width, font=sub_style.font_path, fontsize=sub_style.font_size
    )
    interline = int(sub_style.font_size * 0.25)
    size=(int(max_width), int(txt_height + sub_style.font_size * 0.25 + (interline * (wrapped_txt.count("\n") + 1))))

    _clip = TextClip(
        text=wrapped_txt,
        font=sub_style.font_path,
        font_size=sub_style.font_size,
        color=sub_style.text_fore_color,
        bg_color=sub_style.text_background_color,
        stroke_color=sub_style.stroke_color,
        stroke_width=sub_style.stroke_width,
        interline=interline,
        size=size,
    )
    duration = subtitle_item[0][1] - subtitle_item[0][0]
    _clip = _clip.with_start(subtitle_item[0][0])
    _clip = _clip.with_end(subtitle_item[0][1])
    _clip = _clip.with_duration(duration)

    if sub_style.position == "bottom":
        _clip = _clip.with_position(("center", video_dimension.height * 0.95 - _clip.h))
    elif sub_style.position == "top":
        _clip = _clip.with_position(("center", video_dimension.height * 0.05))
    elif sub_style.position == "custom":
        # Ensure the subtitle is fully within the screen bounds
        margin = 10  # Additional margin, in pixels
        max_y = video_dimension.height - _clip.h - margin
        min_y = margin
        custom_y = (video_dimension.height - _clip.h) * (sub_style.custom_position / 100)
        custom_y = max(
            min_y, min(custom_y, max_y)
        )  # Constrain the y value within the valid range
        _clip = _clip.with_position(("center", custom_y))
    else:  # center
        _clip = _clip.with_position(("center", "center"))
    return _clip


def wrap_text(text, max_width, font="Arial", fontsize=60):
    # Create ImageFont
    font = ImageFont.truetype(font, fontsize)

    def get_text_size(inner_text):
        inner_text = inner_text.strip()
        left, top, right, bottom = font.getbbox(inner_text)
        return right - left, bottom - top

    width, height = get_text_size(text)
    if width <= max_width:
        return text, height

    # logger.warning(f"wrapping text, max_width: {max_width}, text_width: {width}, text: {text}")

    processed = True

    _wrapped_lines_ = []
    words = text.split(" ")
    _txt_ = ""
    for word in words:
        _before = _txt_
        _txt_ += f"{word} "
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            if _txt_.strip() == word.strip():
                processed = False
                break
            _wrapped_lines_.append(_before)
            _txt_ = f"{word} "
    _wrapped_lines_.append(_txt_)
    if processed:
        _wrapped_lines_ = [line.strip() for line in _wrapped_lines_]
        result = "\n".join(_wrapped_lines_).strip()
        height = len(_wrapped_lines_) * height
        # logger.warning(f"wrapped text: {result}")
        return result, height

    _wrapped_lines_ = []
    chars = list(text)
    _txt_ = ""
    for word in chars:
        _txt_ += word
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            _wrapped_lines_.append(_txt_)
            _txt_ = ""
    _wrapped_lines_.append(_txt_)
    result = "\n".join(_wrapped_lines_).strip()
    height = len(_wrapped_lines_) * height
    # logger.warning(f"wrapped text: {result}")
    return result, height