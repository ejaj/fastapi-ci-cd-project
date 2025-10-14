from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

router = APIRouter(prefix="/items", tags=["Body Updates"])


# -------------------------
# Models
# -------------------------
class Item(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    tax: float = 10.5
    tags: list[str] = []


# Optional separate model for PATCH (all fields optional).
# You could reuse Item, but having a distinct type can be clearer.
class ItemPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    tax: float | None = None
    tags: list[str] | None = None


# -------------------------
# Fake in-memory store
# -------------------------
items: dict[str, dict[str, Any]] = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}


# -------------------------
# Read
# -------------------------
@router.get("/{item_id}", response_model=Item, summary="Get one item")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]


@router.get("", summary="List items")
async def list_items():
    return items


# -------------------------
# PUT = Replace the entire resource
# -------------------------
@router.put("/{item_id}", response_model=Item, summary="Replace an item (PUT)")
async def replace_item(item_id: str, item: Item):
    """
    Replaces the stored item with the given payload.
    Missing fields get their **defaults**, not the old values.
    """
    # Make JSON-safe (e.g., datetime->str if present)
    update_item_encoded = jsonable_encoder(item)
    items[item_id] = update_item_encoded
    return update_item_encoded


# -------------------------
# PATCH = Partial update
# -------------------------
@router.patch("/{item_id}", response_model=Item, summary="Partially update an item (PATCH)")
async def patch_item(item_id: str, patch: ItemPatch):
    """
    Updates only the fields actually provided by the client.
    Uses Pydantic's exclude_unset to avoid overwriting with defaults.
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")

    # Build a Pydantic model from stored data for validation/merging
    stored_item_model = Item(**items[item_id])

    # Pydantic v2: model_dump(exclude_unset=True)
    # (If you're on v1, .dict(exclude_unset=True) still works.)
    update_data = patch.model_dump(exclude_unset=True)

    # Pydantic v2: model_copy(update=...)
    # (If you're on v1, use .copy(update=...) instead.)
    updated_item = stored_item_model.model_copy(update=update_data)

    # Encode to JSON-friendly structure (e.g., sets, datetimes, etc.)
    items[item_id] = jsonable_encoder(updated_item)
    return updated_item
