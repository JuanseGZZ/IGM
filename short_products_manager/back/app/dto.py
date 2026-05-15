from pydantic import BaseModel
from typing import Optional


class BrandDTO(BaseModel):
    id: str
    name: str


class AttributeImplementationDTO(BaseModel):
    attributeId: str
    value: str


class StockDTO(BaseModel):
    id: str
    quantity: float
    date: str
    cost_unit_price: float = 0.0


class VariantDTO(BaseModel):
    id: str
    price: float
    implementations: list[AttributeImplementationDTO] = []
    historical_stocks: list[StockDTO] = []


class AttributeDTO(BaseModel):
    id: str
    key: str
    values: list[str] = []


class ProductDTO(BaseModel):
    id: str
    name: str
    description: str = ""
    brand: Optional[BrandDTO] = None
    attributes: list[AttributeDTO] = []
    variants: list[VariantDTO] = []
    photo: Optional[str] = None


class StateDTO(BaseModel):
    products: list[ProductDTO] = []
    brands: list[BrandDTO] = []
