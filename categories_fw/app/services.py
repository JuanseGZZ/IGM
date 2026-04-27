from app.models import Attribute, AttributeImplementation, Category, Product, Variant
from app.schemas import (
    AttributeRef, ProductRef,
    ImpactGroup, ImpactResponse, SuccessResponse,
    ResolutionGroup, ResolutionAction,
    ChangeCategoryImpactResponse, ChangeCategoryResolution,
)


# ── Helpers internos ──────────────────────────────────────────────────────────

def _to_attr_ref(a: Attribute) -> AttributeRef:
    return AttributeRef(id=a.id, key=a.key, name=a.name)

def _to_prod_ref(p: Product) -> ProductRef:
    return ProductRef(id=p.id, code=p.code, title=p.title)

def _build_impact(pairs: list[tuple[set, list]]) -> list[ImpactGroup]:
    return [
        ImpactGroup(
            attrs=[_to_attr_ref(a) for a in attrs],
            products=[_to_prod_ref(p) for p in prods],
        )
        for attrs, prods in pairs
    ]

def _resolution_covers(resolution: list[ResolutionGroup], pairs: list[tuple[set, list]]) -> bool:
    """Verifica que la resolucion cubra cada par (attr_id, product_id) del impacto."""
    needed = {
        (a.id, p.id)
        for attrs, prods in pairs
        for a in attrs
        for p in prods
    }
    covered = {
        (attr_id, prod_id)
        for g in resolution
        for attr_id in g.attr_ids
        for prod_id in g.product_ids
    }
    return needed <= covered

def _apply_resolution(
    resolution: list[ResolutionGroup],
    products_by_id: dict[int, Product],
) -> None:
    for g in resolution:
        if g.action == ResolutionAction.heredar:
            continue  # mantener implementaciones como estan
        # eliminar: sacar las implementaciones de esos attrs en esos productos
        attr_ids = set(g.attr_ids)
        for prod_id in g.product_ids:
            prod = products_by_id.get(prod_id)
            if prod is None:
                continue
            prod.attributes_implementations = [
                impl for impl in prod.attributes_implementations
                if impl.attribute.id not in attr_ids
            ]
            prod._impl_keys = {i.attribute.key for i in prod.attributes_implementations}

def _apply_add_static_resolution(
    resolution: list[ResolutionGroup],
    products_by_id: dict[int, Product],
    attr: Attribute,
) -> None:
    for g in resolution:
        if g.action != ResolutionAction.asignar:
            continue
        for prod_id in g.product_ids:
            prod = products_by_id.get(prod_id)
            if prod is not None and g.value is not None:
                prod.attributes_implementations.append(
                    AttributeImplementation(attribute=attr, value=g.value)
                )
                prod._impl_keys = {i.attribute.key for i in prod.attributes_implementations}

def _apply_add_dynamic_resolution(
    resolution: list[ResolutionGroup],
    products_by_id: dict[int, Product],
) -> None:
    for g in resolution:
        if g.action == ResolutionAction.eliminar:
            for prod_id in g.product_ids:
                prod = products_by_id.get(prod_id)
                if prod is not None:
                    prod.variants = []


# ── CategoryService ───────────────────────────────────────────────────────────

class CategoryService:

    def change_father(
        self,
        category:        Category,
        new_father:      Category | None,
        resolution:      list[ResolutionGroup] | None,
        products_by_id:  dict[int, Product],
    ) -> ImpactResponse | SuccessResponse:
        """E1/E2/E3 segun el estado actual de category.father_categorie y new_father."""

        if new_father is not None:
            new_father._check_exclusive_children('subcategory')

        if new_father is None:
            pairs = category.impact_on_remove_father()
        elif category.father_categorie is None:
            pairs = category.impact_on_add_father(new_father)
        else:
            out, into = category.impact_on_change_father(new_father)
            pairs = out + into

        if not pairs:
            self._apply_father_change(category, new_father)
            return SuccessResponse()

        if resolution is None:
            return ImpactResponse(impact=_build_impact(pairs))

        if not _resolution_covers(resolution, pairs):
            return ImpactResponse(
                impact=_build_impact(pairs),
                message="La resolucion no cubre todos los productos impactados.",
            )

        _apply_resolution(resolution, products_by_id)
        self._apply_father_change(category, new_father)
        return SuccessResponse()

    def _apply_father_change(self, category: Category, new_father: Category | None) -> None:
        if category.father_categorie is not None:
            old = category.father_categorie
            old.subcategories = [s for s in old.subcategories if s is not category]
        category.set_father(new_father)
        if new_father is not None and category not in new_father.subcategories:
            new_father.subcategories.append(category)

    def add_attribute(
        self,
        category:       Category,
        attr:           Attribute,
        resolution:     list[ResolutionGroup] | None,
        products_by_id: dict[int, Product],
    ) -> ImpactResponse | SuccessResponse:
        """E4."""
        pairs = category.impact_on_add_attribute(attr)
        context = "add_static_attr" if attr.is_static else "add_dynamic_attr"

        if not pairs:
            category.attributes.append(attr)
            return SuccessResponse()

        if resolution is None:
            return ImpactResponse(impact=_build_impact(pairs), context=context)

        if not _resolution_covers(resolution, pairs):
            return ImpactResponse(
                impact=_build_impact(pairs),
                context=context,
                message="La resolucion no cubre todos los productos impactados.",
            )

        if attr.is_static:
            _apply_add_static_resolution(resolution, products_by_id, attr)
        else:
            _apply_add_dynamic_resolution(resolution, products_by_id)
        category.attributes.append(attr)
        return SuccessResponse()

    def remove_attribute(
        self,
        category:       Category,
        attr:           Attribute,
        resolution:     list[ResolutionGroup] | None,
        products_by_id: dict[int, Product],
    ) -> ImpactResponse | SuccessResponse:
        """E5."""
        pairs = category.impact_on_remove_attribute(attr)
        context = "remove_static_attr" if attr.is_static else "remove_dynamic_attr"

        if not pairs:
            category.attributes = [a for a in category.attributes if a.id != attr.id]
            return SuccessResponse()

        if resolution is None:
            return ImpactResponse(impact=_build_impact(pairs), context=context)

        if not _resolution_covers(resolution, pairs):
            return ImpactResponse(
                impact=_build_impact(pairs),
                context=context,
                message="La resolucion no cubre todos los productos impactados.",
            )

        if attr.is_static:
            _apply_resolution(resolution, products_by_id)
        else:
            _apply_add_dynamic_resolution(resolution, products_by_id)

        category.attributes = [a for a in category.attributes if a.id != attr.id]
        return SuccessResponse()


# ── ProductService ────────────────────────────────────────────────────────────

class ProductService:

    def change_category(
        self,
        product:        Product,
        new_category:   Category,
        resolution:     ChangeCategoryResolution | None,
        attributes_by_id: dict[int, Attribute],
    ) -> ChangeCategoryImpactResponse | SuccessResponse:
        """E6."""
        to_add, to_remove = product.impact_on_change_category(new_category)

        if not to_add and not to_remove:
            product.category = new_category
            return SuccessResponse()

        if resolution is None:
            return ChangeCategoryImpactResponse(
                to_add=[_to_attr_ref(a) for a in to_add],
                to_remove=[_to_attr_ref(a) for a in to_remove],
            )

        # Validar que new_implementations cubre exactamente los attrs de to_add
        provided_ids  = {i.attr_id for i in resolution.new_implementations}
        required_ids  = {a.id for a in to_add}
        missing_ids   = required_ids - provided_ids
        if missing_ids:
            return ChangeCategoryImpactResponse(
                to_add=[_to_attr_ref(a) for a in to_add],
                to_remove=[_to_attr_ref(a) for a in to_remove],
                message=f"Faltan implementaciones para attrs: {sorted(missing_ids)}",
            )

        # Aplicar to_remove segun la accion elegida
        if resolution.remove_action == ResolutionAction.eliminar:
            rm_ids = {a.id for a in to_remove}
            product.attributes_implementations = [
                impl for impl in product.attributes_implementations
                if impl.attribute.id not in rm_ids
            ]
            product._impl_keys = {i.attribute.key for i in product.attributes_implementations}
        # heredar: no hace nada, las implementaciones se mantienen

        # Agregar las nuevas implementaciones
        for ni in resolution.new_implementations:
            attr = attributes_by_id.get(ni.attr_id)
            if attr is None:
                continue
            product.attributes_implementations.append(
                AttributeImplementation(attribute=attr, value=ni.value)
            )
        product._impl_keys = {i.attribute.key for i in product.attributes_implementations}
        product.category = new_category
        return SuccessResponse()

    def add_variant(self, product: Product, variant: Variant) -> SuccessResponse:
        """E7a — lanza ValueError si la variante es invalida o duplicada."""
        product.add_variant(variant)
        return SuccessResponse()

    def remove_variant(self, product: Product, variant: Variant) -> SuccessResponse:
        """E7b — lanza ValueError si la variante no pertenece al producto."""
        product.remove_variant(variant)
        return SuccessResponse()
