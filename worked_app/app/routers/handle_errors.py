from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

# -------------------------
# Data / Models
# -------------------------
items = {"foo": "The Foo Wrestlers"}


class Item(BaseModel):
    title: str
    size: int


# -------------------------
# Custom Exception
# -------------------------
class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


router = APIRouter(prefix="", tags=["Error Handling"])


@router.api_route("/items/{item_id}", methods=["GET"])
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail={"message": "Item not found", "id": item_id})
    return {"item": items[item_id]}


@router.get("/items-header/{item_id}")
async def read_item_with_header(item_id: str):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


@router.get("/unicorns/{name}")
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}


@router.post("/items/")
async def create_item(item: Item):
    return item


# -------------------------
# Global Exception Handlers
# -------------------------
@router.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


@router.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@router.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
