"""
service.py — Capa de servicio.

Recibe datos planos, opera sobre los modelos en memoria usando la lógica de
acciones_reglas_negocio.md, persiste los cambios con los repos y retorna objetos
del modelo o dicts de resultado.

Convenciones de retorno:
  - Objeto del modelo         → operación exitosa directa.
  - {"needs_implementations": True, "impact": [...]}  → el cliente debe proveer
      implementaciones para completar la operación.
  - {"needs_decision": True, "impact": [...]}         → el cliente debe elegir
      del_opt para continuar (solo en del_attribute con del_opt=0).
  - ValueError                → violación de regla de negocio o entidad no encontrada.
"""

from models import Attribute, AttributeImplementation, Category, Variant, Product
from attributes_repo import AttributeRepo
from category_repo import CategoryRepo
from product_repo import ProductRepo


# ─── helpers internos ───────────────────────────────────────────────────────

def _impact_dynamic(products: list) -> list[dict]:
    """Impacto de atributo dinámico: qué variantes necesitan valor."""
    return [
        {
            "product_id": p.id,
            "product_code": p.code,
            "variants": [{"variant_id": v.id} for v in p.variants],
        }
        for p in products
    ]

def _impact_static(products: list) -> list[dict]:
    """Impacto de atributo estático: qué productos necesitan valor."""
    return [{"product_id": p.id, "product_code": p.code} for p in products]

def _require_cat(cat_id: int) -> Category:
    cat = CategoryRepo.read(cat_id)
    if cat is None:
        raise ValueError(f"Categoría {cat_id} no encontrada")
    return cat

def _require_prod(prod_id: int) -> Product:
    prod = ProductRepo.read(prod_id)
    if prod is None:
        raise ValueError(f"Producto {prod_id} no encontrado")
    return prod

def _require_attr(attr_id: int) -> Attribute:
    attr = AttributeRepo.read(attr_id)
    if attr is None:
        raise ValueError(f"Atributo {attr_id} no encontrado")
    return attr


# ─── AttributeService ───────────────────────────────────────────────────────

class AttributeService:

    @staticmethod
    def create(key: str, name: str, data_type: str, is_static: bool,
               enum_values: list[str] = None) -> Attribute:
        attr = Attribute(key=key, name=name, data_type=data_type, is_static=is_static)
        for v in (enum_values or []):
            attr.add_enum_value(v)
        return AttributeRepo.save(attr)

    @staticmethod
    def get(attr_id: int) -> Attribute | None:
        return AttributeRepo.read(attr_id)

    @staticmethod
    def get_all() -> list[Attribute]:
        return AttributeRepo.bring_all()

    @staticmethod
    def update(attr_id: int, name: str = None,
               enum_values: list[str] = None) -> Attribute | None:
        attr = AttributeRepo.read(attr_id)
        if attr is None:
            return None
        if name is not None:
            attr.name = name
        if enum_values is not None:
            attr.enum_values = list(enum_values)
        return AttributeRepo.save(attr)

    @staticmethod
    def delete(attr_id: int) -> bool:
        return AttributeRepo.delete(attr_id)

    @staticmethod
    def add_enum_value(attr_id: int, value: str) -> Attribute | None:
        attr = AttributeRepo.read(attr_id)
        if attr is None:
            return None
        attr.add_enum_value(value)   # ValueError si no es enum o ya existe
        return AttributeRepo.save(attr)


# ─── CategoryService ─────────────────────────────────────────────────────────

class CategoryService:

    @staticmethod
    def create(name: str) -> Category:
        return CategoryRepo.save(Category(name=name))

    @staticmethod
    def get(cat_id: int) -> Category | None:
        return CategoryRepo.read(cat_id)

    @staticmethod
    def get_all() -> list[Category]:
        return CategoryRepo.bring_all()

    @staticmethod
    def update_name(cat_id: int, name: str) -> Category | None:
        cat = CategoryRepo.read(cat_id)
        if cat is None:
            return None
        cat.name = name
        return CategoryRepo.save(cat)

    @staticmethod
    def change_parent(cat_id: int, parent_id: int,
                      implementations: dict = None, del_opt: int = 0) -> dict:
        """
        Cambia el padre de la categoría.

        implementations: {attr_key: [{"product_id": id, "value": val}]
                         | [{"product_id": id, "variants": [{"variant_id": id, "value": val}]}]}

        del_opt 0 → si hay atributos huérfanos del padre anterior, retorna needs_decision.
        del_opt 1 → inyecta los atributos huérfanos en la categoría.
        del_opt 2 → elimina las implementaciones huérfanas de los productos afectados.
        """
        cat        = _require_cat(cat_id)
        new_parent = _require_cat(parent_id)

        # Verificar que no se crea un ciclo (nuevo padre no puede ser el mismo ni
        # un descendiente de la categoría que se está moviendo)
        if new_parent.id == cat_id:
            raise ValueError("Una categoría no puede ser su propio padre")
        ancestor = new_parent.father_categorie
        while ancestor is not None:
            if ancestor.id == cat_id:
                raise ValueError(
                    "No se puede asignar un descendiente como padre: crearía un ciclo"
                )
            ancestor = ancestor.father_categorie

        # Convierte formato API → formato esperado por el modelo
        model_impls: dict = {}
        for attr_key, entries in (implementations or {}).items():
            model_impls[attr_key] = [
                (e["product_id"], e["variants"]) if "variants" in e
                else (e["product_id"], e["value"])
                for e in entries
            ]

        result = cat.change_categorie_father(new_parent, model_impls, del_opt)

        if result:  # dict no vacío → requiere acción del cliente
            new_parent_attr_keys = {a.key for a in new_parent.get_attributes()}
            is_impl_impact = (
                del_opt != 0
                or {a.key for a in result}.issubset(new_parent_attr_keys)
            )

            if is_impl_impact:
                # Atributos del nuevo padre que necesitan implementations
                impact = []
                for attr, val in result.items():
                    entry = {
                        "attribute_key":  attr.key,
                        "attribute_name": attr.name,
                        "is_static":      attr.is_static,
                    }
                    if attr.is_static:
                        entry["products"] = [
                            {"product_id": p.id, "product_code": p.code}
                            for p in val
                        ]
                    else:
                        entry["products"] = [
                            {
                                "product_id":   p.id,
                                "product_code": p.code,
                                "variants":     [{"variant_id": s["variant_id"]} for s in slots],
                            }
                            for p, slots in val
                        ]
                    impact.append(entry)
                return {"needs_implementations": True, "impact": impact}
            else:
                # Atributos huérfanos del padre anterior — cliente elige del_opt
                return {
                    "needs_decision": True,
                    "impact": [
                        {
                            "attribute_key":   a.key,
                            "attribute_name":  a.name,
                            "is_static":       a.is_static,
                            "affected_products": [
                                {"product_id": p.id, "product_code": p.code}
                                for p in prods
                            ],
                        }
                        for a, prods in result.items()
                    ],
                }

        # Éxito — guardar productos afectados en el subárbol y luego la categoría
        def _products_in_tree(c):
            items = list(c.products)
            for sub in c.subcategories:
                items.extend(_products_in_tree(sub))
            return items

        for prod in _products_in_tree(cat):
            ProductRepo.save(prod)

        return {"category": CategoryRepo.save(cat)}

    @staticmethod
    def delete(cat_id: int) -> bool:
        return CategoryRepo.delete(cat_id)

    @staticmethod
    def add_dynamic_attribute(
        cat_id: int,
        attr_id: int,
        product_variant_implementations: list[dict] | None = None,
    ) -> dict:
        """
        Agrega atributo dinámico a la categoría.
        Si hay productos impactados sin implementations → retorna needs_implementations.

        product_variant_implementations:
            [{"product_id": id, "variants": [{"variant_id": id, "value": val}]}]
        """
        cat  = _require_cat(cat_id)
        attr = _require_attr(attr_id)

        result = cat.add_dinamic_attribute(attr, product_variant_implementations or [])

        if isinstance(result, list) and result:
            # validación fallida: necesita implementations para los productos en riesgo
            return {"needs_implementations": True, "impact": _impact_dynamic(result)}

        # éxito: guardar productos afectados primero, luego la categoría
        if product_variant_implementations:
            affected_ids = {e["product_id"] for e in product_variant_implementations}
            for prod in cat.products:
                if prod.id in affected_ids:
                    ProductRepo.save(prod)

        return {"needs_implementations": False, "category": CategoryRepo.save(cat)}

    @staticmethod
    def add_static_attribute(
        cat_id: int,
        attr_id: int,
        implementations: list[dict] | None = None,
    ) -> dict:
        """
        Agrega atributo estático a la categoría.
        implementations: [{"product_id": id, "value": value}]
        """
        cat  = _require_cat(cat_id)
        attr = _require_attr(attr_id)

        result = cat.add_static_attribute(attr, implementations or [])

        if isinstance(result, list) and result:
            return {"needs_implementations": True, "impact": _impact_static(result)}

        if implementations:
            affected_ids = {e["product_id"] for e in implementations}
            for prod in cat.products:
                if prod.id in affected_ids:
                    ProductRepo.save(prod)

        return {"needs_implementations": False, "category": CategoryRepo.save(cat)}

    @staticmethod
    def del_attribute(cat_id: int, attr_id: int, del_opt: int = 0) -> dict:
        """
        Elimina atributo de la categoría.
        del_opt 0 → reporta impacto sin modificar.
        del_opt 1 → elimina implementaciones huérfanas.
        del_opt 2 → inyecta el atributo en los productos afectados.
        """
        cat  = _require_cat(cat_id)
        attr = _require_attr(attr_id)

        # capturamos impactados antes de la operación (read-only)
        impacted = cat.del_attribute_check_family_impact(attr)
        result   = cat.del_attribute(attr, del_opt)

        if result:
            # del_opt=0 con impacto: nada fue modificado
            return {"needs_decision": True, "impact": _impact_static(result)}

        for prod in impacted:
            ProductRepo.save(prod)
        return {"needs_decision": False, "category": CategoryRepo.save(cat)}

    @staticmethod
    def add_product_to_category(cat_id: int, product_id: int) -> Product:
        """
        Reasigna el producto a esta categoría actualizando product.category_id.
        """
        cat  = _require_cat(cat_id)
        prod = _require_prod(product_id)
        if len(cat.subcategories) > 0:
            raise ValueError("La categoría tiene subcategorías; no puede tener productos directos")
        prod.category = cat
        return ProductRepo.save(prod)


# ─── ProductService ──────────────────────────────────────────────────────────

class ProductService:

    @staticmethod
    def create(code: str, title: str, price: float, description: str,
               brand: str, category_id: int) -> Product:
        cat  = _require_cat(category_id)
        prod = Product(code=code, title=title, price=price,
                       description=description, brand=brand, category=cat)
        return ProductRepo.save(prod)

    @staticmethod
    def get(prod_id: int) -> Product | None:
        return ProductRepo.read(prod_id)

    @staticmethod
    def get_by_code(code: str) -> Product | None:
        return ProductRepo.read_by_code(code)

    @staticmethod
    def get_all() -> list[Product]:
        return ProductRepo.bring_all()

    @staticmethod
    def update(prod_id: int, title: str = None, price: float = None,
               description: str = None, brand: str = None,
               category_id: int = None) -> Product | None:
        prod = ProductRepo.read(prod_id)
        if prod is None:
            return None
        if title       is not None: prod.title       = title
        if price       is not None: prod.price       = price
        if description is not None: prod.description = description
        if brand       is not None: prod.brand       = brand
        if category_id is not None:
            prod.category = _require_cat(category_id)
        return ProductRepo.save(prod)

    @staticmethod
    def delete(prod_id: int) -> bool:
        return ProductRepo.delete(prod_id)

    @staticmethod
    def add_dynamic_attribute(
        prod_id: int,
        attr_id: int,
        variant_options: list[dict] | None = None,
    ) -> dict:
        """
        Agrega atributo dinámico al producto.
        variant_options: [{"variant_id": id, "value": value}]
        Si el producto tiene variantes y no se proveen options → retorna needs_implementations.
        """
        prod = _require_prod(prod_id)
        attr = _require_attr(attr_id)

        if variant_options is None and prod.variants:
            return {
                "needs_implementations": True,
                "impact": [{"variant_id": v.id} for v in prod.variants],
            }

        result = prod.add_dinamic_attribute(attr, variant_options or [])

        if result is False:
            return {
                "needs_implementations": True,
                "impact": [{"variant_id": v.id} for v in prod.variants],
            }

        return {"needs_implementations": False, "product": ProductRepo.save(prod)}

    @staticmethod
    def add_implementation(prod_id: int, attr_id: int, value) -> Product:
        """
        Agrega implementación de atributo estático directamente al producto.
        El atributo debe estar suscripto (en la categoría o en product.attributes).
        """
        prod = _require_prod(prod_id)
        attr = _require_attr(attr_id)
        impl = AttributeImplementation(attribute=attr, value=value)
        prod.add_product_implementation(impl)   # ValueError si inválido o duplicado
        return ProductRepo.save(prod)

    @staticmethod
    def del_own_attribute(prod_id: int, attr_key: str, del_opt: int = 0) -> dict:
        """
        Elimina atributo propio del producto.
        del_opt 0 → reporta impacto sin modificar.
        del_opt 1 → elimina implementaciones huérfanas.
        """
        prod = _require_prod(prod_id)

        attr = next((a for a in prod.attributes if a.key == attr_key), None)
        if attr is None:
            raise ValueError(f"Atributo '{attr_key}' no está en los atributos propios del producto")

        result = prod.del_attribute(attr, del_opt)

        if result is False:
            raise ValueError(f"Atributo '{attr_key}' no encontrado")

        if result:
            # del_opt=0 con impacto
            if result and hasattr(result[0], "attribute"):
                impact = [i.to_json() for i in result]      # AttributeImplementation
            else:
                impact = [v.to_json() for v in result]      # Variant
            return {"needs_decision": True, "impact": impact}

        return {"needs_decision": False, "product": ProductRepo.save(prod)}

    @staticmethod
    def create_variant(prod_id: int, implementations: list[dict]) -> dict:
        """
        Crea una variante para el producto.
        implementations: [{"attribute_id": id, "value": value}]
        Si las implementations no matchean → retorna atributos necesarios.
        """
        prod = _require_prod(prod_id)

        impls = []
        for item in implementations:
            attr = _require_attr(item["attribute_id"])
            impls.append(AttributeImplementation(attribute=attr, value=item["value"]))

        before = len(prod.variants)
        prod.create_variant_by_implementations(impls)

        if len(prod.variants) == before:
            # no se agregó → validación fallida
            needed = prod.get_needed_atributes_implementations(is_static=False)
            return {
                "error": "implementations_invalid",
                "needed_attributes": [a.to_json() for a in needed],
            }

        return {"product": ProductRepo.save(prod)}

    @staticmethod
    def del_variant(prod_id: int, variant_id: int) -> Product:
        prod = _require_prod(prod_id)
        removed = prod.del_variant(variant_id)
        if not removed:
            raise ValueError(f"Variante {variant_id} no encontrada en el producto")
        return ProductRepo.save(prod)
