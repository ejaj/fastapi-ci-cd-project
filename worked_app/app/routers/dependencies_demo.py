from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

# Create router
router = APIRouter(prefix="/deps", tags=["Dependencies Demo"])


# --------------------------------
# Basic dependency
# --------------------------------
async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    """Common query parameters dependency"""
    return {"q": q, "skip": skip, "limit": limit}


# Define a type alias to reuse it easily
CommonsDep = Annotated[dict, Depends(common_parameters)]


# --------------------------------
# Example of a simple reusable dependency chain
# --------------------------------
def get_token(authorization: str | None = None):
    """
    Fake token extractor.
    Normally you'd read from headers, e.g.:
    Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return authorization


def get_current_user(token: Annotated[str, Depends(get_token)]):
    """Fake user lookup"""
    # Normally you’d decode the token or look it up in a DB.
    if token != "supersecrettoken":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    return {"username": "alice", "is_admin": True}


def require_admin(user: Annotated[dict, Depends(get_current_user)]):
    """Sub-dependency that ensures the user is admin"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user


# --------------------------------
# Routes using @router.api_route
# --------------------------------
@router.api_route(
    "/items",
    methods=["GET"],
    summary="List items with common query parameters (uses dependency)",
)
async def read_items(commons: CommonsDep):
    """Demonstrates shared dependency injection for pagination/filtering."""
    return {
        "message": "Listing items",
        "query": commons,
    }


@router.api_route(
    "/users",
    methods=["GET"],
    summary="List users (shares same common dependency)",
)
async def read_users(commons: CommonsDep):
    """Reuses the same dependency alias (CommonsDep)."""
    return {
        "message": "Listing users",
        "query": commons,
    }


@router.api_route(
    "/me",
    methods=["GET"],
    summary="Get current user (requires token)",
)
async def read_me(user: Annotated[dict, Depends(get_current_user)]):
    """Requires token, returns current user info."""
    return {
        "message": "User info retrieved successfully",
        "user": user,
    }


@router.api_route(
    "/admin/dashboard",
    methods=["GET"],
    summary="Admin-only route (sub-dependency chain)",
)
async def admin_dashboard(admin: Annotated[dict, Depends(require_admin)]):
    """Protected route using a dependency chain."""
    return {
        "message": "Welcome, admin!",
        "admin_user": admin,
    }


@router.api_route(
    "/about",
    methods=["GET"],
    summary="Demonstrates a simple route with no dependency",
)
async def about():
    """No dependency used here."""
    return {"message": "This route has no dependencies"}
