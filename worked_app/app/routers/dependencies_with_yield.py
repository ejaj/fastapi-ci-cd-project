from typing import Annotated, Optional
from fastapi import (
    FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks
)
from contextlib import asynccontextmanager

router = APIRouter(prefix="/api", tags=["demo"])


# ----------------------- Fake DB session -----------------------

class DBSession:
    def __init__(self):
        self.closed = False
        print("DBSession: open")

    def query(self, table: str):
        if self.closed:
            raise RuntimeError("DBSession already closed")
        print(f"DBSession: query on {table}")
        return [{"id": 1, "name": "Foo"}]

    def close(self):
        self.closed = True
        print("DBSession: close")


# Classic: ensure DB closes even on errors
async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


# ----------------------- Sub-dependencies with yield -----------------------

# These simulate resources that depend on each other and must close in order.

class DepA:
    def close(self): print("DepA: close")


class DepB:
    def close(self, dep_a: DepA): print("DepB: close (needs DepA)")


class DepC:
    def close(self, dep_b: DepB): print("DepC: close (needs DepB)")


async def dependency_a():
    dep_a = DepA()
    print("DepA: open")
    try:
        yield dep_a
    finally:
        dep_a.close()


async def dependency_b(dep_a: Annotated[DepA, Depends(dependency_a)]):
    dep_b = DepB()
    print("DepB: open")
    try:
        yield dep_b
    finally:
        dep_b.close(dep_a)


async def dependency_c(dep_b: Annotated[DepB, Depends(dependency_b)]):
    dep_c = DepC()
    print("DepC: open")
    try:
        yield dep_c
    finally:
        dep_c.close(dep_b)


# ----------------------- yield + try/except mapping -----------------------

class OwnerError(Exception):
    pass


# This dependency provides a username, but can catch specific internal errors
# and map them to HTTP errors if they bubble up through the 'yield'.
def current_username():
    try:
        # setup (e.g., read from session / token) — simple constant for demo
        print("current_username: setup")
        yield "Rick"
    except OwnerError as e:
        print("current_username: caught OwnerError")
        # Map to HTTP 400 for demo
        raise HTTPException(status_code=400, detail=f"Owner error: {e}") from e
    finally:
        print("current_username: teardown")


# ----------------------- Background task (for timing) -----------------------

def after_response_task(item_id: str):
    # Runs after response has been sent; cleanup from yield has already run
    print(f"Background task: post-process {item_id}")


# ----------------------- Endpoints -----------------------

@router.api_route("/items", methods=["GET"])
async def list_items(db: Annotated[DBSession, Depends(get_db)]):
    # Demonstrates DB usage; DB closes after response
    rows = db.query("items")
    return {"items": rows}


@router.api_route("/items/{item_id}", methods=["GET"])
async def get_item(
        item_id: str,
        username: Annotated[str, Depends(current_username)],  # has yield + except mapping
        db: Annotated[DBSession, Depends(get_db)],
        background: BackgroundTasks,
):
    """
    - If item_id == 'portal-gun', we raise OwnerError to show dependency with yield catching it.
    - Else we return a fake item and schedule a background task.
    """
    if item_id == "portal-gun":
        # Triggers OwnerError, caught in dependency 'current_username'
        raise OwnerError(f"{username} is not allowed to own a portal gun")

    # Normal path
    rows = db.query("items")
    item = next((r for r in rows if r["id"] == 1), {"id": 1, "name": "Foo"})
    background.add_task(after_response_task, item_id)
    return {"item": item, "owner": username}


@router.api_route("/chain", methods=["GET"])
async def chain(dep_c: Annotated[DepC, Depends(dependency_c)]):
    """
    Touch a chain of yield dependencies (A -> B -> C). Cleanup order will be:
    DepC.close -> DepB.close(dep_a) -> DepA.close
    (Watch logs/console to see the order.)
    """
    return {"status": "ok", "info": "check server logs for open/close order"}
