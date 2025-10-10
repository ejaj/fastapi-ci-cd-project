from typing import Annotated, Literal
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/items", tags=["items"])

# Fake data
ITEMS = [
    {"id": 1, "name": "Laptop", "price": 1200, "tags": ["tech", "electronics"], "created_at": "2024-11-01"},
    {"id": 2, "name": "Coffee Mug", "price": 15, "tags": ["kitchen", "gift"], "created_at": "2024-09-12"},
    {"id": 3, "name": "Headphones", "price": 250, "tags": ["tech", "music"], "created_at": "2024-10-22"},
    {"id": 4, "name": "Notebook", "price": 8, "tags": ["stationery"], "created_at": "2024-08-01"},
    {"id": 5, "name": "Smartphone", "price": 950, "tags": ["tech", "mobile"], "created_at": "2024-10-02"},
]


# Base reusable query model (lenient by default: extra params ignored)
class FilterParams(BaseModel):
    limit: int = Field(10, gt=0, le=100, description="Max items to return")
    offset: int = Field(0, ge=0, description="Items to skip")
    order_by: Literal["price", "name", "created_at"] = "name"
    order: Literal["asc", "desc"] = "asc"
    tags: list[str] = Field(default=[], description="Repeat param: ?tags=tech&tags=gift")


# Strict variant: forbid any extra/unknown query params
class StrictFilterParams(FilterParams):
    model_config = {"extra": "forbid"}


def apply_filters(data: list[dict], f: FilterParams) -> list[dict]:
    # Filter by tags
    if f.tags:
        data = [d for d in data if any(tag in d["tags"] for tag in f.tags)]
    # Sort
    reverse = (f.order == "desc")
    try:
        data = sorted(data, key=lambda x: x[f.order_by], reverse=reverse)
    except KeyError:
        raise HTTPException(400, f"Invalid sort field: {f.order_by}")
    return data


@router.get("/", summary="Lenient: extra query params are ignored")
async def list_items(filters: Annotated[FilterParams, Query()]):
    data = apply_filters(ITEMS, filters)
    start, end = filters.offset, filters.offset + filters.limit
    return {
        "count": len(data),
        "limit": filters.limit,
        "offset": filters.offset,
        "items": data[start:end],
    }


@router.get("/strict", summary="Strict: extra query params are forbidden")
async def list_items_strict(filters: Annotated[StrictFilterParams, Query()]):
    data = apply_filters(ITEMS, filters)
    start, end = filters.offset, filters.offset + filters.limit
    return {
        "count": len(data),
        "limit": filters.limit,
        "offset": filters.offset,
        "items": data[start:end],
    }
