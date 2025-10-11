# app/routers/body_examples.py
from typing import Annotated
from fastapi import APIRouter, Body, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/body-request-example", tags=["Body - Declare Request Example Data"])


# ─────────────────────────────────────────────────────────────
# 1) MODEL-LEVEL EXAMPLES via model_config
# ─────────────────────────────────────────────────────────────
class ItemModelConfigured(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

    # Pydantic v2: add JSON Schema extras (including "examples")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                }
            ]
        }
    }


@router.api_route(
    path="/items/{item_id}",
    methods=["PUT"],
    status_code=status.HTTP_200_OK,
    description="Uses model-level examples via model_config.json_schema_extra",
)
async def put_item_model_configured(
        item_id: int,
        item: Annotated[
            ItemModelConfigured,
            Body(embed=True, description="Payload under 'item'"),
        ],
):
    return {"item_id": item_id, "item": item}


# ─────────────────────────────────────────────────────────────
# 2) FIELD-LEVEL EXAMPLES via Field(examples=[...])
# ─────────────────────────────────────────────────────────────
class ItemFieldExamples(BaseModel):
    name: str = Field(..., examples=["Foo"])
    description: str | None = Field(default=None, examples=["A very nice Item"])
    price: float = Field(..., examples=[35.4])
    tax: float | None = Field(default=None, examples=[3.2])


@router.api_route(
    path="/items/field-examples/{item_id}",
    methods=["PUT"],
    description="Uses Field(examples=[...]) on each attribute",
)
async def put_item_field_examples(
        item_id: int,
        item: Annotated[ItemFieldExamples, Body(embed=True, description="Payload under 'item'")],
):
    return {"item_id": item_id, "item": item}


# ─────────────────────────────────────────────────────────────
# 3) BODY-LEVEL EXAMPLES via Body(examples=[...])
# ─────────────────────────────────────────────────────────────
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


@router.api_route(
    path="/items/body-examples/{item_id}",
    methods=["PUT"],
    description="Uses Body(examples=[...]) to attach example payload(s) at the parameter level",
)
async def put_item_body_examples(
        item_id: int,
        item: Annotated[
            Item,
            Body(
                embed=True,
                description="Payload under 'item'",
                examples=[
                    {
                        "name": "Foo",
                        "description": "A very nice Item",
                        "price": 35.4,
                        "tax": 3.2,
                    }
                ],
            ),
        ],
):
    return {"item_id": item_id, "item": item}


# ─────────────────────────────────────────────────────────────
# 4) MULTIPLE LABELED EXAMPLES via Body(openapi_examples={...})
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/items/openapi-examples/{item_id}",
    methods=["PUT"],
    description="Uses Body(openapi_examples={...}) to show multiple labeled examples in Swagger",
)
async def put_item_openapi_examples(
        item_id: int,
        item: Annotated[
            Item,
            Body(
                embed=True,
                description="Payload under 'item'",
                openapi_examples={
                    "normal": {
                        "summary": "A normal example",
                        "description": "A **valid** item works correctly.",
                        "value": {
                            "name": "Foo",
                            "description": "A very nice Item",
                            "price": 35.4,
                            "tax": 3.2,
                        },
                    },
                    "converted": {
                        "summary": "String-to-float conversion",
                        "description": "FastAPI/Pydantic can convert numeric strings to numbers.",
                        "value": {"name": "Bar", "price": "35.4"},
                    },
                    "invalid": {
                        "summary": "Invalid data is rejected",
                        "description": "This fails validation because price is not a number.",
                        "value": {"name": "Baz", "price": "thirty five point four"},
                    },
                },
            ),
        ],
):
    return {"item_id": item_id, "item": item}
