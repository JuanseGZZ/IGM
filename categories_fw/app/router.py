from fastapi import APIRouter, HTTPException
from app import store
from app.models import AttributeImplementation, Variant
from app.schemas import (
    ImpactResponse, SuccessResponse,
    ChangeFatherRequest,
    AddAttributeRequest, RemoveAttributeRequest,
    ChangeCategoryRequest, ChangeCategoryImpactResponse,
    AddVariantRequest,
)
from app.services import CategoryService, ProductService

router = APIRouter()
cat_svc  = CategoryService()
prod_svc = ProductService()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_category(cat_id: int):
    cat = store.get_category(cat_id)
    if cat is None:
        raise HTTPException(status_code=404, detail=f"Categoria {cat_id} no encontrada.")
    return cat

def _get_product(prod_id: int):
    prod = store.get_product(prod_id)
    if prod is None:
        raise HTTPException(status_code=404, detail=f"Producto {prod_id} no encontrado.")
    return prod

def _get_attribute(attr_id: int):
    attr = store.get_attribute(attr_id)
    if attr is None:
        raise HTTPException(status_code=404, detail=f"Atributo {attr_id} no encontrado.")
    return attr

def _get_variant(var_id: int):
    var = store.get_variant(var_id)
    if var is None:
        raise HTTPException(status_code=404, detail=f"Variante {var_id} no encontrada.")
    return var

def _all_product_ids(resolution) -> list[int]:
    if resolution is None:
        return []
    return [pid for g in resolution for pid in g.product_ids]


# ── E1 / E2 / E3 — categoria cambia padre ─────────────────────────────────────
#
# PATCH /categories/{id}/father
#
# Fase 1 — sin resolution en el body:
#   { "new_father_id": 5 }
#   → 200 { "status": "impact_pending", "impact": [...] }
#
# Fase 2 — con resolution:
#   {
#     "new_father_id": 5,
#     "resolution": [
#       { "attr_ids": [3, 4], "product_ids": [10, 11], "action": "eliminar" },
#       { "attr_ids": [2],    "product_ids": [12],      "action": "heredar"  }
#     ]
#   }
#   → 200 { "status": "ok" }
#   → 200 { "status": "impact_pending", ... }  si la resolution no cubre todo

@router.patch(
    "/categories/{cat_id}/father",
    response_model=ImpactResponse | SuccessResponse,
)
def change_father(cat_id: int, body: ChangeFatherRequest):
    category   = _get_category(cat_id)
    new_father = _get_category(body.new_father_id) if body.new_father_id is not None else None

    try:
        products_by_id = store.get_products_by_ids(_all_product_ids(body.resolution))
        return cat_svc.change_father(category, new_father, body.resolution, products_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E4 — categoria agrega atributo ────────────────────────────────────────────
#
# POST /categories/{id}/attributes/{attr_id}
#
# Fase 1 — body vacio o sin resolution:
#   {}
#   → 200 { "status": "impact_pending", "impact": [...] }
#
# Fase 2 — con resolution:
#   { "resolution": [{ "attr_ids": [4], "product_ids": [10], "action": "eliminar" }] }
#   → 200 { "status": "ok" }

@router.post(
    "/categories/{cat_id}/attributes/{attr_id}",
    response_model=ImpactResponse | SuccessResponse,
)
def add_attribute(cat_id: int, attr_id: int, body: AddAttributeRequest = AddAttributeRequest()):
    category = _get_category(cat_id)
    attr     = _get_attribute(attr_id)

    try:
        products_by_id = store.get_products_by_ids(_all_product_ids(body.resolution))
        return cat_svc.add_attribute(category, attr, body.resolution, products_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E5 — categoria elimina atributo ───────────────────────────────────────────
#
# DELETE /categories/{id}/attributes/{attr_id}
#
# Mismo contrato de dos fases que E4.

@router.delete(
    "/categories/{cat_id}/attributes/{attr_id}",
    response_model=ImpactResponse | SuccessResponse,
)
def remove_attribute(cat_id: int, attr_id: int, body: RemoveAttributeRequest = RemoveAttributeRequest()):
    category = _get_category(cat_id)
    attr     = _get_attribute(attr_id)

    try:
        products_by_id = store.get_products_by_ids(_all_product_ids(body.resolution))
        return cat_svc.remove_attribute(category, attr, body.resolution, products_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E6 — producto cambia de categoria ─────────────────────────────────────────
#
# PATCH /products/{id}/category/{new_category_id}
#
# Fase 1 — sin resolution:
#   {}
#   → 200 {
#       "status": "impact_pending",
#       "to_add":    [{ "id": 4, "key": "garantia", "name": "Garantia" }],
#       "to_remove": [{ "id": 1, "key": "ram",      "name": "RAM" }]
#     }
#
# Fase 2 — con resolution:
#   {
#     "resolution": {
#       "remove_action": "eliminar",
#       "new_implementations": [{ "attr_id": 4, "value": "2 años" }]
#     }
#   }
#   → 200 { "status": "ok" }

@router.patch(
    "/products/{prod_id}/category/{new_cat_id}",
    response_model=ChangeCategoryImpactResponse | SuccessResponse,
)
def change_category(prod_id: int, new_cat_id: int, body: ChangeCategoryRequest = ChangeCategoryRequest()):
    product      = _get_product(prod_id)
    new_category = _get_category(new_cat_id)

    attr_ids_needed = (
        [ni.attr_id for ni in body.resolution.new_implementations]
        if body.resolution else []
    )
    attributes_by_id = {aid: _get_attribute(aid) for aid in attr_ids_needed}

    try:
        return prod_svc.change_category(product, new_category, body.resolution, attributes_by_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E7a — producto agrega variante ────────────────────────────────────────────
#
# POST /products/{id}/variants
#
# Sin two-phase. Valida completitud y unicidad internamente.
# 400 si falla alguna validacion.
#
# Body:
#   { "attribute_implementations": [{ "attr_id": 5, "value": "rojo" }, ...] }

@router.post("/products/{prod_id}/variants", response_model=SuccessResponse)
def add_variant(prod_id: int, body: AddVariantRequest):
    product = _get_product(prod_id)
    impls   = []
    for item in body.attribute_implementations:
        attr = _get_attribute(item.attr_id)
        impls.append(AttributeImplementation(attribute=attr, value=item.value))
    variant = Variant(attribute_implementations=impls)

    try:
        return prod_svc.add_variant(product, variant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── E7b — producto quita variante ─────────────────────────────────────────────
#
# DELETE /products/{id}/variants/{variant_id}
#
# 404 si la variante no existe.
# 400 si la variante no pertenece al producto.

@router.delete("/products/{prod_id}/variants/{var_id}", response_model=SuccessResponse)
def remove_variant(prod_id: int, var_id: int):
    product = _get_product(prod_id)
    variant = _get_variant(var_id)

    try:
        return prod_svc.remove_variant(product, variant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
