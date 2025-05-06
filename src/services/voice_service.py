import asyncio
import os
import re
from datetime import datetime
from typing import Union, List
from xml.sax.saxutils import unescape
import requests
import edge_tts
from functools import lru_cache
from edge_tts import SubMaker, submaker
from edge_tts.submaker import mktimestamp
from loguru import logger
from moviepy.video.tools import subtitles
import azure.cognitiveservices.speech as speechsdk

from src.config import config
from src.constants.config import AiConfig
from src.models.schema import VoiceOut
from src.utils import utils


@lru_cache(maxsize=5)
def get_azure_voices() -> List[VoiceOut]:
    tts_base_url = f"https://{AiConfig.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices"
    tts_headers = {"Ocp-Apim-Subscription-Key": AiConfig.azure_speech_key}
    response = requests.get(f'{tts_base_url}/voices/list', headers=tts_headers)
    return [VoiceOut(**d) for d in response.json()]


@lru_cache(maxsize=5)
def get_azure_voice_locales() -> List[str]:
    voices = get_azure_voices()
    locales = set()
    for v in voices:
        locales.add(v.Locale)
        if v.SecondaryLocaleList:
            locales.update(v.SecondaryLocaleList)

    return sorted(list(locales))


def _format_duration_to_offset(duration) -> int:
    if isinstance(duration, str):
        time_obj = datetime.strptime(duration, "%H:%M:%S.%f")
        milliseconds = (
                (time_obj.hour * 3600000)
                + (time_obj.minute * 60000)
                + (time_obj.second * 1000)
                + (time_obj.microsecond // 1000)
        )
        return milliseconds * 10000

    if isinstance(duration, int):
        return duration

    return 0


def azure_tts_v2(text: str, voice_name: str, voice_file: str) -> Union[SubMaker, None]:
    text = text.strip()
    sub_maker = SubMaker()

    def speech_synthesizer_word_boundary_cb(evt: speechsdk.SessionEventArgs):
        duration = _format_duration_to_offset(str(evt.duration))
        offset = _format_duration_to_offset(evt.audio_offset)
        sub_maker.subs.append(evt.text)
        sub_maker.offset.append((offset, offset + duration))

    try:
        logger.info(f"start, voice name: {voice_name}")

        # Creates an instance of a speech config with specified subscription key and service region.
        speech_key = config.azure.get("speech_key", "")
        service_region = config.azure.get("speech_region", "")
        audio_config = speechsdk.audio.AudioOutputConfig(
            filename=voice_file, use_default_speaker=True
        )
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=service_region
        )
        speech_config.speech_synthesis_voice_name = voice_name
        # speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestSentenceBoundary,
        #                            value='true')
        speech_config.set_property(
            property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestWordBoundary,
            value="true",
        )

        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            audio_config=audio_config, speech_config=speech_config
        )
        speech_synthesizer.synthesis_word_boundary.connect(
            speech_synthesizer_word_boundary_cb
        )

        result = speech_synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.success(f"azure v2 speech synthesis succeeded: {voice_file}")
            return sub_maker
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.error(
                f"azure v2 speech synthesis canceled: {cancellation_details.reason}"
            )
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error(
                    f"azure v2 speech synthesis error: {cancellation_details.error_details}"
                )
        logger.info(f"completed, output file: {voice_file}")
    except Exception as e:
        logger.error(f"failed, error: {str(e)}")
    return None


def _format_text(text: str) -> str:
    # text = text.replace("\n", " ")
    text = text.replace("[", " ")
    text = text.replace("]", " ")
    text = text.replace("(", " ")
    text = text.replace(")", " ")
    text = text.replace("{", " ")
    text = text.replace("}", " ")
    text = text.strip()
    return text


def create_subtitle(sub_maker: submaker.SubMaker, text: str, subtitle_file: str):
    """
    优化字幕文件
    1. 将字幕文件按照标点符号分割成多行
    2. 逐行匹配字幕文件中的文本
    3. 生成新的字幕文件
    """

    text = _format_text(text)

    def formatter(idx: int, start_time: float, end_time: float, sub_text: str) -> str:
        """
        1
        00:00:00,000 --> 00:00:02,360
        跑步是一项简单易行的运动
        """
        start_t = mktimestamp(start_time).replace(".", ",")
        end_t = mktimestamp(end_time).replace(".", ",")
        return f"{idx}\n" f"{start_t} --> {end_t}\n" f"{sub_text}\n"

    start_time = -1.0
    sub_items = []
    sub_index = 0

    script_lines = utils.split_string_by_punctuations(text)

    def match_line(_sub_line: str, _sub_index: int):
        if len(script_lines) <= _sub_index:
            return ""

        _line = script_lines[_sub_index]
        if _sub_line == _line:
            return script_lines[_sub_index].strip()

        _sub_line_ = re.sub(r"[^\w\s]", "", _sub_line)
        _line_ = re.sub(r"[^\w\s]", "", _line)
        if _sub_line_ == _line_:
            return _line_.strip()

        _sub_line_ = re.sub(r"\W+", "", _sub_line)
        _line_ = re.sub(r"\W+", "", _line)
        if _sub_line_ == _line_:
            return _line.strip()

        return ""

    sub_line = ""

    try:
        for _, (offset, sub) in enumerate(zip(sub_maker.offset, sub_maker.subs)):
            _start_time, end_time = offset
            if start_time < 0:
                start_time = _start_time

            sub = unescape(sub)
            sub_line += sub
            sub_text = match_line(sub_line, sub_index)
            if sub_text:
                sub_index += 1
                line = formatter(
                    idx=sub_index,
                    start_time=start_time,
                    end_time=end_time,
                    sub_text=sub_text,
                )
                sub_items.append(line)
                start_time = -1.0
                sub_line = ""

        if len(sub_items) == len(script_lines):
            with open(subtitle_file, "w", encoding="utf-8") as file:
                file.write("\n".join(sub_items) + "\n")
            try:
                sbs = subtitles.file_to_subtitles(subtitle_file, encoding="utf-8")
                duration = max([tb for ((ta, tb), txt) in sbs])
                logger.info(
                    f"completed, subtitle file created: {subtitle_file}, duration: {duration}"
                )
            except Exception as e:
                logger.error(f"failed, error: {str(e)}")
                os.remove(subtitle_file)
        else:
            logger.warning(
                f"failed, sub_items len: {len(sub_items)}, script_lines len: {len(script_lines)}"
            )

    except Exception as e:
        logger.error(f"failed, error: {str(e)}")


def get_audio_duration(sub_maker: submaker.SubMaker):
    """
    获取音频时长
    """
    if not sub_maker.offset:
        return 0.0
    return sub_maker.offset[-1][1] / 10000000

