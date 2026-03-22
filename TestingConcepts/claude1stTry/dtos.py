from pydantic import BaseModel


# ── Attribute ────────────────────────────────────────────────────────────────

class AttributeCreate(BaseModel):
    key: str
    name: str
    data_type: str          # text | number | boolean | enum
    is_static: bool = False  # solo aplica si data_type == "enum"
    enum_values: list[str] = []

class AttributeUpdate(BaseModel):
    name: str
    is_static: bool = False  # solo aplica si data_type == "enum"
    enum_values: list[str] = []

class AttributeOut(BaseModel):
    id: int
    key: str
    name: str
    data_type: str
    is_static: bool
    enum_values: list[str]


# ── Category ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    attribute_ids: list[int] = []

class CategoryUpdate(BaseModel):
    name: str
    attribute_ids: list[int] = []

class CategoryOut(BaseModel):
    id: int
    name: str
    attributes: list[AttributeOut]


# ── Product ───────────────────────────────────────────────────────────────────

class ImplementationIn(BaseModel):
    attribute_id: int
    value: str  # siempre string, la validacion del tipo la hace el dominio

class ProductCreate(BaseModel):
    code: str
    title: str
    price: float
    description: str
    brand: str
    category_id: int
    attribute_ids: list[int] = []              # atributos propios del producto
    static_implementations: list[ImplementationIn] = []  # implementaciones estaticas

class ProductUpdate(BaseModel):
    title: str
    price: float
    description: str
    brand: str
    category_id: int
    attribute_ids: list[int] = []
    static_implementations: list[ImplementationIn] = []

class ImplementationOut(BaseModel):
    id: int
    attribute: AttributeOut
    value: str

class VariantIn(BaseModel):
    implementations: list[ImplementationIn]

class VariantOut(BaseModel):
    id: int
    attribute_implementations: list[ImplementationOut]

class ProductOut(BaseModel):
    id: int
    code: str
    title: str
    price: float
    description: str
    brand: str
    category: CategoryOut
    attributes: list[AttributeOut]             # atributos propios del producto
    attributes_implementations: list[ImplementationOut]
    variants: list[VariantOut]

class ProductSummary(BaseModel):
    id: int
    code: str
    title: str
    price: float
    brand: str
    category_id: int
    category_name: str
    variant_count: int