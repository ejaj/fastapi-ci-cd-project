# app/routers/items.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from worked_app.app.database import SessionLocal
from worked_app.app.models import Item, CategoryEnum
from worked_app.app.schemas import ItemCreate, ItemUpdate, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


# Dependency to provide DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Utility for computing tax-inclusive price (optional)
def _with_tax(price: float, tax: float | None) -> float | None:
    return None if tax is None else round(price + tax, 2)


# ───────────────────────────────────────────────
@router.post("/", response_model=ItemOut, status_code=201)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(
        name=item.name,
        description=item.description,
        price=item.price,
        tax=item.tax,
        category=CategoryEnum(item.category.value),
        status=item.status,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/", response_model=List[ItemOut])
def list_items(
        q: str | None = Query(default=None, description="Search by name"),
        db: Session = Depends(get_db),
):
    query = db.query(Item)
    if q:
        query = query.filter(Item.name.ilike(f"%{q}%"))
    return query.all()


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.put("/{item_id}", response_model=ItemOut)
def replace_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")

    db_item.name = item.name
    db_item.description = item.description
    db_item.price = item.price
    db_item.tax = item.tax
    db_item.category = CategoryEnum(item.category.value)
    db_item.status = item.status

    db.commit()
    db.refresh(db_item)
    return db_item


@router.patch("/{item_id}", response_model=ItemOut)
def patch_item(item_id: int, patch: ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")

    if patch.name is not None:
        db_item.name = patch.name
    if patch.description is not None:
        db_item.description = patch.description
    if patch.price is not None:
        db_item.price = patch.price
    if patch.tax is not None:
        db_item.tax = patch.tax
    if patch.category is not None:
        db_item.category = CategoryEnum(patch.category.value)
    if patch.status is not None:
        db_item.status = patch.status

    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")
    db.delete(db_item)
    db.commit()
    return None
