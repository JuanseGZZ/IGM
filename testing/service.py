import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models import Category, Product, Variant, Attribute, AttributeImplementation
import repository as repo


def load_catalog() -> dict:
    """Carga el estado completo desde la DB."""
    return repo.get_full_state()


def validate_and_apply(payload) -> dict:
    """
    Construye el árbol completo en memoria usando models.py.
    Cada mutación pasa por los métodos validados del modelo.
    Si todo es válido → persiste. Si hay error → retorna ubicación, no persiste nada.
    """
    # 1. Construir registry de atributos desde el payload
    attr_by_id:  dict[int, Attribute] = {}
    attr_by_key: dict[str, Attribute] = {}

    for a in payload.attributes:
        attr = Attribute(
            key=a.key,
            name=a.name,
            data_type=a.data_type,
            id=a.id,
            is_static=a.is_static,
        )
        attr.enum_values = list(a.enum_values)
        attr_by_id[a.id]   = attr
        attr_by_key[a.key] = attr

    # 2. Construir árbol top-down en memoria
    try:
        root = _build_category(payload.tree, attr_by_id, attr_by_key, location="raíz")
    except ValueError as e:
        return {"valid": False, "error": str(e)}

    # 3. Persistir solo si todo fue válido
    repo.save_full_state(list(attr_by_key.values()), root)
    return {"valid": True}


def _build_category(
    data,
    attr_by_id: dict,
    attr_by_key: dict,
    location: str,
) -> Category:
    cat = Category(name=data.name, id=data.id)

    # Asignar atributos propios de la categoría
    for aid in data.attribute_ids:
        if aid not in attr_by_id:
            raise ValueError(f"[{location}] Atributo id={aid} no encontrado en el payload")
        cat.attributes.append(attr_by_id[aid])

    # Construir subcategorías primero (el modelo las valida contra R1 y R3)
    for sub_data in data.subcategories:
        loc = f"{location} → categoría '{sub_data.name}'"
        sub = _build_category(sub_data, attr_by_id, attr_by_key, loc)  # propaga su propio error
        try:
            cat.add_subcategory(sub)
        except ValueError as e:
            raise ValueError(f"[{loc}] {e}") from None

    # Construir productos (el modelo los valida contra R2 y R13)
    for prod_data in data.products:
        loc = f"{location} → producto '{prod_data.code}'"
        prod = _build_product(prod_data, attr_by_key, cat, loc)  # propaga su propio error
        try:
            cat.add_product(prod)
        except ValueError as e:
            raise ValueError(f"[{loc}] {e}") from None

    return cat


def _build_product(
    data,
    attr_by_key: dict,
    cat: Category,
    location: str,
) -> Product:
    # Implementaciones estáticas del producto
    impls = []
    for ai in data.attributes_implementations:
        if ai.attribute_key not in attr_by_key:
            raise ValueError(f"[{location}] Atributo '{ai.attribute_key}' no encontrado")
        impls.append(AttributeImplementation(
            attribute=attr_by_key[ai.attribute_key],
            value=ai.value,
        ))

    prod = Product(
        code=data.code,
        title=data.title,
        price=data.price,
        description=data.description,
        brand=data.brand,
        id=data.id,
        category=cat,
        attributes_implementations=impls,
    )

    # Variantes (el modelo las valida contra R13b, R14, R15)
    for var_data in data.variants:
        loc = f"{location} → variante id={var_data.id}"
        var_impls = []
        for ai in var_data.attribute_implementations:
            if ai.attribute_key not in attr_by_key:
                raise ValueError(f"[{loc}] Atributo '{ai.attribute_key}' no encontrado")
            var_impls.append(AttributeImplementation(
                attribute=attr_by_key[ai.attribute_key],
                value=ai.value,
            ))
        var = Variant(id=var_data.id, attribute_implementations=var_impls)
        try:
            prod.add_variant(var)
        except ValueError as e:
            raise ValueError(f"[{loc}] {e}") from None

    return prod
