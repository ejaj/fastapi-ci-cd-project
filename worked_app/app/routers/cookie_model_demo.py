from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Cookie
from pydantic import BaseModel

router = APIRouter(prefix="/cookies", tags=["Cookie Models"])


# ────────────────────────────────────────────────
# Define a Pydantic cookie model
# ────────────────────────────────────────────────
class TrackingCookies(BaseModel):
    session_id: str
    facebook_tracker: str | None = None
    google_tracker: str | None = None


# ────────────────────────────────────────────────
# Basic usage: read cookies into a model
# ────────────────────────────────────────────────
@router.api_route(
    "/read",
    methods=["GET"],
    description="Reads all tracking cookies into a Pydantic model",
)
async def read_cookies(cookies: Annotated[TrackingCookies, Cookie()]):
    return {"cookies_received": cookies.model_dump()}


# ────────────────────────────────────────────────
# Strict mode: reject unknown cookies
# ────────────────────────────────────────────────
class StrictCookies(BaseModel):
    model_config = {"extra": "forbid"}
    session_id: str
    analytics_tracker: str | None = None


@router.api_route(
    "/strict",
    methods=["GET"],
    description="Rejects any cookies not defined in the model (extra='forbid')",
)
async def strict_cookie_check(cookies: Annotated[StrictCookies, Cookie()]):
    return {"validated_cookies": cookies.model_dump()}
