from typing import Annotated, Optional
from fastapi import (
    FastAPI, APIRouter, Depends, Header, HTTPException
)


# ---------------- Global dependencies ----------------

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key  # Return value is ignored when used as a decorator/global dep


# Apply to the whole app: every endpoint must include both headers
app = FastAPI(
    title="Global Dependencies demo",
    dependencies=[Depends(verify_token), Depends(verify_key)]
)

# ---------------- Routers ----------------

router = APIRouter(prefix="/api", tags=["main"])


@router.api_route("/items", methods=["GET"])
async def list_items():
    # Global dependencies already validated the headers
    return [{"item": "Portal Gun"}, {"item": "Plumbus"}]


@router.api_route("/users", methods=["GET"])
async def list_users():
    return [{"username": "Rick"}, {"username": "Morty"}]


# Per-route extra dependency (still runs after global ones)
async def audit_marker(x_audit: Annotated[Optional[str], Header()] = None):
    # Could log/trace here; return value is ignored
    return x_audit or "no-audit"


@router.api_route(
    "/secure-with-audit",
    methods=["GET"],
    dependencies=[Depends(audit_marker)]
)
async def secure_with_audit():
    return {"status": "ok", "note": "global + audit dependency executed"}


# Per-router dependency layered on top of global ones
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(audit_marker)]  # runs for every /admin/* route
)


@admin_router.api_route("/stats", methods=["GET"])
async def admin_stats():
    return {"uptime": "42h", "requests_last_minute": 123}
