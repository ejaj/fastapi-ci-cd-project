from __future__ import annotations

import asyncio
import mimetypes
import re
from pathlib import Path
from typing import Annotated, List
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse

from pydantic import BaseModel, Field

router = APIRouter(prefix="/upload", tags=["File Uploads"])

# ─────────────────────────────────────────────────────────────
# "Config" (keep it simple; swap to env/config system later)
# ─────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("var/uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 10 MB per file
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Accept only these MIME types (extend as needed)
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

# Accept only these file extensions (extra guardrail)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

# Chunk size for streaming writes
CHUNK_SIZE = 1024 * 1024  # 1 MB


# ─────────────────────────────────────────────────────────────
# Pydantic DTOs
# ─────────────────────────────────────────────────────────────
class FileMeta(BaseModel):
    filename: str = Field(..., description="Stored filename (sanitized + unique)")
    original_filename: str = Field(..., description="Client-provided name")
    content_type: str
    size_bytes: int
    url: str = Field(..., description="Download URL")


class MultiFileResponse(BaseModel):
    files: List[FileMeta]


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _sanitize_filename(name: str) -> str:
    """
    Very small 'secure filename' helper:
    - keep basename
    - drop path parts, normalize spaces, allow [a-zA-Z0-9._-]
    """
    base = Path(name).name  # drop any path
    base = base.strip().replace(" ", "_")
    base = re.sub(r"[^a-zA-Z0-9._-]", "", base)
    # avoid empty / weird names
    return base or f"file_{uuid4().hex}"


def _has_allowed_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _is_allowed_mime(content_type: str | None, filename: str) -> bool:
    if content_type in ALLOWED_MIME_TYPES:
        return True
    # Fallback: guess from extension if content_type is missing or generic
    guessed, _ = mimetypes.guess_type(filename)
    return guessed in ALLOWED_MIME_TYPES


def _unique_destination(safe_name: str) -> Path:
    ext = Path(safe_name).suffix
    stem = Path(safe_name).stem
    unique = f"{stem}__{uuid4().hex}{ext}"
    return (UPLOAD_DIR / unique).resolve()


async def _save_streaming_with_limit(
        up: UploadFile, dest: Path, max_bytes: int
) -> int:
    """Stream to disk in chunks; enforce a max size. Returns total bytes written."""
    total = 0
    # Ensure destination stays within UPLOAD_DIR (no traversal)
    if not str(dest).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid destination path")

    # Write asynchronously using threadpool for file I/O
    def _write_chunk(path: Path, chunk: bytes, mode: str = "ab"):
        with open(path, mode) as f:
            f.write(chunk)

    # Ensure file is empty (create/truncate)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.touch()
    dest.write_bytes(b"")

    while True:
        chunk = await up.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            # cleanup partial file
            try:
                dest.unlink(missing_ok=True)
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Limit is {max_bytes} bytes",
            )
        await asyncio.to_thread(_write_chunk, dest, chunk)

    # Seek back if caller wants to re-read (optional)
    await up.seek(0)
    return total


# ─────────────────────────────────────────────────────────────
# Single upload
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/single",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    response_model=FileMeta,
    description="Upload a single file with validation and streaming save.",
)
async def upload_single(
        file: Annotated[UploadFile, File(description="File to upload")],
        background: BackgroundTasks,
):
    original = file.filename or "upload.bin"
    safe_original = _sanitize_filename(original)

    if not _has_allowed_extension(safe_original):
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    if not _is_allowed_mime(file.content_type, safe_original):
        raise HTTPException(status_code=400, detail="Unsupported content type")

    dest = _unique_destination(safe_original)

    # Stream to disk with size limit
    size = await _save_streaming_with_limit(file, dest, MAX_FILE_SIZE_BYTES)

    meta = FileMeta(
        filename=dest.name,
        original_filename=original,
        content_type=file.content_type or mimetypes.guess_type(safe_original)[0] or "application/octet-stream",
        size_bytes=size,
        url=f"/upload/files/{dest.name}",
    )

    # Nothing heavy to do after response right now, but example:
    # background.add_task(do_async_postprocess, dest)
    return meta


# ─────────────────────────────────────────────────────────────
# Multiple uploads
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/multiple",
    methods=["POST"],
    response_model=MultiFileResponse,
    description="Upload multiple files in one request.",
)
async def upload_multiple(
        files: Annotated[List[UploadFile], File(description="Multiple files")],
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results: List[FileMeta] = []
    for f in files:
        original = f.filename or "upload.bin"
        safe_original = _sanitize_filename(original)

        if not _has_allowed_extension(safe_original):
            raise HTTPException(status_code=400, detail=f"Unsupported extension: {original}")

        if not _is_allowed_mime(f.content_type, safe_original):
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {original}")

        dest = _unique_destination(safe_original)
        size = await _save_streaming_with_limit(f, dest, MAX_FILE_SIZE_BYTES)

        results.append(
            FileMeta(
                filename=dest.name,
                original_filename=original,
                content_type=f.content_type or mimetypes.guess_type(safe_original)[0] or "application/octet-stream",
                size_bytes=size,
                url=f"/upload/files/{dest.name}",
            )
        )

    return MultiFileResponse(files=results)


# ─────────────────────────────────────────────────────────────
# Upload with extra form metadata
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/with-meta",
    methods=["POST"],
    response_model=FileMeta,
    description="Upload a file along with additional form fields (e.g. title).",
)
async def upload_with_meta(
        title: Annotated[str, Form(min_length=1, max_length=80)],
        description: Annotated[str | None, Form(max_length=300)] = None,
        file: Annotated[UploadFile, File(description="File to upload")] = None,
):
    if file is None:
        raise HTTPException(status_code=400, detail="File is required")

    # Optional business rule example: title must be in filename
    if title.lower() not in (file.filename or "").lower():
        # Just a demo validation; tweak/remove for real apps
        raise HTTPException(status_code=400, detail="Title should appear in filename")

    original = file.filename or "upload.bin"
    safe_original = _sanitize_filename(original)

    if not _has_allowed_extension(safe_original):
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    if not _is_allowed_mime(file.content_type, safe_original):
        raise HTTPException(status_code=400, detail="Unsupported content type")

    dest = _unique_destination(safe_original)
    size = await _save_streaming_with_limit(file, dest, MAX_FILE_SIZE_BYTES)

    return FileMeta(
        filename=dest.name,
        original_filename=original,
        content_type=file.content_type or mimetypes.guess_type(safe_original)[0] or "application/octet-stream",
        size_bytes=size,
        url=f"/upload/files/{dest.name}",
    )


# ─────────────────────────────────────────────────────────────
# Download (serve a stored file)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/files/{stored_name}",
    methods=["GET"],
    description="Download/serve a previously uploaded file.",
)
async def get_file(stored_name: str):
    safe_name = _sanitize_filename(stored_name)
    file_path = (UPLOAD_DIR / safe_name).resolve()

    # Prevent directory traversal
    if not str(file_path).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Try to guess a content type for better UX
    media_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(path=file_path, media_type=media_type)


# ─────────────────────────────────────────────────────────────
# Delete (housekeeping)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/files/{stored_name}",
    methods=["DELETE"],
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a previously uploaded file.",
)
async def delete_file(stored_name: str):
    safe_name = _sanitize_filename(stored_name)
    file_path = (UPLOAD_DIR / safe_name).resolve()

    if not str(file_path).startswith(str(UPLOAD_DIR)):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        file_path.unlink()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {exc}") from exc
    return None


@router.get("/form", response_class=HTMLResponse, include_in_schema=False)
async def upload_form_page():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Upload Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f6f7fb; }
            h1 { color: #333; }
            form { background: #fff; padding: 20px; border-radius: 10px;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 2rem; }
            input[type="file"], input[type="text"], textarea {
                display: block; margin-top: 10px; width: 100%;
            }
            button {
                margin-top: 10px; padding: 10px 15px;
                background: #007bff; color: white; border: none; border-radius: 5px;
                cursor: pointer;
            }
            button:hover { background: #0056b3; }
            hr { margin: 2rem 0; }
        </style>
    </head>
    <body>
        <h1>FastAPI File Upload Demo</h1>

        <h2>Single File Upload</h2>
        <form action="/upload/single" enctype="multipart/form-data" method="post">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>

        <hr>

        <h2>Multiple File Upload</h2>
        <form action="/upload/multiple" enctype="multipart/form-data" method="post">
            <input type="file" name="files" multiple required>
            <button type="submit">Upload Files</button>
        </form>

        <hr>

        <h2>Upload With Metadata</h2>
        <form action="/upload/with-meta" enctype="multipart/form-data" method="post">
            <label>Title:</label>
            <input type="text" name="title" required>
            <label>Description:</label>
            <textarea name="description" rows="3"></textarea>
            <label>File:</label>
            <input type="file" name="file" required>
            <button type="submit">Upload With Info</button>
        </form>

        <p style="margin-top:40px;"><a href="/docs">Go to Swagger Docs</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
