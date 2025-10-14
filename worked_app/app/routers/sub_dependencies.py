from typing import Annotated, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    FastAPI,
    Response,
    Body,
)

router = APIRouter(prefix="", tags=["demo"])


# ---------- Sub-dependencies: query -> (query or cookie) ----------

def query_extractor(q: Optional[str] = None) -> Optional[str]:
    # First-level dependency: just returns the ?q=... value if present
    return q


def query_or_cookie_extractor(
        q: Annotated[Optional[str], Depends(query_extractor)],
        last_query: Annotated[Optional[str], Cookie()] = None,
) -> Optional[str]:
    # Second-level dependency: fall back to cookie if no query
    return q or last_query


@router.api_route("/items/", methods=["GET"])
async def read_items(
        q_or_default: Annotated[Optional[str], Depends(query_or_cookie_extractor)],
):
    """
    Try: /items/?q=hello  -> returns 'hello'
    Or set cookie first (see /remember), then call /items/ with no ?q to get cookie value.
    """
    return {"q_or_cookie": q_or_default}


@router.api_route("/remember", methods=["POST"])
async def remember_last_query(
        response: Response,
        payload: Annotated[dict, Body(embed=True)]  # expects {"q": "..."}
):
    """
    POST {"q": "saved"} to set the 'last_query' cookie, then call GET /items/ with no ?q.
    """
    q = payload.get("q")
    if q is None:
        return {"detail": "Send body like: {\"q\": \"something\"}"}
    response.set_cookie(key="last_query", value=q, httponly=True)
    return {"detail": "Cookie 'last_query' set", "q": q}


# ---------- Dependency cache demo: Depends(..., use_cache=False) ----------

def get_value() -> str:
    # Returns a new unique value each call
    return str(uuid4())


def cached_value(
        val: Annotated[str, Depends(get_value)]
) -> str:
    # Uses the default dependency cache (same value if reused in the same request)
    return val


def fresh_value(
        val: Annotated[str, Depends(get_value, use_cache=False)]
) -> str:
    # Bypasses the dependency cache (forces a new call each time)
    return val


@router.api_route("/cache-demo", methods=["GET"])
async def cache_demo(
        # cached_value is the same dependency used twice -> should be identical within one request
        cached1: Annotated[str, Depends(cached_value)],
        cached2: Annotated[str, Depends(cached_value)],
        # fresh_value bypasses cache -> each one should differ
        fresh1: Annotated[str, Depends(fresh_value)],
        fresh2: Annotated[str, Depends(fresh_value)],
):
    return {
        "cached_1": cached1,
        "cached_2": cached2,
        "fresh_1": fresh1,
        "fresh_2": fresh2,
        "cached_equal": cached1 == cached2,
        "fresh_equal": fresh1 == fresh2,
    }
