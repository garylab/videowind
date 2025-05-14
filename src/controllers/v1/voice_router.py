from typing import List

from fastapi import APIRouter
from fastapi import Depends

from src.constants.enums import VoiceType
from src.models.schema import VoiceParams, VoiceOut
from src.services.voice_service import get_azure_voices, get_azure_voice_locales

router = APIRouter(tags=["Voices"], prefix="/voices")


@router.get("", response_model=List[VoiceOut])
def get_all_voices(params: VoiceParams = Depends()):
    voices = get_azure_voices()
    results = []
    for v in voices:
        condition = True
        if params.q:
            condition = params.q in v.ShortName

        if params.locale:
            condition = condition and params.locale.lower() == v.Locale.lower()

        if params.gender:
            condition = condition and params.gender.value.lower() == v.Gender.lower()

        if params.type:
            if params.type == VoiceType.MULTILINGUAL_NEURAL:
                condition = condition and v.ShortName.lower().endswith(VoiceType.MULTILINGUAL_NEURAL.value.lower())
            else:
                condition = condition and not v.ShortName.lower().endswith(VoiceType.MULTILINGUAL_NEURAL.value.lower())

        if condition:
            results.append(v)

    return results


@router.get("/locales", response_model=List[str])
def get_all_locales():
    return get_azure_voice_locales()
