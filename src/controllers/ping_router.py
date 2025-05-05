from fastapi import APIRouter, Request

router = APIRouter()


@router.get(
    "/ping",
    tags=["Health Check"],
    description="Check if the server is running",
    response_description="pong",
)
def ping(request: Request) -> int:
    return 1
