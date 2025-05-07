import glob
import os
import random
from typing import List
from moviepy import Clip, vfx
from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
)

from src.models import const
from src.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoRequest,
    VideoTransitionMode,
)
from src.utils import utils
from src.utils.subtitle_utils import add_subtitle, VideoDimension, SubtitleStyle


def get_bgm_file(bgm_type: str = "random", bgm_file: str = ""):
    if not bgm_type:
        return ""

    if bgm_file and os.path.exists(bgm_file):
        return bgm_file

    if bgm_type == "random":
        suffix = "*.mp3"
        song_dir = utils.song_dir()
        files = glob.glob(os.path.join(song_dir, suffix))
        return random.choice(files)

    return ""


def combine_videos(
    combined_video_path: str,
    video_paths: List[str],
    audio_file: str,
    video_aspect: VideoAspect = VideoAspect.portrait,
    video_concat_mode: VideoConcatMode = VideoConcatMode.random,
    video_transition_mode: VideoTransitionMode = None,
    max_clip_duration: int = 5,
    threads: int = 2,
) -> str:
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration
    logger.info(f"max duration of audio: {audio_duration} seconds")
    # Required duration of each clip
    req_dur = audio_duration / len(video_paths)
    req_dur = max_clip_duration
    logger.info(f"each clip will be maximum {req_dur} seconds long")
    output_dir = os.path.dirname(combined_video_path)

    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()

    clips = []
    video_duration = 0

    raw_clips = []
    for video_path in video_paths:
        clip = VideoFileClip(video_path).without_audio()
        clip_duration = clip.duration
        start_time = 0

        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)
            split_clip = clip.subclipped(start_time, end_time)
            raw_clips.append(split_clip)
            # logger.info(f"splitting from {start_time:.2f} to {end_time:.2f}, clip duration {clip_duration:.2f}, split_clip duration {split_clip.duration:.2f}")
            start_time = end_time
            if video_concat_mode.value == VideoConcatMode.sequential.value:
                break

    # random video_paths order
    if video_concat_mode.value == VideoConcatMode.random.value:
        random.shuffle(raw_clips)

    # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
    while video_duration < audio_duration:
        for clip in raw_clips:
            # Check if clip is longer than the remaining audio
            if (audio_duration - video_duration) < clip.duration:
                clip = clip.subclipped(0, (audio_duration - video_duration))
            # Only shorten clips if the calculated clip length (req_dur) is shorter than the actual clip to prevent still image
            elif req_dur < clip.duration:
                clip = clip.subclipped(0, req_dur)
            clip = clip.with_fps(30)

            # Not all videos are same size, so we need to resize them
            clip_w, clip_h = clip.size
            if clip_w != video_width or clip_h != video_height:
                clip_ratio = clip.w / clip.h
                video_ratio = video_width / video_height

                if clip_ratio == video_ratio:
                    # Resize proportionally
                    clip = clip.resized((video_width, video_height))
                else:
                    # Resize proportionally
                    if clip_ratio > video_ratio:
                        # Resize proportionally based on the target width
                        scale_factor = video_width / clip_w
                    else:
                        # Resize proportionally based on the target height
                        scale_factor = video_height / clip_h

                    new_width = int(clip_w * scale_factor)
                    new_height = int(clip_h * scale_factor)
                    clip_resized = clip.resized(new_size=(new_width, new_height))

                    background = ColorClip(
                        size=(video_width, video_height), color=(0, 0, 0)
                    )
                    clip = CompositeVideoClip(
                        [
                            background.with_duration(clip.duration),
                            clip_resized.with_position("center"),
                        ]
                    )

                logger.info(
                    f"resizing video to {video_width} x {video_height}, clip size: {clip_w} x {clip_h}"
                )

            shuffle_side = random.choice(["left", "right", "top", "bottom"])
            logger.info(f"Using transition mode: {video_transition_mode}")
            if video_transition_mode.value == VideoTransitionMode.none.value:
                clip = clip
            elif video_transition_mode.value == VideoTransitionMode.fade_in.value:
                clip = fadein_transition(clip, 1)
            elif video_transition_mode.value == VideoTransitionMode.fade_out.value:
                clip = fadeout_transition(clip, 1)
            elif video_transition_mode.value == VideoTransitionMode.slide_in.value:
                clip = slidein_transition(clip, 1, shuffle_side)
            elif video_transition_mode.value == VideoTransitionMode.slide_out.value:
                clip = slideout_transition(clip, 1, shuffle_side)
            elif video_transition_mode.value == VideoTransitionMode.shuffle.value:
                transition_funcs = [
                    lambda c: fadein_transition(c, 1),
                    lambda c: fadeout_transition(c, 1),
                    lambda c: slidein_transition(c, 1, shuffle_side),
                    lambda c: slideout_transition(c, 1, shuffle_side),
                ]
                shuffle_transition = random.choice(transition_funcs)
                clip = shuffle_transition(clip)

            if clip.duration > max_clip_duration:
                clip = clip.subclipped(0, max_clip_duration)

            clips.append(clip)
            video_duration += clip.duration
    clips = [CompositeVideoClip([clip]) for clip in clips]
    video_clip = concatenate_videoclips(clips)
    video_clip = video_clip.with_fps(30)
    logger.info("writing")
    # https://github.com/harry0703/MoneyPrinterTurbo/issues/111#issuecomment-2032354030
    video_clip.write_videofile(
        filename=combined_video_path,
        threads=threads,
        logger=None,
        temp_audiofile_path=output_dir,
        audio_codec="aac",
        fps=30,
    )
    video_clip.close()
    logger.success("completed")
    return combined_video_path


def generate_video(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_file: str,
    params: VideoRequest,
):
    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"start, video size: {video_width} x {video_height}")
    logger.info(f"  ① video: {video_path}")
    logger.info(f"  ② audio: {audio_path}")
    logger.info(f"  ③ subtitle: {subtitle_path}")
    logger.info(f"  ④ output: {output_file}")

    # https://github.com/harry0703/MoneyPrinterTurbo/issues/217
    # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'final-1.mp4.tempTEMP_MPY_wvf_snd.mp3'
    # write into the same directory as the output file
    output_dir = os.path.dirname(output_file)

    font_path = ""
    if params.subtitle_enabled:
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
        font_path = os.path.join(utils.font_dir(), params.font_name)
        if os.name == "nt":
            font_path = font_path.replace("\\", "/")

        logger.info(f"using font: {font_path}")

        if not subtitle_path or not os.path.exists(subtitle_path):
            logger.warning("Subtitle enabled, but no subtitle file found at: %s", subtitle_path)

    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path).with_effects(
        [afx.MultiplyVolume(params.voice_volume)]
    )

    if subtitle_path and os.path.exists(subtitle_path):
        dimension = VideoDimension(width=video_width, height=video_height)
        sub_style = SubtitleStyle(
            position=params.subtitle_position,
            custom_position=params.subtitle_custom_position,
            font_path=font_path,
            font_size=params.font_size,
            text_fore_color=params.text_fore_color,
            text_background_color=params.text_background_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
        )
        video_clip = add_subtitle(video_clip, dimension, subtitle_path, sub_style)

    bgm_file = get_bgm_file(bgm_type=params.bgm_type, bgm_file=params.bgm_file)
    if bgm_file:
        try:
            bgm_clip = AudioFileClip(bgm_file).with_effects(
                [
                    afx.MultiplyVolume(params.bgm_volume),
                    afx.AudioFadeOut(3),
                    afx.AudioLoop(duration=video_clip.duration),
                ]
            )
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"failed to add bgm: {str(e)}")

    video_clip = video_clip.with_audio(audio_clip)
    video_clip.write_videofile(
        output_file,
        audio_codec="aac",
        temp_audiofile_path=output_dir,
        threads=params.n_threads or 2,
        logger=None,
        fps=30,
    )
    video_clip.close()
    del video_clip
    logger.success("completed")


def preprocess_video(materials: List[MaterialInfo], clip_duration=4):
    for material in materials:
        if not material.url:
            continue

        ext = utils.parse_extension(material.url)
        try:
            clip = VideoFileClip(material.url)
        except Exception:
            clip = ImageClip(material.url)

        width = clip.size[0]
        height = clip.size[1]
        if width < 480 or height < 480:
            logger.warning(f"video is too small, width: {width}, height: {height}")
            continue

        if ext in const.FILE_TYPE_IMAGES:
            logger.info(f"processing image: {material.url}")
            # Create an image clip and set its duration to 3 seconds
            clip = (
                ImageClip(material.url)
                .with_duration(clip_duration)
                .with_position("center")
            )
            # Apply a zoom effect using the resize method.
            # A lambda function is used to make the zoom effect dynamic over time.
            # The zoom effect starts from the original size and gradually scales up to 120%.
            # t represents the current time, and clip.duration is the total duration of the clip (3 seconds).
            # Note: 1 represents 100% size, so 1.2 represents 120% size.
            zoom_clip = clip.resized(
                lambda t: 1 + (clip_duration * 0.03) * (t / clip.duration)
            )

            # Optionally, create a composite video clip containing the zoomed clip.
            # This is useful when you want to add other elements to the video.
            final_clip = CompositeVideoClip([zoom_clip])

            # Output the video to a file.
            video_file = f"{material.url}.mp4"
            final_clip.write_videofile(video_file, fps=30, logger=None)
            final_clip.close()
            del final_clip
            material.url = video_file
            logger.success(f"completed: {video_file}")
    return materials


# FadeIn
def fadein_transition(clip: Clip, t: float) -> Clip:
    return clip.with_effects([vfx.FadeIn(t)])


# FadeOut
def fadeout_transition(clip: Clip, t: float) -> Clip:
    return clip.with_effects([vfx.FadeOut(t)])


# SlideIn
def slidein_transition(clip: Clip, t: float, side: str) -> Clip:
    return clip.with_effects([vfx.SlideIn(t, side)])


# SlideOut
def slideout_transition(clip: Clip, t: float, side: str) -> Clip:
    return clip.with_effects([vfx.SlideOut(t, side)])
