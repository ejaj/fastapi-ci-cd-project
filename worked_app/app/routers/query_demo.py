from typing import Annotated, Literal
from fastapi import APIRouter, Query
from pydantic import AfterValidator

# Create a router for all query parameter examples
router = APIRouter(prefix="/query-demo", tags=["Query Demo"])

# ────────────────────────────────
# Example data (mock dataset)
# ────────────────────────────────
ITEMS = [
    {"id": 1, "name": "Apple iPad", "tags": ["tablet", "ios"]},
    {"id": 2, "name": "Banana Phone", "tags": ["phone", "fun"]},
    {"id": 3, "name": "Cherry Keyboard", "tags": ["keyboard", "pc"]},
]


# ────────────────────────────────
# Custom validator (used later)
# ────────────────────────────────
def ensure_known_id(v: str):
    """Validate ID must start with isbn- or imdb-"""
    if not v.startswith(("isbn-", "imdb-")):
        raise ValueError('id must start with "isbn-" or "imdb-"')
    return v


# ────────────────────────────────
# Basic query params with validation
# ────────────────────────────────
@router.get("/")
def list_items(
        q: Annotated[str | None, Query(min_length=3, max_length=50, description="Search term")] = None,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        size: Annotated[int, Query(ge=1, le=50, description="Items per page")] = 10,
        order: Annotated[Literal["asc", "desc"], Query()] = "asc",
):
    """Example: http://127.0.0.1:8000/query-demo?q=pad&page=1&order=desc"""
    data = ITEMS

    # Filter by search term
    if q:
        data = [it for it in data if q.lower() in it["name"].lower()]

    # Sort by name (asc/desc)
    if order == "desc":
        data = sorted(data, key=lambda x: x["name"].lower(), reverse=True)
    else:
        data = sorted(data, key=lambda x: x["name"].lower())

    # Simple pagination
    start = (page - 1) * size
    end = start + size

    return {"count": len(data), "items": data[start:end]}


# ────────────────────────────────
# List of query parameters
# ────────────────────────────────
@router.get("/tags")
def filter_by_tags(
        tag: Annotated[list[str] | None, Query(description="Filter by multiple tags")] = None,
):
    """Example: /query-demo/tags?tag=pc&tag=keyboard"""
    if not tag:
        return {"items": ITEMS}
    filtered = [it for it in ITEMS if any(t in it["tags"] for t in tag)]
    return {"tags": tag, "items": filtered}


# ────────────────────────────────
# Alias example
# ────────────────────────────────
@router.get("/alias")
def alias_example(
        q: Annotated[str | None, Query(alias="item-query", min_length=3)] = None
):
    """Example: /query-demo/alias?item-query=apple"""
    return {"received": q}


# ────────────────────────────────
# Regex validation
# ────────────────────────────────
@router.get("/regex")
def regex_example(
        q: Annotated[str | None, Query(pattern="^fixedquery$")] = None
):
    """Only allows q=fixedquery"""
    return {"q": q}


# ────────────────────────────────
# Deprecated parameter example
# ────────────────────────────────
@router.get("/deprecated")
def deprecated_example(
        q: Annotated[str | None, Query(deprecated=True)] = None
):
    """Shows as deprecated in Swagger UI"""
    return {"q": q, "message": "Deprecated param"}


# ────────────────────────────────
# Hidden parameter (not shown in docs)
# ────────────────────────────────
@router.get("/hidden")
def hidden_example(
        hidden: Annotated[str | None, Query(include_in_schema=False)] = None
):
    """Hidden parameter (not shown in /docs)"""
    return {"hidden": hidden}


# ────────────────────────────────
# Required parameter example
# ────────────────────────────────
@router.get("/required")
def required_example(q: Annotated[str, Query(min_length=2)]):
    """Parameter q is required"""
    return {"q": q}


# ────────────────────────────────
# Required but can be None
# ────────────────────────────────
@router.get("/required-none")
def required_none_example(q: Annotated[str | None, Query()] = None):
    """q is required, but may be None"""
    return {"q": q}


# ────────────────────────────────
# Custom validator with AfterValidator
# ────────────────────────────────
@router.get("/validate")
def custom_validate(
        id: Annotated[str | None, AfterValidator(ensure_known_id)] = None
):
    """Validates ID format"""
    return {"id": id}
