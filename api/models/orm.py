from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, ForeignKey, Float
from typing import List, Optional

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    category_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all,delete-orphan")

class ProductImage(Base):
    __tablename__ = "images"
    image_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String, ForeignKey("products.product_id"), index=True)
    rel_path: Mapped[str] = mapped_column(String)  # путь относительно storage_root
    product: Mapped[Product] = relationship("Product", back_populates="images")
