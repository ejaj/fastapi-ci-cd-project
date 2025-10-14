from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

router = APIRouter(prefix="/items", tags=["JSON Encoder Demo"])

# ---- Fake JSON-only DB (accepts only JSON-compatible types) ----
fake_db: dict[str, dict[str, Any]] = {}


# ---- Models ----
class Item(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    timestamp: datetime
    price: Decimal
    tags: set[str] = set()
    description: str | None = None


# ---- Helpers ----
def encode_for_db(obj: Any) -> dict[str, Any]:
    """
    Convert complex Python/Pydantic types to JSON-compatible dicts/lists using
    FastAPI's jsonable_encoder.

    - datetime -> ISO string
    - UUID -> string
    - Decimal -> float (custom)
    - set -> list
    """
    return jsonable_encoder(
        obj,
        custom_encoder={
            Decimal: float,  # or str if you prefer exactness: Decimal: str
        },
        exclude_none=True,  # drop None fields to keep payload slim
        by_alias=True,
    )


# ---- Routes ----

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an item (converted for a JSON-only DB)",
    response_description="The item as stored (JSON-compatible)",
)
async def create_item(item: Item):
    data = encode_for_db(item)
    fake_db[str(item.id)] = data
    return data


@router.put(
    "/{item_id}",
    summary="Upsert an item by ID (uses jsonable_encoder)",
    response_description="The upserted item (JSON-compatible)",
)
async def upsert_item(item_id: UUID, item: Item):
    # Force payload ID to match path ID (typical upsert pattern)
    item = item.copy(update={"id": item_id})
    data = encode_for_db(item)
    fake_db[str(item_id)] = data
    return data


@router.get(
    "/{item_id}",
    summary="Fetch raw JSON stored data",
    response_description="JSON-compatible dict as stored in the fake DB",
)
async def get_item(item_id: UUID):
    key = str(item_id)
    if key not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_db[key]


@router.get(
    "",
    summary="List all items (JSON-compatible)",
    response_description="Array of JSON-compatible dicts",
)
async def list_items():
    return list(fake_db.values())


# Example: partially update only some fields, then encode/merge
class ItemPatch(BaseModel):
    title: str | None = None
    price: Decimal | None = None
    tags: set[str] | None = None
    description: str | None = None


@router.patch(
    "/{item_id}",
    summary="Patch item fields, re-encode for JSON-only DB",
    response_description="Patched item (JSON-compatible)",
)
async def patch_item(item_id: UUID, patch: ItemPatch):
    key = str(item_id)
    if key not in fake_db:
        raise HTTPException(status_code=404, detail="Item not found")

    # Reconstruct a Pydantic model to validate, then re-encode
    current = fake_db[key]
    # Convert stored JSON back to model-friendly kwargs
    # (timestamp is already ISO string; Pydantic will parse it)
    candidate = Item(
        id=item_id,
        title=patch.title if patch.title is not None else current["title"],
        timestamp=current["timestamp"],
        price=patch.price if patch.price is not None else Decimal(str(current["price"])),
        tags=set(patch.tags) if patch.tags is not None else set(current.get("tags", [])),
        description=patch.description if patch.description is not None else current.get("description"),
    )

    updated = encode_for_db(candidate)
    fake_db[key] = updated
    return updated
