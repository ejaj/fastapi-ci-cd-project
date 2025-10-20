from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional, Dict, Any, List

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from pwdlib import PasswordHash

router = APIRouter(prefix="/auth/jwt", tags=["FastAPI Auth (OAuth2 + JWT + Argon2)"])

# ------------------------------------------------------------------------------
# Config (put secrets in env vars in real apps)
#   Generate a strong key with:  openssl rand -hex 32
# ------------------------------------------------------------------------------
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # resolves to /api/token
password_hash = PasswordHash.recommended()  # Argon2id by default

# ------------------------------------------------------------------------------
# Fake DB (demo). Hashed password corresponds to plaintext 'secret'
# ------------------------------------------------------------------------------
fake_users_db: Dict[str, Dict[str, Any]] = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        # Argon2id hash for 'secret' (from tutorial)
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    },
    # Example inactive user (password would be 'secret2' if you add a matching hash)
    # "alice": { ... "disabled": True }
}


# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def get_user(db: Dict[str, Dict[str, Any]], username: str) -> Optional[UserInDB]:
    user_dict = db.get(username)
    return UserInDB(**user_dict) if user_dict else None


def authenticate_user(db: Dict[str, Dict[str, Any]], username: str, password: str) -> Optional[UserInDB]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------------------
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exc
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exc
    user = get_user(fake_users_db, username=token_data.username)  # type: ignore[arg-type]
    if user is None:
        raise credentials_exc
    return user


async def get_current_active_user(current_user: Annotated[UserInDB, Depends(get_current_user)]) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    OAuth2 Password flow: accepts form-encoded 'username' & 'password'.
    Returns a signed JWT in { access_token, token_type } format.
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        # Spec-compliant: 401 + WWW-Authenticate header
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user


@router.get("/users/me/items")
async def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]) -> List[dict]:
    return [{"item_id": "Foo", "owner": current_user.username}]
