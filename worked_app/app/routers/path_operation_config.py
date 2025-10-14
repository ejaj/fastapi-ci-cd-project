from enum import Enum
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["Path Config Demo"])


# -------------------------
# Models
# -------------------------
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()


# -------------------------
# Tags as Enum (optional, for consistency)
# -------------------------
class Tags(Enum):
    items = "items"
    users = "users"


# -------------------------
# 1) Status code + tags + summary/description + response_description
# -------------------------
@router.post(
    "/items/",
    response_model=Item,
    status_code=status.HTTP_201_CREATED,
    tags=["items"],
    summary="Create an item",
    description=(
            "Create an item with all the information:\n\n"
            "- **name**: each item must have a name\n"
            "- **description**: a long description\n"
            "- **price**: required\n"
            "- **tax**: optional\n"
            "- **tags**: a set of unique tag strings for this item"
    ),
    response_description="The created item",
)
async def create_item(item: Item) -> Item:
    return item


# -------------------------
# 2) Simple listing + string tags
# -------------------------
@router.get("/items/", tags=["items"])
async def read_items():
    return [{"name": "Foo", "price": 42}]


# -------------------------
# 3) Another group with a different tag
# -------------------------
@router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "johndoe"}]


# -------------------------
# 4) Using Enum tags to avoid typos
# -------------------------
@router.get("/items-enum/", tags=[Tags.items])
async def read_items_enum():
    return ["Portal gun", "Plumbus"]


@router.get("/users-enum/", tags=[Tags.users])
async def read_users_enum():
    return ["Rick", "Morty"]


# -------------------------
# 5) Long description from docstring (Markdown supported)
# -------------------------
@router.post("/items-doc/", response_model=Item, summary="Create an item (docstring)", tags=["items"])
async def create_item_with_docstring(item: Item) -> Item:
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: optional
    - **tags**: a set of unique tag strings for this item
    """
    return item


# -------------------------
# 6) Deprecated path operation
# -------------------------
@router.get("/elements/", tags=["items"], deprecated=True)
async def read_elements():
    return [{"item_id": "Foo"}]


# -------------------------
# 7) Using the generic decorator @router.api_route
#    (multi-method example)
# -------------------------
@router.api_route(
    "/items/any-method",
    methods=["GET", "POST"],
    tags=["items"],
    summary="Handle multiple methods on one path",
    description="Demonstrates using `@router.api_route` with multiple HTTP methods.",
    response_description="The result of the operation",
)
async def items_any_method():
    return {"message": "This route accepts GET and POST"}
