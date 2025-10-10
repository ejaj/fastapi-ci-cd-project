from typing import Annotated
from fastapi import APIRouter, Path, Query

router = APIRouter(prefix="/path-demo", tags=["Path & Numeric Validation Demo"])

# Example dataset
ITEMS = [
    {"id": 1, "name": "Apple iPad"},
    {"id": 2, "name": "Banana Phone"},
    {"id": 3, "name": "Cherry Keyboard"},
    {"id": 10, "name": "Dell Monitor"},
]


# Basic example — path + query parameter
@router.get("/items/{item_id}")
def read_item(
        item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],  # path param
        q: Annotated[str | None, Query(alias="item-query", max_length=20)] = None,  # query param
):
    """Example: /path-demo/items/2?item-query=phone"""
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


# Numeric validation for integers (gt, le)
@router.get("/int/{item_id}")
def read_int_item(
        item_id: Annotated[int, Path(gt=0, le=1000, title="Item ID between 1 and 1000")],
):
    """Example: /path-demo/int/50"""
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    return {"found": item is not None, "item": item}


# Numeric validation for floats (gt, lt)
@router.get("/float/{value}")
def read_float_item(
        *,
        value: Annotated[float, Path(gt=0.0, lt=10.5, title="Float between 0 and 10.5")],
        size: Annotated[float, Query(gt=0, lt=5.0, description="Size must be >0 and <5")] = 1.0,
):
    """Example: /path-demo/float/5.5?size=2"""
    return {"value": value, "size": size, "message": "Both values are within valid ranges!"}


# Multiple parameter validation with both Path and Query
@router.get("/combine/{item_id}")
def combine_example(
        item_id: Annotated[int, Path(ge=1, le=100)],
        qty: Annotated[int, Query(gt=0, le=50, description="Quantity to order")] = 1,
):
    """Example: /path-demo/combine/3?qty=5"""
    item = next((i for i in ITEMS if i["id"] == item_id), None)
    if not item:
        return {"error": "Item not found"}
    return {
        "item": item,
        "quantity": qty,
        "total_id_x_qty": item["id"] * qty,
    }
