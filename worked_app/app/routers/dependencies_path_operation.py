from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException

router = APIRouter(prefix="/dependencies/path", tags=["demo"])


# ---- Dependencies ----

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key  # Return value is ignored when used via decorator dependencies


# A dependency that returns something (to show it's still executed when attached via decorator)
async def audit_marker(x_audit: Annotated[str | None, Header()] = None):
    # You could log/trace here. Returning a value—but it won't be injected into the handler.
    return x_audit or "no-audit"


# ---- Routes using decorator-level dependencies ----

@router.api_route(
    "/items",
    methods=["GET"],
    dependencies=[Depends(verify_token), Depends(verify_key)]
)
async def list_items():
    # No unused parameters in the signature; headers were validated already.
    return [{"item": "Foo"}, {"item": "Bar"}]


@router.api_route(
    "/secure-with-audit",
    methods=["GET"],
    dependencies=[Depends(verify_token), Depends(verify_key), Depends(audit_marker)]
)
async def secure_with_audit():
    # audit_marker ran, but we don't need its return value here.
    return {"status": "ok", "note": "headers validated and audit dependency executed"}


# ---- Router-level dependency (applies to all endpoints in this router) ----
# For illustration, we create a second router that requires the token on every route.

secure_router = APIRouter(
    prefix="/secure",
    tags=["secure"],
    dependencies=[Depends(verify_token)]  # runs for all paths below
)


@secure_router.api_route(
    "/profile",
    methods=["GET"],
    dependencies=[Depends(verify_key)]  # add extra per-route requirement
)
async def get_profile():
    return {"profile": "you", "secure": True}


@secure_router.api_route(
    "/settings",
    methods=["GET"]
)
async def get_settings():
    # Only verify_token runs here (from the router-level dependency).
    return {"settings": {"theme": "dark"}}
