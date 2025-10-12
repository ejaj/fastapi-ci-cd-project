from __future__ import annotations

from typing import Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/extra-models", tags=["Extra Models"])


# ─────────────────────────────────────────────────────────────
# User models: input (with password), output (no password),
# DB model (with hashed_password). Inheritance reduces duplication.
# ─────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: str = Field(..., min_length=6)


class UserOut(UserBase):
    pass  # no password here


class UserInDB(UserBase):
    hashed_password: str


# Fake "DB"
USERS_DB: dict[str, UserInDB] = {}


def fake_password_hasher(raw_password: str) -> str:
    return "supersecret" + raw_password


def fake_save_user(user_in: UserIn) -> UserInDB:
    hashed_password = fake_password_hasher(user_in.password)
    # dict unpacking from one model to another + add hashed_password
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    USERS_DB[user_in.username] = user_in_db
    return user_in_db


@router.api_route(
    "/users",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    response_model=UserOut,
    description="Create a user. Response filters out password/hashed_password."
)
async def create_user(user_in: UserIn):
    if user_in.username in USERS_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    saved = fake_save_user(user_in)
    return saved  # filtered by response_model=UserOut


@router.api_route(
    "/users/{username}",
    methods=["GET"],
    response_model=UserOut,
    description="Fetch user by username (safe public shape)."
)
async def get_user(username: str):
    user_db = USERS_DB.get(username)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found")
    return user_db  # hashed_password will be excluded by response_model


# ─────────────────────────────────────────────────────────────
# Union (anyOf) example: response could be one of multiple models.
# Order more specific → less specific when using Union.
# ─────────────────────────────────────────────────────────────
class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type: str = "car"


class PlaneItem(BaseItem):
    type: str = "plane"
    size: int


ITEMS = {
    "item1": {"description": "Low rider", "type": "car"},
    "item2": {"description": "It’s my aeroplane", "type": "plane", "size": 5},
}


@router.api_route(
    "/items/{item_id}",
    methods=["GET"],
    response_model=Union[PlaneItem, CarItem],
    description="Return either a PlaneItem or CarItem (documented as anyOf)."
)
async def read_item(item_id: str):
    data = ITEMS.get(item_id)
    if not data:
        raise HTTPException(status_code=404, detail="Item not found")
    return data


# ─────────────────────────────────────────────────────────────
# List of models: return a list[Model] and FastAPI validates each item.
# ─────────────────────────────────────────────────────────────
class SimpleItem(BaseModel):
    name: str
    description: str


SIMPLE_ITEMS = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It’s my aeroplane"},
]


@router.api_route(
    "/items",
    methods=["GET"],
    response_model=list[SimpleItem],
    description="Return a validated list of items."
)
async def list_items():
    return SIMPLE_ITEMS


# ─────────────────────────────────────────────────────────────
# Arbitrary dict response: use a typed dict when keys are dynamic.
# ─────────────────────────────────────────────────────────────
KEYWORD_WEIGHTS = {"foo": 2.3, "bar": 3.4, "baz": 1.1}


@router.api_route(
    "/keyword-weights",
    methods=["GET"],
    response_model=dict[str, float],
    description="Return a dynamic mapping without defining a Pydantic model."
)
async def read_keyword_weights():
    return KEYWORD_WEIGHTS
