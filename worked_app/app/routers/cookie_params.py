from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Cookie, Response, status, HTTPException

router = APIRouter(prefix="/cookies", tags=["Cookie Parameters"])


# ─────────────────────────────────────────────────────────────
# Set a cookie (with secure flags)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/set",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    description="Set an example cookie with best-practice flags.",
)
async def set_cookie(response: Response):
    session_id = str(uuid4())
    # Key points:
    # - httponly=True: JS can't read it (mitigates XSS)
    # - secure=True: only over HTTPS
    # - samesite='lax' or 'strict' or 'none' (none requires secure)
    # - max_age vs expires: choose what your app needs
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60,  # 1 hour
        path="/",
    )
    return {"message": "cookie set", "session_id_preview": session_id[:8]}


# ─────────────────────────────────────────────────────────────
#  Read a cookie (optional)
#    If not present, returns None.
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/echo",
    methods=["GET"],
    description="Read an optional cookie: ads_id",
)
async def echo_ads_cookie(
        ads_id: Annotated[Optional[str], Cookie(description="Ad tracking cookie")] = None
):
    return {"ads_id": ads_id}


# ─────────────────────────────────────────────────────────────
# Require & validate a cookie (UUID format)
#    If missing/invalid, return 401/422.
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/me",
    methods=["GET"],
    description="Require a session_id cookie (UUID).",
)
async def read_me(
        session_id: Annotated[UUID | None, Cookie(description="Session cookie UUID")] = None
):
    if session_id is None:
        # Missing cookie → unauthorized
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing session cookie")
    # If present but not UUID, FastAPI/Pydantic will 422 before reaching here.
    return {"user": "current", "session_id": str(session_id)}


# ─────────────────────────────────────────────────────────────
# Overwrite/refresh a cookie (rotate)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/rotate",
    methods=["POST"],
    description="Rotate the session_id cookie (issue a new one).",
)
async def rotate_cookie(response: Response):
    new_id = str(uuid4())
    response.set_cookie(
        key="session_id",
        value=new_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60,
        path="/",
    )
    return {"message": "rotated", "session_id_preview": new_id[:8]}


# ─────────────────────────────────────────────────────────────
# Delete a cookie
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/clear",
    methods=["POST"],
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete the session_id cookie.",
)
async def clear_cookie(response: Response):
    response.delete_cookie(key="session_id", path="/")
    return None
