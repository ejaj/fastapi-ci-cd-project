from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Security - Authentication"])


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


def fake_decode_token(token: str) -> User:
    # Pretend to decode; return a user model
    return User(
        username=token + "fakedecoded",
        email="john@example.com",
        full_name="John Doe",
        disabled=False,
    )


# OAuth2 "password" flow with a Bearer token
# NOTE: Using a *relative* tokenUrl keeps it working even if you change prefixes or run behind a proxy.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    user = fake_decode_token(token)
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    # 🔒 First-steps demo: accept any username/password and return a dummy token.
    # Replace this with real user verification + JWT creation later.
    fake_token = f"fake-token-for-{form_data.username}"
    return {"access_token": fake_token, "token_type": "bearer"}


@router.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    # If this executes, an Authorization header with a Bearer token was present.
    # e.g. Authorization: Bearer <token>
    return {"token": token}


# Protected route that injects the current user
@router.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
