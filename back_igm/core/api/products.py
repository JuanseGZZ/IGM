from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/products", tags=["products"])

# Modelo
class Product(BaseModel):
    id: int
    name: str
    price: float

# Fake DB
products_db: List[Product] = []

@router.get("/", response_model=List[Product])
def list_products():
    return products_db

@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    for product in products_db:
        if product.id == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@router.post("/", response_model=Product)
def create_product(product: Product):
    products_db.append(product)
    return product