from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/forms", tags=["Forms & Files"])


class UploadResponse(BaseModel):
    message: str
    filename: str
    token: str
    content_type: str


@router.api_route(
    "/upload",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    response_model=UploadResponse,
    description="Upload a file and form field together (multipart/form-data)."
)
async def upload_form_and_file(
        token: Annotated[str, Form(description="API token or session ID")],
        file: Annotated[UploadFile, File(description="File to upload")],
):
    # Simple auth-like validation demo
    if token != "secret123":
        raise HTTPException(status_code=401, detail="Invalid token")

    # Read a few bytes to simulate processing (not required)
    contents = await file.read(1024)
    size_preview = len(contents)

    return UploadResponse(
        message=f"File received ({size_preview} bytes preview)",
        filename=file.filename,
        token=token,
        content_type=file.content_type,
    )
