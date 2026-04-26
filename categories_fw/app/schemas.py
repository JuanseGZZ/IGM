from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel


# ── Refs (lo minimo para identificar objetos en respuestas) ───────────────────

class AttributeRef(BaseModel):
    id: int
    key: str
    name: str

class ProductRef(BaseModel):
    id: int
    code: str
    title: str


# ── Impacto ───────────────────────────────────────────────────────────────────

class ImpactGroup(BaseModel):
    """Un conjunto de atributos que impacta a un conjunto de productos."""
    attrs:    list[AttributeRef]
    products: list[ProductRef]

class ResolutionAction(str, Enum):
    eliminar = "eliminar"   # quitar las implementaciones de esos attrs en esos productos
    heredar  = "heredar"    # mantener las implementaciones tal como estan (no hacer nada)

class ResolutionGroup(BaseModel):
    """Decision del llamador sobre un grupo de impacto."""
    attr_ids:    list[int]
    product_ids: list[int]
    action:      ResolutionAction


# ── Respuestas comunes ────────────────────────────────────────────────────────

class ImpactResponse(BaseModel):
    """Fase 1: hay impacto que resolver antes de ejecutar."""
    status:  Literal["impact_pending"] = "impact_pending"
    impact:  list[ImpactGroup]
    message: str | None = None

class SuccessResponse(BaseModel):
    """Fase 2: directiva ejecutada correctamente."""
    status: Literal["ok"] = "ok"


# ── E1/E2/E3 — categoria cambia padre ─────────────────────────────────────────
# PATCH /categories/{id}/father
# Body sin resolution → responde ImpactResponse
# Body con resolution valida → responde SuccessResponse

class ChangeFatherRequest(BaseModel):
    new_father_id: int | None                    # None = eliminar padre (E3)
    resolution:    list[ResolutionGroup] | None = None


# ── E4 — categoria agrega atributo ────────────────────────────────────────────
# POST /categories/{id}/attributes/{attr_id}
# Sin resolution → ImpactResponse   |   Con resolution → SuccessResponse

class AddAttributeRequest(BaseModel):
    resolution: list[ResolutionGroup] | None = None


# ── E5 — categoria elimina atributo ───────────────────────────────────────────
# DELETE /categories/{id}/attributes/{attr_id}
# Sin resolution → ImpactResponse   |   Con resolution → SuccessResponse

class RemoveAttributeRequest(BaseModel):
    resolution: list[ResolutionGroup] | None = None


# ── E6 — producto cambia de categoria ─────────────────────────────────────────
# PATCH /products/{id}/category/{new_category_id}
#
# Fase 1 devuelve:
#   to_remove: attrs que el producto implementa pero la nueva cat no exige
#   to_add:    attrs que la nueva cat exige pero el producto no implementa
#
# Fase 2 requiere resolution para to_remove + implementaciones nuevas para to_add.

class NewImplementation(BaseModel):
    attr_id: int
    value:   str

class ChangeCategoryResolution(BaseModel):
    remove_action:       ResolutionAction         # aplica a todos los attrs de to_remove
    new_implementations: list[NewImplementation]  # valores para los attrs de to_add

class ChangeCategoryImpactResponse(BaseModel):
    status:    Literal["impact_pending"] = "impact_pending"
    to_add:    list[AttributeRef]
    to_remove: list[AttributeRef]
    message:   str | None = None

class ChangeCategoryRequest(BaseModel):
    resolution: ChangeCategoryResolution | None = None


# ── E7a — producto agrega variante ────────────────────────────────────────────
# POST /products/{id}/variants
# Sin two-phase: valida internamente (completitud + unicidad), 400 si falla.

class VariantImplInput(BaseModel):
    attr_id: int
    value:   str

class AddVariantRequest(BaseModel):
    attribute_implementations: list[VariantImplInput]


# ── E7b — producto quita variante ─────────────────────────────────────────────
# DELETE /products/{id}/variants/{variant_id}
# Sin two-phase: solo elimina, 404 si no existe.
