import asyncio
import os
import re
from datetime import datetime
from typing import Union, List, Tuple
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
from src.constants.config import AiConfig, DirConfig
from src.models.schema import VoiceOut
from src.utils import utils
from src.utils.file_utils import write_json


@lru_cache(maxsize=5)
def get_azure_voices() -> List[VoiceOut]:
    tts_base_url = f"https://{AiConfig.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices"
    tts_headers = {"Ocp-Apim-Subscription-Key": AiConfig.azure_speech_key}
    response = requests.get(f'{tts_base_url}/voices/list', headers=tts_headers)
    data = response.json()
    asyncio.run(write_json(DirConfig.storage_dir.joinpath("voices/azure-voices.json"), data))
    return [VoiceOut(**d) for d in data]


@lru_cache(maxsize=5)
def get_azure_voice_locales() -> List[str]:
    voices = get_azure_voices()
    locales = set()
    for v in voices:
        locales.add(v.Locale)

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


def azure_tts_v2(text: str, voice_name: str, voice_file: str, rate: str = "+50%") -> Union[SubMaker, None]:
    text = text.strip()
    sub_maker = SubMaker()

    def speech_synthesizer_word_boundary_cb(evt: speechsdk.SessionEventArgs):
        duration = _format_duration_to_offset(str(evt.duration))
        offset = _format_duration_to_offset(evt.audio_offset)
        sub_maker.subs.append(evt.text)
        sub_maker.offset.append((offset, offset + duration))

    try:
        logger.info(f"start, voice name: {voice_name}")

        audio_config = speechsdk.audio.AudioOutputConfig(filename=voice_file, use_default_speaker=True)
        speech_config = speechsdk.SpeechConfig(subscription=AiConfig.azure_speech_key, region=AiConfig.azure_speech_region)
        speech_config.speech_synthesis_voice_name = voice_name

        speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestWordBoundary, value="true")
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )

        speech_synthesizer = speechsdk.SpeechSynthesizer(audio_config=audio_config, speech_config=speech_config)
        speech_synthesizer.synthesis_word_boundary.connect(speech_synthesizer_word_boundary_cb)

        # Wrap text in SSML with prosody rate
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
               xmlns:mstts="http://www.w3.org/2001/mstts"
               xml:lang="en-US">
          <voice name="{voice_name}">
            <prosody rate="{rate}">{text}</prosody>
          </voice>
        </speak>
        """

        result = speech_synthesizer.speak_ssml_async(ssml_text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.success(f"azure v2 speech synthesis succeeded: {voice_file}")
            return sub_maker
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.error(f"azure v2 speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logger.error(f"azure v2 speech synthesis error: {cancellation_details.error_details}")
        logger.info(f"completed, output file: {voice_file}")
    except Exception as e:
        logger.error(f"failed, error: {str(e)}")
    return None


def _format_srt_timestamp(ms: int) -> str:
    seconds, millis = divmod(ms, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def azure_tts_generate_with_srt(text: str, voice_name: str, audio_file: str, srt_file: str) -> int:
    word_timings: List[Tuple[str, int]] = []

    def on_word_boundary(evt: speechsdk.SpeechSynthesisWordBoundaryEventArgs):
        word_timings.append((evt.text, evt.audio_offset // 10000))  # convert 100-nanosecond to milliseconds

    try:
        print(f"Starting synthesis with voice: {voice_name}")

        speech_config = speechsdk.SpeechConfig(
            subscription=AiConfig.azure_speech_key,
            region=AiConfig.azure_speech_region
        )
        speech_config.speech_synthesis_voice_name = voice_name
        speech_config.set_property(
            property_id=speechsdk.PropertyId.SpeechServiceResponse_RequestWordBoundary,
            value="true"
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
        )

        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file)

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        synthesizer.synthesis_word_boundary.connect(on_word_boundary)

        result = synthesizer.speak_text_async(text.strip()).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.success("Speech synthesis succeeded.")
        else:
            logger.error("Speech synthesis failed.")
            return 0

        audio_duration = int(result.audio_duration.total_seconds())

        # Group words into compact subtitle chunks
        max_words: int = 7
        max_duration_ms: int = 2500

        # Calculate word ranges: (text, start_ms, end_ms)
        word_ranges = []
        for i in range(len(word_timings)):
            word = word_timings[i][0]
            start = word_timings[i][1]
            end = word_timings[i + 1][1] if i + 1 < len(word_timings) else start + 500
            word_ranges.append((word, start, end))

        # Group into subtitle chunks
        subtitles = []
        chunk = []
        chunk_start = word_ranges[0][1]

        for word, start, end in word_ranges:
            if not chunk:
                chunk_start = start
            chunk.append((word, start, end))
            chunk_duration = end - chunk_start

            if (
                    len(chunk) >= max_words
                    or chunk_duration >= max_duration_ms
                    or word.strip().endswith(('.', '?', '!'))
            ):
                text_line = ' '.join(w for w, _, _ in chunk)
                subtitles.append((chunk[0][1], chunk[-1][2], text_line))
                chunk = []

        if chunk:
            text_line = ' '.join(w for w, _, _ in chunk)
            subtitles.append((chunk[0][1], chunk[-1][2], text_line))

        # Write SRT
        with open(srt_file, "w", encoding="utf-8") as f:
            for idx, (start, end, line) in enumerate(subtitles):
                f.write(f"{idx + 1}\n")
                f.write(f"{_format_srt_timestamp(start)} --> {_format_srt_timestamp(end)}\n")
                f.write(f"{line}\n\n")

        print(f"SRT written to {srt_file}, Audio to {audio_file}")
        return audio_duration
    except Exception as e:
        print(f"Error during synthesis: {str(e)}")


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

