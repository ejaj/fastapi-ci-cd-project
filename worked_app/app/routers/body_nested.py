from typing import Annotated

from fastapi import Body, status
from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl, Field

router = APIRouter(prefix="/body-nested", tags=["Body - Nested Models"])


# ─────────────────────────────────────────────────────────────
# Models (nested, lists, sets)
# ─────────────────────────────────────────────────────────────

class Image(BaseModel):
    url: HttpUrl
    name: str = Field(..., max_length=100)


class Item(BaseModel):
    name: str = Field(..., max_length=50)
    description: str | None = Field(default=None, max_length=300)
    price: float = Field(..., gt=0)
    tax: float | None = Field(default=None, ge=0)
    tags: set[str] = set()                      # 👈 uniqueness enforced
    images: list[Image] | None = None           # 👈 list of submodels


class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(..., gt=0)
    items: list[Item]                           # 👈 nested list of models


# ─────────────────────────────────────────────────────────────
# Routes using @router.api_route
# ─────────────────────────────────────────────────────────────

@router.api_route(
    path="/items/{item_id}",
    methods=["PUT"],
    status_code=status.HTTP_200_OK,
    description="Replace an item; demonstrates nested fields (sets, list[Image])."
)
async def put_item(
    item_id: int,
    item: Annotated[Item, Body(embed=True, description="Payload under 'item'")],
):
    # In a real app you’d persist `item` for `item_id` here
    return {"item_id": item_id, "item": item}


@router.api_route(
    path="/offers",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    description="Create an Offer containing a list of Items (each with nested Images)."
)
async def create_offer(
    offer: Annotated[Offer, Body(embed=True, description="Payload under 'offer'")],
):
    return {"offer": offer}


@router.api_route(
    path="/images/multiple",
    methods=["POST"],
    description="Top-level list body: list[Image]."
)
async def create_multiple_images(
    images: Annotated[list[Image], Body(embed=True, description="List under 'images'")],
):
    return {"count": len(images), "images": images}


@router.api_route(
    path="/index-weights",
    methods=["POST"],
    description="Dict body with typed keys/values: dict[int, float]."
)
async def create_index_weights(
    weights: Annotated[dict[int, float], Body(embed=True, description="Dict under 'weights'")],
):
    # JSON keys arrive as strings; Pydantic converts to int when possible.
    return {"weights": weights}
