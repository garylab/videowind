import glob
import os
import pathlib
import shutil
from typing import Union
from fastapi import Depends, Path, Request, UploadFile
from fastapi.params import File
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from fastapi_pagination import Params
from fastapi import APIRouter
from src.config import config
from src.constants.enums import StopAt
from src.crud.task_crud import TaskCrud
from src.db.models import Task
from src.models.exception import HttpException
from src.models.schema import (
    AudioRequest,
    BgmRetrieveResponse,
    BgmUploadResponse,
    SubtitleRequest,
    TaskDeletionResponse,
    TaskQueryResponse,
    TaskResponse,
    TaskVideoRequest,
)
from src.utils import utils

# 认证依赖项
# router = new_router(dependencies=[Depends(base.verify_token)])
router = APIRouter(tags=["Music"], prefix="/musics")


@router.get(
    "", response_model=BgmRetrieveResponse, summary="Retrieve local BGM files"
)
def get_bgm_list(request: Request):
    suffix = "*.mp3"
    song_dir = utils.song_dir()
    files = glob.glob(os.path.join(song_dir, suffix))
    bgm_list = []
    for file in files:
        bgm_list.append(
            {
                "name": os.path.basename(file),
                "size": os.path.getsize(file),
                "file": file,
            }
        )
    response = {"files": bgm_list}
    return utils.get_response(200, response)


@router.post(
    "",
    response_model=BgmUploadResponse,
    summary="Upload the BGM file to the songs directory",
)
def upload_bgm_file(file: UploadFile = File(...)):
    # check file ext
    if file.filename.endswith("mp3"):
        song_dir = utils.song_dir()
        save_path = os.path.join(song_dir, file.filename)
        # save file
        with open(save_path, "wb+") as buffer:
            # If the file already exists, it will be overwritten
            file.file.seek(0)
            buffer.write(file.file.read())
        response = {"file": save_path}
        return utils.get_response(200, response)

    raise HttpException(
        "", status_code=400, message=f"Only *.mp3 files can be uploaded"
    )
