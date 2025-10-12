# app/models.py
from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum
from database import Base
import enum


class CategoryEnum(str, enum.Enum):
    general = "general"
    tech = "tech"
    books = "books"
    apparel = "apparel"


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True, nullable=False)
    description = Column(String(200), nullable=True)
    price = Column(Float, nullable=False)
    tax = Column(Float, nullable=True)
    category = Column(SAEnum(CategoryEnum), default=CategoryEnum.general)
    status = Column(String(8), default="active")
