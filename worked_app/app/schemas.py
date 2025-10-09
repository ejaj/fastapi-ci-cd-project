# app/schemas.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum


class Category(str, Enum):
    general = "general"
    tech = "tech"
    books = "books"
    apparel = "apparel"


class ItemBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: str | None = Field(None, max_length=200)
    price: float = Field(..., gt=0)
    tax: float | None = Field(None, ge=0)
    category: Category = Category.general
    status: Literal["active", "inactive"] = "active"


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    tax: Optional[float] = Field(None, ge=0)
    category: Optional[Category] = None
    status: Optional[Literal["active", "inactive"]] = None


class ItemOut(ItemBase):
    id: int

    class Config:
        orm_mode = True
