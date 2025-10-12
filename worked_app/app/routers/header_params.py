from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter(prefix="/headers", tags=["Header Parameters"])


# ────────────────────────────────────────────────
# Basic header extraction (User-Agent)
# ────────────────────────────────────────────────
@router.api_route(
    "/user-agent",
    methods=["GET"],
    description="Reads the User-Agent header (automatically converts underscore → hyphen).",
)
async def get_user_agent(user_agent: Annotated[str | None, Header()] = None):
    return {"user_agent": user_agent}


# ────────────────────────────────────────────────
# Custom header (e.g., API key)
# ────────────────────────────────────────────────
@router.api_route(
    "/secure",
    methods=["GET"],
    description="Simulates checking an API key header.",
)
async def get_secure_data(
        x_api_key: Annotated[str | None, Header(description="Custom API key header")] = None
):
    if x_api_key != "secret123":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
    return {"data": "You have access!", "x_api_key": x_api_key}


# ────────────────────────────────────────────────
# Multiple headers (list)
# ────────────────────────────────────────────────
@router.api_route(
    "/tokens",
    methods=["GET"],
    description="Demonstrates multiple headers with the same name.",
)
async def read_tokens(x_token: Annotated[list[str] | None, Header()] = None):
    return {"received_tokens": x_token}


# ────────────────────────────────────────────────
# Disable underscore conversion (uncommon)
# ────────────────────────────────────────────────
@router.api_route(
    "/raw-header",
    methods=["GET"],
    description="Demonstrates disabling underscore-to-hyphen conversion.",
)
async def read_raw_header(
        custom_header_test: Annotated[str | None, Header(convert_underscores=False)] = None
):
    return {"custom_header_test": custom_header_test}
