from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Header
from pydantic import BaseModel

router = APIRouter(prefix="/headers-model", tags=["Header Models"])


# ────────────────────────────────────────────────
# Define a common header model
# ────────────────────────────────────────────────
class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []


# ────────────────────────────────────────────────
# Normal usage — auto underscore→hyphen conversion
# ────────────────────────────────────────────────
@router.api_route(
    "/basic",
    methods=["GET"],
    description="Reads multiple headers into a Pydantic model."
)
async def read_headers(headers: Annotated[CommonHeaders, Header()]):
    return {"validated_headers": headers.model_dump()}


# ────────────────────────────────────────────────
# Strict validation — forbid extra headers
# ────────────────────────────────────────────────
class StrictHeaders(BaseModel):
    model_config = {"extra": "forbid"}
    host: str
    save_data: bool


@router.api_route(
    "/strict",
    methods=["GET"],
    description="Rejects unknown headers (extra='forbid')."
)
async def read_strict_headers(headers: Annotated[StrictHeaders, Header()]):
    return {"validated_headers": headers.model_dump()}


# ────────────────────────────────────────────────
# Disable underscore→hyphen conversion
# ────────────────────────────────────────────────
@router.api_route(
    "/raw",
    methods=["GET"],
    description="Disables underscore-to-hyphen conversion for header names."
)
async def read_raw_headers(
        headers: Annotated[CommonHeaders, Header(convert_underscores=False)]
):
    return {"raw_headers": headers.model_dump()}
