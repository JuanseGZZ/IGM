from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import categories_fw.testing.repository as repo
import categories_fw.testing.service as service


@asynccontextmanager
async def lifespan(app: FastAPI):
    repo.init_db()
    yield


app = FastAPI(title="IGM Catalog API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class AttrImplSchema(BaseModel):
    attribute_key: str
    value: str


class VariantSchema(BaseModel):
    id: Optional[int] = None
    attribute_implementations: list[AttrImplSchema] = []


class ProductSchema(BaseModel):
    id: Optional[int] = None
    code: str
    title: str
    price: float
    description: str = ""
    brand: str = ""
    attributes_implementations: list[AttrImplSchema] = []
    variants: list[VariantSchema] = []


class CategorySchema(BaseModel):
    id: Optional[int] = None
    name: str
    attribute_ids: list[int] = []
    subcategories: list["CategorySchema"] = []
    products: list[ProductSchema] = []


CategorySchema.model_rebuild()


class AttributeSchema(BaseModel):
    id: int
    key: str
    name: str
    data_type: str
    is_static: bool
    enum_values: list[str] = []


class CatalogPayload(BaseModel):
    attributes: list[AttributeSchema]
    tree: CategorySchema


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/catalog")
def get_catalog():
    """Retorna el estado actual: todos los atributos y el árbol completo."""
    return service.load_catalog()


@app.post("/catalog")
def update_catalog(payload: CatalogPayload):
    """
    Valida el árbol recibido construyéndolo con models.py.
    Si es válido lo persiste y retorna {valid: true}.
    Si hay un error retorna 422 con {valid: false, error: <ubicación + mensaje>}.
    No modifica nada si hay un error.
    """
    result = service.validate_and_apply(payload)
    if not result["valid"]:
        raise HTTPException(status_code=422, detail=result)
    return result
