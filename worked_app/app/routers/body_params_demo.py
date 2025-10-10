from typing import Annotated
from fastapi import APIRouter, Body, Path, Query
from pydantic import BaseModel

# Create a router instead of a whole app
router = APIRouter(prefix="/items", tags=["Body Parameters Demo"])


# ─────────────────────────────
# Models
# ─────────────────────────────
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class User(BaseModel):
    username: str
    full_name: str | None = None


# ─────────────────────────────
# Mix Path + optional Body + optional Query
# ─────────────────────────────
@router.put("/{item_id}", summary="Optional body + query")
async def update_item_optional_body(
        item_id: Annotated[int, Path(ge=0, le=1000, description="Item ID")],
        q: str | None = Query(default=None, description="Optional search flag"),
        item: Item | None = None,
):
    result = {"item_id": item_id}
    if q:
        result["q"] = q
    if item:
        result["item"] = item
    return result


# ─────────────────────────────
# Multiple body models (Item + User)
# ─────────────────────────────
@router.put("/{item_id}/assign", summary="Two body models: item + user")
async def update_item_with_user(
        item_id: int,
        item: Item,
        user: User,
):
    return {"item_id": item_id, "item": item, "user": user}


# ─────────────────────────────
# Add a singular value into the body using Body()
# ─────────────────────────────
@router.put("/{item_id}/importance", summary="Body scalar with Body()")
async def set_item_importance(
        item_id: int,
        item: Item,
        importance: Annotated[int, Body(gt=0, description="1..N")],
):
    return {"item_id": item_id, "item": item, "importance": importance}


# ─────────────────────────────
# Multiple body params + query param
# ─────────────────────────────
@router.put("/{item_id}/full", summary="Body (item+user+scalar) + query")
async def update_item_full(
        *,
        item_id: int,
        item: Item,
        user: User,
        importance: Annotated[int, Body(gt=0)],
        q: str | None = None,
):
    result = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        result["q"] = q
    return result


# ─────────────────────────────
# Embed a single model under a key
# ─────────────────────────────
@router.put("/{item_id}/embed", summary="Embed single model in body")
async def update_item_embedded(
        item_id: int,
        item: Annotated[Item, Body(embed=True)],
):
    return {"item_id": item_id, "item": item}
