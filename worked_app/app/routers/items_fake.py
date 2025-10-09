# routers/items.py
from enum import Enum
from typing import Literal, Optional, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/items", tags=["items"])


# ── types/models ─────────────────────────────────────────────
class Category(str, Enum):
    general = "general"
    tech = "tech"
    books = "books"
    apparel = "apparel"


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(None, max_length=200)
    price: float = Field(..., gt=0)
    tax: float | None = Field(None, ge=0)
    category: Category = Category.general
    status: Literal["active", "inactive"] = "active"


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    tax: Optional[float] = Field(None, ge=0)
    category: Optional[Category] = None
    status: Optional[Literal["active", "inactive"]] = None


class ItemOut(BaseModel):
    id: str
    name: str
    description: str | None
    price: float
    tax: float | None
    price_with_tax: float | None
    category: Category
    status: Literal["active", "inactive"]


# simple in-memory store for demo
DB: dict[str, ItemOut] = {}


def _with_tax(price: float, tax: float | None) -> float | None:
    return None if tax is None else round(price + tax, 2)


# ── routes ───────────────────────────────────────────────────

# Create
@router.post("/", response_model=ItemOut, status_code=201)
async def create_item(item: ItemCreate):
    new_id = uuid4().hex
    saved = ItemOut(
        id=new_id,
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax,
        price_with_tax=_with_tax(item.price, item.tax),
        category=item.category,
        status=item.status,
    )
    DB[new_id] = saved
    return saved


# Read (list)
@router.get("/", response_model=List[ItemOut])
async def list_items():
    return list(DB.values())


# Read (one)
@router.get("/{item_id}", response_model=ItemOut)
async def get_item(item_id: str):
    item = DB.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


# Replace (PUT)
@router.put("/{item_id}", response_model=ItemOut)
async def replace_item(
        item_id: str,
        item: ItemCreate,
        q: str | None = Query(default=None, description="Optional flag"),
):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = ItemOut(
        id=item_id,
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax,
        price_with_tax=_with_tax(item.price, item.tax),
        category=item.category,
        status=item.status,
    )
    DB[item_id] = updated
    return updated


# Partial update (PATCH)
@router.patch("/{item_id}", response_model=ItemOut)
async def patch_item(item_id: str, patch: ItemUpdate):
    curr = DB.get(item_id)
    if not curr:
        raise HTTPException(status_code=404, detail="Item not found")

    new_price = patch.price if patch.price is not None else curr.price
    new_tax = patch.tax if patch.tax is not None else curr.tax
    updated = ItemOut(
        id=curr.id,
        name=patch.name or curr.name,
        description=patch.description if patch.description is not None else curr.description,
        price=new_price,
        tax=new_tax,
        price_with_tax=_with_tax(new_price, new_tax),
        category=patch.category or curr.category,
        status=patch.status or curr.status,
    )
    DB[item_id] = updated
    return updated


# Delete
@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: str):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")
    del DB[item_id]
    return None
