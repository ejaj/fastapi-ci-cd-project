from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, status

router = APIRouter(prefix="/forms", tags=["Form Data"])


# 1) Classic login form (username/password). Content-Type: application/x-www-form-urlencoded
@router.api_route(
    "/login",
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    description="Accepts standard login form fields."
)
async def login(
        username: Annotated[str, Form(min_length=3, max_length=50, description="Login name")],
        password: Annotated[str, Form(min_length=6, description="Secret password")],
):
    # Pretend check
    if username == "admin" and password == "admin123":
        return {"message": "Welcome admin!"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


# 2) Fields with defaults, optional, and bool casting
@router.api_route(
    "/profile",
    methods=["POST"],
    description="Demonstrates optional fields, defaults, and boolean casting from forms."
)
async def update_profile(
        display_name: Annotated[str | None, Form(default=None, max_length=60)],
        bio: Annotated[str | None, Form(default=None, max_length=200)],
        # HTML checkbox typically sends "on" → FastAPI casts to bool
        newsletter_opt_in: Annotated[bool, Form(default=False)],
):
    return {
        "display_name": display_name,
        "bio": bio,
        "newsletter_opt_in": newsletter_opt_in,
    }


# 3) Aliases (HTML name=... can differ from your Python param)
@router.api_route(
    "/alias",
    methods=["POST"],
    description="Use alias to accept different HTML names."
)
async def alias_example(
        # Accepts HTML field called user-name, maps to python variable username
        username: Annotated[str, Form(alias="user-name", min_length=3)],
        # Accepts HTML field called user-age
        age: Annotated[int, Form(alias="user-age")],
):
    return {"username": username, "age": age}


# 4) Multiple values (e.g., <select multiple> or repeated inputs with same name)
@router.api_route(
    "/tags",
    methods=["POST"],
    description="Accept multiple values from a multi-select or repeated inputs."
)
async def submit_tags(
        tags: Annotated[list[str], Form(description="Multiple tags")],
):
    # Example HTML: <select name="tags" multiple> or multiple <input name="tags">
    return {"tags": tags}


# 5) OAuth2-style username/password as form (password grant style)
@router.api_route(
    "/oauth2/token",
    methods=["POST"],
    description="OAuth2 password flow example: username/password as form fields."
)
async def oauth2_token(
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        scope: Annotated[str | None, Form()] = "",  # often optional
        grant_type: Annotated[str, Form(pattern="password")] = "password",
):
    if username != "demo" or password != "secret":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_grant")
    # Normally return real JWT/access token
    return {"access_token": "fake-token-123", "token_type": "bearer", "scope": scope or ""}
