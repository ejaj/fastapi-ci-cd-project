from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

# ---------------------------
# DB & Engine (SQLite file)
# ---------------------------
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}  # safe for FastAPI threads with one session per request
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


# ---------------------------
# Session dependency (one per request)
# ---------------------------
def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


# ---------------------------
# Models
# ---------------------------

# Base (shared fields)
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: Optional[int] = Field(default=None, index=True)


# Table model
class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    secret_name: str


# Public response model (no secret_name)
class HeroPublic(HeroBase):
    id: int


# Create request model (includes secret_name)
class HeroCreate(HeroBase):
    secret_name: str


# Update request model (all optional; PATCH semantics)
class HeroUpdate(HeroBase):
    name: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None


# ---------------------------
# Router
# ---------------------------
router = APIRouter(prefix="/heroes", tags=["heroes"])


# Create
@router.api_route("/", methods=["POST"], response_model=HeroPublic)
def create_hero(hero_in: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero_in)  # copy fields into table model
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


# List (with simple pagination)
@router.api_route("/", methods=["GET"], response_model=List[HeroPublic])
def read_heroes(
        session: SessionDep,
        offset: int = 0,
        limit: Annotated[int, Query(le=100)] = 100,
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes


# Read one
@router.api_route("/{hero_id}", methods=["GET"], response_model=HeroPublic)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


# Update (PATCH)
@router.api_route("/{hero_id}", methods=["PATCH"], response_model=HeroPublic)
def update_hero(hero_id: int, hero_update: HeroUpdate, session: SessionDep):
    hero_db = session.get(Hero, hero_id)
    if not hero_db:
        raise HTTPException(status_code=404, detail="Hero not found")

    updates = hero_update.model_dump(exclude_unset=True)
    # SQLModel provides a helper to apply dict updates
    hero_db.sqlmodel_update(updates)
    session.add(hero_db)
    session.commit()
    session.refresh(hero_db)
    return hero_db


# Delete
@router.api_route("/{hero_id}", methods=["DELETE"])
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
