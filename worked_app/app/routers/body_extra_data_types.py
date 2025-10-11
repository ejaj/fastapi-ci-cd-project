from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/extra-types", tags=["Body - Extra Data Types"])


# ─────────────────────────────────────────────────────────────
# Models (only where it improves clarity)
# ─────────────────────────────────────────────────────────────
class Money(BaseModel):
    amount: Decimal = Field(..., description="Exact decimal (useful for currency)", examples=["19.99"])
    currency: str = Field(..., min_length=3, max_length=3, examples=["USD"])


class Tags(BaseModel):
    # frozenset enforces uniqueness; shows as list in schema/JSON
    tags: frozenset[str] = Field(default_factory=frozenset, examples=[["alpha", "beta", "alpha"]])


class Blob(BaseModel):
    # bytes are shown as base64-encoded strings in OpenAPI/Swagger
    data: bytes = Field(..., description="Raw bytes (base64 in JSON)", examples=["aGVsbG8="])


# ─────────────────────────────────────────────────────────────
# UUID + datetime/time/timedelta/date in a single request
#    Multiple Body(...) params are allowed; payload is one JSON object
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/schedule/{item_id}",
    methods=["PUT"],
    status_code=status.HTTP_200_OK,
    description=(
            "Demonstrates UUID (path) + datetime/time/timedelta/date in body. "
            "FastAPI/Pydantic parse & validate ISO 8601 strings and seconds for timedelta."
    ),
)
async def schedule_item(
        item_id: UUID,
        start_datetime: Annotated[
            datetime,
            Body(
                description="ISO 8601 datetime",
                examples=["2025-10-11T12:00:00"],
            ),
        ],
        end_datetime: Annotated[
            datetime,
            Body(
                description="ISO 8601 datetime (must be ≥ start)",
                examples=["2025-10-11T18:00:00"],
            ),
        ],
        process_after: Annotated[
            timedelta,
            Body(
                description="Delay before processing (seconds or ISO 8601 duration).",
                examples=[3600],
            ),
        ],
        repeat_at: Annotated[
            time | None,
            Body(description="Optional time-of-day for repeat (ISO 8601 time).", examples=["14:30:00"]),
        ] = None,
        event_date: Annotated[
            date,
            Body(description="ISO 8601 date", examples=["2025-10-11"]),
        ] = date.today(),
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,  # UUID → str in JSON
        "start_datetime": start_datetime,  # datetime → ISO 8601
        "end_datetime": end_datetime,
        "process_after": process_after,  # timedelta → seconds (float)
        "repeat_at": repeat_at,  # time → "HH:MM:SS[.fff]"
        "event_date": event_date,  # date → "YYYY-MM-DD"
        "start_process": start_process,
        "duration": duration.total_seconds(),  # make duration explicit in seconds
    }


# ─────────────────────────────────────────────────────────────
# Decimal for money (exact math) via a model
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/money/charge",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    description="Uses Decimal for exact currency; avoids float rounding errors.",
)
async def charge_money(
        payment: Annotated[
            Money,
            Body(
                embed=True,
                description="Payload under 'payment'",
                openapi_examples={
                    "exact": {
                        "summary": "Exact decimal",
                        "value": {"amount": "19.99", "currency": "USD"},
                    },
                    "integer": {
                        "summary": "Integer is fine too",
                        "value": {"amount": 25, "currency": "EUR"},
                    },
                },
            ),
        ]
):
    # Return amount as string to preserve exact representation in JSON
    return {
        "charged": True,
        "amount": str(payment.amount),
        "currency": payment.currency,
    }


# ─────────────────────────────────────────────────────────────
# frozenset for unique tags (duplicates removed)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/tags/ingest",
    methods=["POST"],
    description="frozenset[str] ensures tags are unique; duplicates are removed.",
)
async def ingest_tags(
        payload: Annotated[
            Tags,
            Body(
                embed=True,
                description="Payload under 'payload'",
                examples=[{"tags": ["alpha", "beta", "alpha", "gamma"]}],
            ),
        ]
):
    unique_sorted = sorted(payload.tags)
    return {"count": len(payload.tags), "unique_tags": unique_sorted}


# ─────────────────────────────────────────────────────────────
# bytes as base64 (Swagger shows 'binary' format)
# ─────────────────────────────────────────────────────────────
@router.api_route(
    path="/blob",
    methods=["POST"],
    description="Accepts raw bytes (base64 in JSON) and echoes size.",
)
async def upload_blob(
        blob: Annotated[
            Blob,
            Body(
                embed=True,
                description="Payload under 'blob' with base64 'data'",
            ),
        ]
):
    return {"size_bytes": len(blob.data)}
