from typing import Annotated
from fastapi import Body, HTTPException
from fastapi import status
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

# ---------------------------
# Router with @api_route (aka “@route” style)
# ---------------------------
router = APIRouter(prefix="/body_fields", tags=["Body Fields"])


# ---------------------------
# Pydantic models using Field
# ---------------------------

class Item(BaseModel):
    name: str = Field(
        ...,
        title="Item Name",
        description="Human-friendly item name",
        min_length=1,
        max_length=50,
    )
    description: str | None = Field(
        default=None,
        title="Description",
        description="Optional description, up to 300 characters",
        max_length=300,
    )
    price: float = Field(
        ...,
        gt=0,
        description="Must be greater than 0",
    )
    tax: float | None = Field(
        default=None,
        ge=0,
        description="Optional tax, must be >= 0 if provided",
    )
    in_stock: bool = Field(
        default=True,
        description="Whether the item is currently in stock",
    )


class ItemUpdate(BaseModel):
    # Demonstrate optional fields with constraints
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="New name (optional). If provided, length 1–50.",
    )
    description: str | None = Field(
        default=None, max_length=300, description="New description (optional)."
    )
    price: float | None = Field(
        default=None,
        gt=0,
        description="New price (optional). If provided, must be > 0.",
    )
    tax: float | None = Field(
        default=None, ge=0, description="New tax (optional). If provided, >= 0."
    )
    in_stock: bool | None = Field(
        default=None, description="New stock flag (optional)."
    )


# ---------------------------
# Fake in-memory "DB"
# ---------------------------
DB: dict[int, Item] = {}


@router.api_route("", methods=["POST"], status_code=status.HTTP_201_CREATED)
async def create_item(
        # Body(embed=True) nests payload under {"item": {...}}
        item: Annotated[Item, Body(embed=True, description="Item payload wrapped under 'item'")]
):
    new_id = (max(DB.keys()) + 1) if DB else 1
    DB[new_id] = item
    return {"id": new_id, "item": item}


@router.api_route("/{item_id}", methods=["GET"])
async def get_item(item_id: int):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, "item": DB[item_id]}


@router.api_route("/{item_id}", methods=["PUT"])
async def replace_item(
        item_id: int,
        # Demonstrate Body(embed=True) with Annotated on PUT as well
        item: Annotated[Item, Body(embed=True, description="Full replacement Item payload")],
):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")
    DB[item_id] = item
    return {"id": item_id, "item": item}


@router.api_route("/{item_id}", methods=["PATCH"])
async def update_item_partial(
        item_id: int,
        patch: Annotated[
            ItemUpdate,
            Body(embed=True, description="Partial update payload under 'patch'")
        ],
):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")

    current = DB[item_id].model_copy()  # pydantic v2: safe copy

    # Apply only provided fields
    updates = patch.model_dump(exclude_unset=True)
    # Respect validation by reloading through the model
    merged = current.model_dump()
    merged.update({k: v for k, v in updates.items() if v is not None})
    DB[item_id] = Item(**merged)

    return {"id": item_id, "item": DB[item_id]}


@router.api_route("/{item_id}", methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    if item_id not in DB:
        raise HTTPException(status_code=404, detail="Item not found")
    DB.pop(item_id)
    return None
