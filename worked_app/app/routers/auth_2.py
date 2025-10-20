from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter(prefix="/auth2", tags=["Security - Authentication"])

# OAuth2 password flow; relative tokenUrl -> resolves to /api/token in docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# ------------------------
# Fake DB and helpers (demo only)
# ------------------------
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",  # password: secret
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",  # password: secret2
        "disabled": True,
    },
}


def fake_hash_password(password: str) -> str:
    return "fakehashed" + password


# ------------------------
# Models
# ------------------------
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ------------------------
# Data access helpers
# ------------------------
def get_user(db: dict, username: str) -> Optional[UserInDB]:
    user_dict = db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


def fake_decode_token(token: str) -> Optional[UserInDB]:
    # For this simple demo, the "token" is just the username.
    # In a real app, decode/verify a JWT and extract the subject/claims.
    return get_user(fake_users_db, token)


# ------------------------
# Dependencies
# ------------------------
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    user = fake_decode_token(token)
    if not user:
        # OAuth2/Bearer-compliant error response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
        current_user: Annotated[UserInDB, Depends(get_current_user)]
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ------------------------
# Routes
# ------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = get_user(fake_users_db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    hashed = fake_hash_password(form_data.password)
    if hashed != user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    # For the simple example, return the username as the token
    return {"access_token": user.username, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user
