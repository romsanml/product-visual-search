from typing import Optional, List
from pydantic import BaseModel, Field

class ProductImageOut(BaseModel):
    image_id: int
    url: str

class ProductCreate(BaseModel):
    product_id: str
    category_id: Optional[str] = None
    title: Optional[str] = None
    rating: Optional[float] = None
    description: Optional[str] = None

class ProductOut(BaseModel):
    product_id: str
    category_id: Optional[str]
    title: Optional[str]
    rating: Optional[float]
    description: Optional[str]
    images: List[ProductImageOut] = Field(default_factory=list)

class SearchTextQuery(BaseModel):
    text: str
    limit: int = 10
