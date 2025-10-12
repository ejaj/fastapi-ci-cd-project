from __future__ import annotations

from typing import Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/response-models", tags=["Response Model - Return Type"])


# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []


class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(BaseUser):
    password: str = Field(..., min_length=6)


class UserOut(BaseUser):
    pass  # no password here


# Fake store
ITEMS = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}


# ─────────────────────────────────────────────────────────────
# 1) response_model filters out sensitive fields (password)
#    We return a UserIn, but docs/output are UserOut (no password).
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/users",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    response_model=UserOut,
    description="Create user: response_model filters out the password.",
)
async def create_user(user: UserIn) -> Any:
    # imagine hashing password & storing user here
    return user  # response will exclude password due to response_model=UserOut


# ─────────────────────────────────────────────────────────────
# 2) Inheritance trick: annotate return as BaseUser, return UserIn
#    Type checkers are happy; FastAPI still filters to BaseUser fields.
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/users/inheritance",
    methods=["POST"],
    description="Return BaseUser type while returning a UserIn instance (password filtered).",
)
async def create_user_inheritance(user: UserIn) -> BaseUser:
    return user  # output is filtered to BaseUser fields


# ─────────────────────────────────────────────────────────────
# 3) Return type annotations for lists
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/items",
    methods=["GET"],
    description="Return a list of Items (validated & documented).",
)
async def list_items() -> list[Item]:
    return [Item(**d) for d in ITEMS.values()]


# ─────────────────────────────────────────────────────────────
# 4) Exclude unset defaults to shorten payloads
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/items/{item_id}",
    methods=["GET"],
    response_model=Item,
    response_model_exclude_unset=True,
    description="Only include fields that were actually set (exclude_unset).",
)
async def read_item(item_id: str):
    return ITEMS[item_id]


# ─────────────────────────────────────────────────────────────
# 5) Quick include/exclude field filtering
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/items/{item_id}/public",
    methods=["GET"],
    response_model=Item,
    response_model_exclude={"tax"},
    description="Exclude 'tax' field from the response.",
)
async def read_item_public(item_id: str):
    return ITEMS[item_id]


@router.api_route(
    "/items/{item_id}/name",
    methods=["GET"],
    response_model=Item,
    response_model_include={"name", "description"},
    description="Only include 'name' and 'description'.",
)
async def read_item_name_desc(item_id: str):
    return ITEMS[item_id]


# ─────────────────────────────────────────────────────────────
# 6) Return a Response directly (skip model processing)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    "/portal",
    methods=["GET"],
    response_model=None,
    description="Demonstrates returning Response/RedirectResponse directly.",
)
async def portal(teleport: bool = False) -> Response | dict:
    if teleport:
        return RedirectResponse(url="https://example.org/teleport")
    return JSONResponse(content={"message": "Here's your interdimensional portal."})
