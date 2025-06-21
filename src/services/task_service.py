import math
import os.path
import re
from os import path
from typing import Union
from loguru import logger

from src.config import config
from src.constants.enums import TaskStatus, StopAt
from src.crud.task_crud import TaskCrud
from src.models.schema import VideoConcatMode, VideoRequest, AudioRequest, SubtitleRequest
from src.services import llm, material, subtitle, video_service
from src.services.voice_service import azure_tts_v2, get_audio_duration, create_subtitle, azure_tts_generate_with_srt
from src.utils import utils


class TaskService:
    def _generate_script(self, task_id, params):
        logger.info("\n\n## generating video script")
        video_script = params.video_script.strip()
        if not video_script:
            video_script = llm.generate_script(
                video_subject=params.video_subject,
                language=params.video_language,
                paragraph_number=params.paragraph_number,
            )
        else:
            logger.debug(f"video script: \n{video_script}")

        if not video_script:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="failed to generate video script.")
            logger.error("failed to generate video script.")
            return None

        return video_script


    def _generate_terms(self, task_id, params, video_script):
        logger.info("\n\n## generating video terms")
        video_terms = params.video_terms
        if not video_terms:
            video_terms = llm.generate_terms(
                video_subject=params.video_subject, video_script=video_script, amount=5
            )
        else:
            if isinstance(video_terms, str):
                video_terms = [term.strip() for term in re.split(r"[,，]", video_terms)]
            elif isinstance(video_terms, list):
                video_terms = [term.strip() for term in video_terms]
            else:
                raise ValueError("video_terms must be a string or a list of strings.")

            logger.debug(f"video terms: {utils.to_json(video_terms)}")

        if not video_terms:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="failed to generate video terms.")
            logger.error("failed to generate video terms.")
            return None

        return video_terms

    @staticmethod
    def validate_voice_acceleration(rate) -> str:
        if re.fullmatch(r"[+-]?\d+%", rate.strip()):
            return rate.strip()

        logger.warning(f"voice acceleration [{rate}] is not valid, use default [+0%].")
        return "+0%"

    def _generate_audio(self, task_id, params, video_script):
        logger.info("\n\n## generating audio")
        audio_file = path.join(utils.task_dir(task_id), "audio.mp3")
        sub_maker = azure_tts_v2(
            text=video_script,
            voice_name=params.voice_name,
            voice_file=audio_file,
            rate=self.validate_voice_acceleration(params.voice_acceleration),
        )

        if sub_maker is None:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="failed to generate audio.")
            logger.error(
                """failed to generate audio:
    1. check if the language of the voice matches the language of the video script.
    2. check if the network is available. If you are in China, it is recommended to use a VPN and enable the global traffic mode.
            """.strip()
            )
            return None, None, None

        audio_duration = get_audio_duration(sub_maker)
        return audio_file, audio_duration, sub_maker


    def _generate_subtitle(self, task_id, params, video_script, sub_maker, audio_file):
        if not params.subtitle_enabled:
            return ""

        subtitle_path = path.join(utils.task_dir(task_id), "subtitle.srt")
        subtitle_provider = config.app.get("subtitle_provider", "").strip().lower()
        logger.info(f"\n\n## generating subtitle, provider: {subtitle_provider}")

        subtitle_fallback = False
        if subtitle_provider == "edge":
            create_subtitle(
                text=video_script, sub_maker=sub_maker, subtitle_file=subtitle_path
            )
            if not os.path.exists(subtitle_path):
                subtitle_fallback = True
                logger.warning("subtitle file not found, fallback to whisper")

        if subtitle_provider == "whisper" or subtitle_fallback:
            subtitle.create(audio_file=audio_file, subtitle_file=subtitle_path)
            logger.info("\n\n## correcting subtitle")
            subtitle.correct(subtitle_file=subtitle_path, video_script=video_script)

        subtitle_lines = subtitle.file_to_subtitles(subtitle_path)
        if not subtitle_lines:
            logger.warning(f"subtitle file is invalid: {subtitle_path}")
            return ""

        return subtitle_path


    def _get_video_materials(self, task_id, params, video_terms, audio_duration):
        if params.video_source == "local":
            logger.info("\n\n## preprocess local materials")
            materials = video_service.preprocess_video(
                materials=params.video_materials, clip_duration=params.video_clip_duration
            )
            if not materials:
                TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="no valid materials found.")
                logger.error(
                    "no valid materials found, please check the materials and try again."
                )
                return None
            return [material_info.url for material_info in materials]
        else:
            logger.info(f"\n\n## downloading videos from {params.video_source}")
            downloaded_videos = material.download_videos(
                task_id=task_id,
                search_terms=video_terms,
                source=params.video_source,
                video_aspect=params.video_aspect,
                video_contact_mode=params.video_concat_mode,
                audio_duration=audio_duration * params.video_count,
                max_clip_duration=params.video_clip_duration,
            )
            if not downloaded_videos:
                TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="failed to download videos.")
                logger.error(
                    "failed to download videos, maybe the network is not available. if you are in China, please use a VPN."
                )
                return None
            return downloaded_videos


    def _generate_final_videos(self, task_id, params, downloaded_videos, audio_file, subtitle_path):
        final_video_paths = []
        combined_video_paths = []
        video_concat_mode = (
            params.video_concat_mode if params.video_count == 1 else VideoConcatMode.random
        )
        video_transition_mode = params.video_transition_mode

        for i in range(params.video_count):
            index = i + 1
            combined_video_path = path.join(
                utils.task_dir(task_id), f"combined-{index}.mp4"
            )
            logger.info(f"Combining video: {index} => {combined_video_path}")
            video_service.combine_videos(
                combined_video_path=combined_video_path,
                video_paths=downloaded_videos,
                audio_file=audio_file,
                video_aspect=params.video_aspect,
                video_concat_mode=video_concat_mode,
                video_transition_mode=video_transition_mode,
                max_clip_duration=params.video_clip_duration,
                threads=params.n_threads,
            )

            final_video_path = path.join(utils.task_dir(task_id), f"final-{index}.mp4")

            logger.info(f"\n\n## generating video: {index} => {final_video_path}")
            video_service.generate_video(
                video_path=combined_video_path,
                audio_path=audio_file,
                subtitle_path=subtitle_path,
                output_file=final_video_path,
                params=params,
            )

            final_video_paths.append(final_video_path)
            combined_video_paths.append(combined_video_path)

        return final_video_paths, combined_video_paths


    def start(self, task_id: str, params: Union[VideoRequest, AudioRequest, SubtitleRequest], stop_at: StopAt = StopAt.VIDEO):
        # task_id = TaskCrud.add_task(params, stop_at)
        logger.info(f"start task: {task_id}, stop_at: {stop_at}")

        # 1. Generate script
        video_script = self._generate_script(task_id, params)
        if not video_script or "Error: " in video_script:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="Generate video script error.")
            return

        TaskCrud.update_task(task_id, TaskStatus.SCRIPT_GENERATED, {"script": video_script})
        if stop_at == StopAt.SCRIPT:
            return {"id": task_id, "script": video_script}

        # 2. Generate audio
        audio_file, audio_duration, sub_maker = self._generate_audio(
            task_id, params, video_script
        )

        if not audio_file:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="Generate audio error.")
            return

        TaskCrud.update_task(task_id, TaskStatus.AUDIO_GENERATED, {
            "audio_file": audio_file,
            "audio_duration": audio_duration,
        })

        if stop_at == StopAt.AUDIO:
            return {"id": task_id, "audio_file": audio_file, "audio_duration": audio_duration}

        # 3. Generate subtitle
        subtitle_path = self._generate_subtitle(
            task_id, params, video_script, sub_maker, audio_file
        )
        TaskCrud.update_task(task_id, TaskStatus.SUBTITLE_GENERATED, {
            "audio_file": audio_file,
            "audio_duration": audio_duration,
            "subtitle_path": subtitle_path
        })

        if stop_at == StopAt.SUBTITLE:
            return {"id": task_id, "subtitle_path": subtitle_path}

        if type(params.video_concat_mode) is str:
            params.video_concat_mode = VideoConcatMode(params.video_concat_mode)

        # 4. Generate terms
        video_terms = ""
        if params.video_source != "local":
            video_terms = self._generate_terms(task_id, params, video_script)
            if not video_terms:
                TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="Generate video terms error.")
                return

        TaskCrud.update_task(task_id, TaskStatus.TERMS_GENERATED, {
            "audio_file": audio_file,
            "audio_duration": audio_duration,
            "subtitle_path": subtitle_path,
            "terms": video_terms,
        })

        if stop_at == StopAt.TERMS:
            return {"id": task_id, "script": video_script, "terms": video_terms}

        # 5. Get video materials
        downloaded_videos = self._get_video_materials(
            task_id, params, video_terms, audio_duration
        )
        if not downloaded_videos:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="Get video materials error.")
            return

        TaskCrud.update_task(task_id, TaskStatus.CLIPS_DOWNLOADED, {
            "terms": video_terms,
            "audio_file": audio_file,
            "audio_duration": audio_duration,
            "subtitle_path": subtitle_path,
            "materials": downloaded_videos
        })
        if stop_at == StopAt.MATERIALS:
            return {"id": task_id, "materials": downloaded_videos}

        # 6. Generate final videos
        final_video_paths, combined_video_paths = self._generate_final_videos(
            task_id, params, downloaded_videos, audio_file, subtitle_path
        )

        if not final_video_paths:
            TaskCrud.update_task(task_id, TaskStatus.FAILED, failed_reason="Generate final videos error.")
            return

        logger.success(
            f"task {task_id} finished, generated {len(final_video_paths)} videos."
        )

        result = {
            "videos": final_video_paths,
            "combined_videos": combined_video_paths,
            "terms": video_terms,
            "audio_file": audio_file,
            "audio_duration": audio_duration,
            "subtitle_path": subtitle_path,
            "materials": downloaded_videos,
        }
        TaskCrud.update_task(task_id, TaskStatus.FINAL_VIDEO_GENERATED, result)
        return result

