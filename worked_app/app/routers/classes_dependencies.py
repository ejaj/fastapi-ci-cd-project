from typing import Annotated, Any
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/class-deps", tags=["Classes as Dependencies"])

# Fake data to paginate/filter
fake_items_db = [
    {"item_name": "Foo"},
    {"item_name": "Bar"},
    {"item_name": "Baz"},
    {"item_name": "Qux"},
    {"item_name": "Quux"},
]


# ---------------------------------------
# Class dependency (callable via __init__)
# ---------------------------------------
class CommonQueryParams:
    """
    Class-based dependency: FastAPI will 'call' this class to create an instance,
    passing query params (q, skip, limit) into __init__.
    """

    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit


# ---------------------------------------------------------------------------------
# Using the explicit form: Annotated[CommonQueryParams, Depends(CommonQueryParams)]
# ---------------------------------------------------------------------------------
@router.api_route(
    "/items",
    methods=["GET"],
    summary="List items (explicit class dependency)",
    description="Uses Depends(CommonQueryParams) explicitly so you see the full form.",
)
async def list_items_explicit(
        commons: Annotated[CommonQueryParams, Depends(CommonQueryParams)]
):
    response: dict[str, Any] = {}
    # Optional filter by 'q'
    if commons.q:
        response["q"] = commons.q

    # Apply pagination with skip/limit
    items = fake_items_db[commons.skip: commons.skip + commons.limit]
    # If 'q' provided, filter by substring match
    if commons.q:
        items = [it for it in items if commons.q.lower() in it["item_name"].lower()]

    response["items"] = items
    response["meta"] = {"skip": commons.skip, "limit": commons.limit, "total": len(fake_items_db)}
    return response


# -------------------------------------------------------------------
# Using the shortcut: Annotated[CommonQueryParams, Depends()]
#    (FastAPI infers the dependency class from the type annotation)
# -------------------------------------------------------------------
@router.api_route(
    "/items/shortcut",
    methods=["GET"],
    summary="List items (shortcut class dependency)",
    description="Uses Depends() with a typed parameter (CommonQueryParams) as a shortcut.",
)
async def list_items_shortcut(
        commons: Annotated[CommonQueryParams, Depends()]
):
    # Same logic as above, showing identical behavior with cleaner signature
    items = fake_items_db[commons.skip: commons.skip + commons.limit]
    if commons.q:
        items = [it for it in items if commons.q.lower() in it["item_name"].lower()]
    return {
        "q": commons.q,
        "items": items,
        "meta": {"skip": commons.skip, "limit": commons.limit, "total": len(fake_items_db)},
    }


# -------------------------------------------------------------------
# Another route just to demonstrate reuse across endpoints
# -------------------------------------------------------------------
@router.api_route(
    "/users",
    methods=["GET"],
    summary="Pretend user list (reuses class dependency)",
    description="Shows reuse of the same class dependency across multiple endpoints.",
)
async def list_users(
        commons: Annotated[CommonQueryParams, Depends()]
):
    fake_users_db = [
        {"username": "alice"},
        {"username": "bob"},
        {"username": "carol"},
        {"username": "dave"},
    ]
    users = fake_users_db[commons.skip: commons.skip + commons.limit]
    if commons.q:
        users = [u for u in users if commons.q.lower() in u["username"].lower()]
    return {
        "q": commons.q,
        "users": users,
        "meta": {"skip": commons.skip, "limit": commons.limit, "total": len(fake_users_db)},
    }


# -------------------------------------------------------------------
# Minimal example showing that the type hint helps editors autocomplete
# -------------------------------------------------------------------
@router.api_route(
    "/echo",
    methods=["GET"],
    summary="Echo the parsed query params (useful to see autocomplete benefits)",
)
async def echo_params(
        commons: Annotated[CommonQueryParams, Depends()]
):
    # Accessing attributes gives you editor autocomplete: commons.q, commons.skip, commons.limit
    return {"q": commons.q, "skip": commons.skip, "limit": commons.limit}
