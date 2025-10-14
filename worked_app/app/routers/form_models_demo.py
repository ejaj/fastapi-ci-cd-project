from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel, constr

router = APIRouter(prefix="/form-models", tags=["Form Models"])


# Simple Pydantic model for form data
class LoginForm(BaseModel):
    username: constr(min_length=3, max_length=20)
    password: constr(min_length=6)


@router.api_route(
    "/login",
    methods=["POST"],
    status_code=status.HTTP_200_OK,
    description="Login form using Pydantic model as Form"
)
async def login(data: Annotated[LoginForm, Form()]):
    if data.username == "admin" and data.password == "secret123":
        return {"message": f"Welcome {data.username}!"}
    raise HTTPException(status_code=401, detail="Invalid credentials")


# Signup form with validation
class SignupForm(BaseModel):
    username: constr(min_length=3)
    email: constr(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: constr(min_length=8)
    confirm_password: constr(min_length=8)
    model_config = {"extra": "forbid"}  # Forbid extra form fields


@router.api_route(
    "/signup",
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
    description="Signup form demonstrating extra field validation"
)
async def signup(data: Annotated[SignupForm, Form()]):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    return {"message": f"User {data.username} registered successfully"}


# Profile update with optional fields
class ProfileForm(BaseModel):
    full_name: str | None = None
    bio: str | None = None


@router.api_route(
    "/profile",
    methods=["POST"],
    description="Profile update with optional fields"
)
async def update_profile(data: Annotated[ProfileForm, Form()]):
    return {"updated_data": data.model_dump(exclude_none=True)}
