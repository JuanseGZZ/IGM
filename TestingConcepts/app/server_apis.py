"""
server_apis.py — Capa HTTP (FastAPI).

Arquitectura: API → (Pydantic schemas) → Service → Repos → Models

Convenciones de respuesta:
  - 200  → operación exitosa, retorna el objeto actualizado en JSON.
  - 201  → recurso creado.
  - 400  → violación de regla de negocio (ValueError del service).
  - 404  → entidad no encontrada.

  Para operaciones que pueden requerir implementaciones del cliente:
    {
      "needs_implementations": true,
      "impact": [...]     ← qué productos/variantes necesitan valor
    }
  El cliente provee las implementations y reintenta el mismo endpoint.

  Para del_attribute con del_opt=0 y hay impacto:
    {
      "needs_decision": true,
      "impact": [...]     ← productos afectados
    }
  El cliente elige del_opt (1 ó 2) y reintenta.

Para correr:  uvicorn server_apis:app --reload --app-dir TestingConcepts/app
"""

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from service import AttributeService, CategoryService, ProductService
from config import conn


app = FastAPI(title="IGM — Product Management API", version="1.0")


# ─── helpers ────────────────────────────────────────────────────────────────

def _404(entity: str, key) -> None:
    raise HTTPException(status_code=404, detail=f"{entity} '{key}' no encontrado")

def _400(msg: str) -> None:
    raise HTTPException(status_code=400, detail=msg)

def _run(fn):
    """Ejecuta fn(), convierte ValueError → 400. Rollback en cualquier error."""
    try:
        return fn()
    except ValueError as e:
        conn.rollback()
        _400(str(e))
    except Exception:
        conn.rollback()
        raise

def _serialize_cat(cat):
    d = cat.to_json()
    d["products"] = [p.to_json() for p in cat.products]
    return d


# ═══════════════════════════════════════════════════════════════════════════
# SCHEMAS — request bodies
# ═══════════════════════════════════════════════════════════════════════════

# ── Attribute ───────────────────────────────────────────────────────────────

class AttributeCreateBody(BaseModel):
    key:        str
    name:       str
    data_type:  str          # text | number | boolean | enum
    is_static:  bool
    enum_values: list[str] = []

class AttributeUpdateBody(BaseModel):
    name:        Optional[str]       = None
    enum_values: Optional[list[str]] = None

class EnumValueBody(BaseModel):
    value: str


# ── Category ────────────────────────────────────────────────────────────────

class CategoryCreateBody(BaseModel):
    name: str

class CategoryUpdateBody(BaseModel):
    name: str

class VariantImplEntry(BaseModel):
    variant_id: int
    value:      Any

class ProductVariantImplEntry(BaseModel):
    product_id: int
    variants:   list[VariantImplEntry]

class AddDynamicAttrBody(BaseModel):
    attribute_id:    int
    implementations: Optional[list[ProductVariantImplEntry]] = None

class ProductImplEntry(BaseModel):
    product_id: int
    value:      Any

class AddStaticAttrBody(BaseModel):
    attribute_id:    int
    implementations: Optional[list[ProductImplEntry]] = None

class DelAttrQuery(BaseModel):
    del_opt: int = 0


# ── Product ─────────────────────────────────────────────────────────────────

class ProductCreateBody(BaseModel):
    code:        str
    title:       str
    price:       float
    description: str
    brand:       str
    category_id: int

class ProductUpdateBody(BaseModel):
    title:       Optional[str]   = None
    price:       Optional[float] = None
    description: Optional[str]   = None
    brand:       Optional[str]   = None
    category_id: Optional[int]   = None

class VariantOptionEntry(BaseModel):
    variant_id: int
    value:      Any

class AddDynamicAttrToProductBody(BaseModel):
    attribute_id:    int
    variant_options: Optional[list[VariantOptionEntry]] = None

class AddImplementationBody(BaseModel):
    attribute_id: int
    value:        Any

class VariantImplItem(BaseModel):
    attribute_id: int
    value:        Any

class CreateVariantBody(BaseModel):
    implementations: list[VariantImplItem]


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES — Attributes
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/attributes", tags=["attributes"])
def list_attributes():
    return [a.to_json() for a in AttributeService.get_all()]


@app.get("/attributes/{attr_id}", tags=["attributes"])
def get_attribute(attr_id: int):
    attr = AttributeService.get(attr_id)
    if attr is None:
        _404("Atributo", attr_id)
    return attr.to_json()


@app.post("/attributes", status_code=201, tags=["attributes"])
def create_attribute(body: AttributeCreateBody):
    attr = _run(lambda: AttributeService.create(
        key=body.key,
        name=body.name,
        data_type=body.data_type,
        is_static=body.is_static,
        enum_values=body.enum_values,
    ))
    return attr.to_json()


@app.patch("/attributes/{attr_id}", tags=["attributes"])
def update_attribute(attr_id: int, body: AttributeUpdateBody):
    attr = _run(lambda: AttributeService.update(attr_id, body.name, body.enum_values))
    if attr is None:
        _404("Atributo", attr_id)
    return attr.to_json()


@app.delete("/attributes/{attr_id}", tags=["attributes"])
def delete_attribute(attr_id: int):
    deleted = _run(lambda: AttributeService.delete(attr_id))
    if not deleted:
        _404("Atributo", attr_id)
    return {"deleted": True}


@app.post("/attributes/{attr_id}/enum-values", tags=["attributes"])
def add_enum_value(attr_id: int, body: EnumValueBody):
    """Agrega un valor posible a un atributo de tipo enum."""
    attr = _run(lambda: AttributeService.add_enum_value(attr_id, body.value))
    if attr is None:
        _404("Atributo", attr_id)
    return attr.to_json()


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES — Categories
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/categories", tags=["categories"])
def list_categories():
    return [_serialize_cat(c) for c in CategoryService.get_all()]


@app.get("/categories/{cat_id}", tags=["categories"])
def get_category(cat_id: int):
    cat = CategoryService.get(cat_id)
    if cat is None:
        _404("Categoría", cat_id)
    return _serialize_cat(cat)


@app.post("/categories", status_code=201, tags=["categories"])
def create_category(body: CategoryCreateBody):
    return _serialize_cat(CategoryService.create(body.name))


@app.patch("/categories/{cat_id}", tags=["categories"])
def update_category(cat_id: int, body: CategoryUpdateBody):
    cat = CategoryService.update_name(cat_id, body.name)
    if cat is None:
        _404("Categoría", cat_id)
    return _serialize_cat(cat)


@app.delete("/categories/{cat_id}", tags=["categories"])
def delete_category(cat_id: int):
    deleted = _run(lambda: CategoryService.delete(cat_id))
    if not deleted:
        _404("Categoría", cat_id)
    return {"deleted": True}


@app.post("/categories/{cat_id}/dynamic-attribute", tags=["categories"])
def category_add_dynamic_attribute(cat_id: int, body: AddDynamicAttrBody):
    """
    Agrega atributo dinámico a la categoría.

    Primera llamada (sin implementations):
      → Si hay productos impactados retorna needs_implementations=true e impact.

    Segunda llamada (con implementations completas):
      → Aplica el atributo y retorna la categoría actualizada.
    """
    impl_data = None
    if body.implementations:
        impl_data = [
            {
                "product_id": e.product_id,
                "variants": [{"variant_id": v.variant_id, "value": v.value}
                             for v in e.variants],
            }
            for e in body.implementations
        ]

    result = _run(lambda: CategoryService.add_dynamic_attribute(
        cat_id, body.attribute_id, impl_data
    ))

    if result["needs_implementations"]:
        return {"needs_implementations": True, "impact": result["impact"]}
    return {"needs_implementations": False, "category": _serialize_cat(result["category"])}


@app.post("/categories/{cat_id}/static-attribute", tags=["categories"])
def category_add_static_attribute(cat_id: int, body: AddStaticAttrBody):
    """
    Agrega atributo estático a la categoría.

    Primera llamada (sin implementations):
      → Si hay productos impactados retorna needs_implementations=true e impact.

    Segunda llamada (con implementations completas):
      → Aplica el atributo y retorna la categoría actualizada.
    """
    impl_data = None
    if body.implementations:
        impl_data = [{"product_id": e.product_id, "value": e.value}
                     for e in body.implementations]

    result = _run(lambda: CategoryService.add_static_attribute(
        cat_id, body.attribute_id, impl_data
    ))

    if result["needs_implementations"]:
        return {"needs_implementations": True, "impact": result["impact"]}
    return {"needs_implementations": False, "category": _serialize_cat(result["category"])}


@app.delete("/categories/{cat_id}/attributes/{attr_id}", tags=["categories"])
def category_del_attribute(cat_id: int, attr_id: int, del_opt: int = 0):
    """
    Elimina atributo de la categoría.

    del_opt=0 (default): retorna needs_decision=true con impacto si hay productos afectados.
    del_opt=1: elimina implementaciones huérfanas en productos/variantes.
    del_opt=2: inyecta la definición del atributo directamente en los productos afectados.
    """
    result = _run(lambda: CategoryService.del_attribute(cat_id, attr_id, del_opt))

    if result["needs_decision"]:
        return {"needs_decision": True, "impact": result["impact"]}
    return {"needs_decision": False, "category": _serialize_cat(result["category"])}


@app.post("/categories/{cat_id}/products/{product_id}", tags=["categories"])
def category_add_product(cat_id: int, product_id: int):
    """Reasigna el producto a esta categoría (cambia product.category_id)."""
    prod = _run(lambda: CategoryService.add_product_to_category(cat_id, product_id))
    return prod.to_json()


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES — Products
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/products", tags=["products"])
def list_products():
    return [p.to_json() for p in ProductService.get_all()]


# /by-code debe ir ANTES de /{prod_id} para que FastAPI no trate "by-code" como int
@app.get("/products/by-code/{code}", tags=["products"])
def get_product_by_code(code: str):
    prod = ProductService.get_by_code(code)
    if prod is None:
        _404("Producto con código", code)
    return prod.to_json()


@app.get("/products/{prod_id}", tags=["products"])
def get_product(prod_id: int):
    prod = ProductService.get(prod_id)
    if prod is None:
        _404("Producto", prod_id)
    return prod.to_json()


@app.post("/products", status_code=201, tags=["products"])
def create_product(body: ProductCreateBody):
    prod = _run(lambda: ProductService.create(
        code=body.code,
        title=body.title,
        price=body.price,
        description=body.description,
        brand=body.brand,
        category_id=body.category_id,
    ))
    return prod.to_json()


@app.patch("/products/{prod_id}", tags=["products"])
def update_product(prod_id: int, body: ProductUpdateBody):
    prod = _run(lambda: ProductService.update(
        prod_id,
        title=body.title,
        price=body.price,
        description=body.description,
        brand=body.brand,
        category_id=body.category_id,
    ))
    if prod is None:
        _404("Producto", prod_id)
    return prod.to_json()


@app.delete("/products/{prod_id}", tags=["products"])
def delete_product(prod_id: int):
    deleted = _run(lambda: ProductService.delete(prod_id))
    if not deleted:
        _404("Producto", prod_id)
    return {"deleted": True}


@app.post("/products/{prod_id}/dynamic-attribute", tags=["products"])
def product_add_dynamic_attribute(prod_id: int, body: AddDynamicAttrToProductBody):
    """
    Agrega atributo dinámico al producto.

    Primera llamada (sin variant_options, o si el producto no tiene variantes):
      → Si el producto tiene variantes retorna needs_implementations=true con sus IDs.

    Segunda llamada (con variant_options completas):
      → Aplica el atributo y retorna el producto actualizado.
    """
    opts = None
    if body.variant_options is not None:
        opts = [{"variant_id": v.variant_id, "value": v.value}
                for v in body.variant_options]

    result = _run(lambda: ProductService.add_dynamic_attribute(
        prod_id, body.attribute_id, opts
    ))

    if result["needs_implementations"]:
        return {"needs_implementations": True, "impact": result["impact"]}
    return {"needs_implementations": False, "product": result["product"].to_json()}


@app.post("/products/{prod_id}/implementations", tags=["products"])
def product_add_implementation(prod_id: int, body: AddImplementationBody):
    """
    Agrega implementación de atributo estático al producto.
    El atributo debe estar suscripto en la categoría del producto (o en sus atributos propios).
    """
    prod = _run(lambda: ProductService.add_implementation(
        prod_id, body.attribute_id, body.value
    ))
    return prod.to_json()


@app.delete("/products/{prod_id}/attributes/{attr_key}", tags=["products"])
def product_del_own_attribute(prod_id: int, attr_key: str, del_opt: int = 0):
    """
    Elimina atributo propio del producto.

    del_opt=0 (default): retorna needs_decision=true con impacto si hay implementaciones.
    del_opt=1: elimina implementaciones huérfanas (estáticas o de variantes).
    """
    result = _run(lambda: ProductService.del_own_attribute(prod_id, attr_key, del_opt))

    if result["needs_decision"]:
        return {"needs_decision": True, "impact": result["impact"]}
    return {"needs_decision": False, "product": result["product"].to_json()}


@app.post("/products/{prod_id}/variants", tags=["products"])
def product_create_variant(prod_id: int, body: CreateVariantBody):
    """
    Crea una variante del producto.

    implementations debe cubrir exactamente todos los atributos dinámicos
    del producto (propios + heredados de la categoría).

    Si no matchean → retorna error con los atributos necesarios.
    """
    impl_data = [{"attribute_id": i.attribute_id, "value": i.value}
                 for i in body.implementations]

    result = _run(lambda: ProductService.create_variant(prod_id, impl_data))

    if "error" in result:
        return {
            "error": result["error"],
            "needed_attributes": result["needed_attributes"],
        }
    return result["product"].to_json()


@app.delete("/products/{prod_id}/variants/{variant_id}", tags=["products"])
def product_del_variant(prod_id: int, variant_id: int):
    """Elimina una variante del producto."""
    prod = _run(lambda: ProductService.del_variant(prod_id, variant_id))
    return prod.to_json()
