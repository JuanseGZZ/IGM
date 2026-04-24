"""
tests_models.py — Cobertura completa de acciones y reglas de negocio definidas en
igm-documentation/igm-models_doc/acciones_reglas_negocio.md

Cada clase corresponde a una acción del documento. Los números de sección
coinciden con los del índice del documento.

Para correr: pytest TestingConcepts/app/tests_models.py -v
"""

import pytest
from models import (
    Attribute,
    Attribute_factory,
    AttributeImplementation,
    Category,
    Variant,
    Product,
)


# ─── helpers de construcción ────────────────────────────────────────────────

def mk_attr(key, data_type="text", is_static=True, name=None):
    return Attribute(key=key, name=name or key, data_type=data_type, is_static=is_static)

def mk_enum_attr(key, values, is_static=True):
    a = Attribute(key=key, name=key, data_type="enum", is_static=is_static)
    a.enum_values = list(values)
    return a

def mk_cat(name="Cat", id=None):
    return Category(name=name, id=id)

def mk_prod(code, cat, id=None):
    return Product(
        code=code, title=code, price=1.0,
        description="", brand="B",
        id=id, category=cat,
    )

def mk_variant(id):
    return Variant(id=id)

def mk_impl(attribute, value):
    return AttributeImplementation(attribute=attribute, value=value)

def cat_add_product(cat, prod):
    """Agrega producto a categoría actualizando cache."""
    cat.products.append(prod)
    cat._product_codes.add(prod.code)

def cat_add_attr(cat, attr):
    """Agrega atributo a categoría actualizando cache."""
    cat.attributes.append(attr)
    cat._attribute_keys.add(attr.key)

def cat_add_subcat(parent, child):
    """Vincula subcategoría actualizando referencias."""
    parent.subcategories.append(child)
    child.father_categorie = parent

def prod_add_attr(prod, attr):
    """Agrega atributo propio al producto actualizando cache."""
    prod.attributes.append(attr)
    prod._attribute_keys.add(attr.key)

def prod_add_static_impl(prod, impl_obj):
    """Agrega implementación estática al producto actualizando cache."""
    prod.attributes_implementations.append(impl_obj)
    prod._impl_keys.add(impl_obj.attribute.key)

def prod_add_dynamic_impl_to_variant(variant, attr, value):
    """Agrega implementación dinámica a una variante."""
    variant.attribute_implementations.append(mk_impl(attr, value))


# ═══════════════════════════════════════════════════════════════════════════
# 1. Attribute.add_enum_value
# ═══════════════════════════════════════════════════════════════════════════

class TestAttributeAddEnumValue:
    """Sección 1 — Attribute.add_enum_value"""

    def test_atributo_no_es_enum_lanza_valueerror(self):
        a = mk_attr("color", data_type="text")
        with pytest.raises(ValueError):
            a.add_enum_value("rojo")

    def test_atributo_boolean_no_es_enum_lanza_valueerror(self):
        a = mk_attr("activo", data_type="boolean")
        with pytest.raises(ValueError):
            a.add_enum_value(True)

    def test_valor_ya_existe_lanza_valueerror(self):
        a = mk_enum_attr("talle", ["S", "M"])
        with pytest.raises(ValueError):
            a.add_enum_value("S")

    def test_valor_nuevo_se_agrega(self):
        a = mk_enum_attr("talle", ["S", "M"])
        a.add_enum_value("L")
        assert "L" in a.enum_values

    def test_primer_valor_en_lista_vacia(self):
        a = mk_attr("talle", data_type="enum")
        a.add_enum_value("XL")
        assert a.enum_values == ["XL"]


# ═══════════════════════════════════════════════════════════════════════════
# 2. Category.add_dinamic_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddDinamicAttribute:
    """Sección 2 — Category.add_dinamic_attribute"""

    def test_atributo_estatico_lanza_valueerror(self):
        cat = mk_cat()
        a = mk_attr("color", is_static=True)
        with pytest.raises(ValueError):
            cat.add_dinamic_attribute(a, [])

    # ── Escenario A — ancestro ya lo tiene ──────────────────────────────

    def test_escA_ancestro_tiene_atributo_retorna_vacio(self):
        a = mk_attr("color", data_type="text", is_static=False)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_subcat(parent, child)

        result = child.add_dinamic_attribute(a, [])

        assert result == {}
        assert a not in child.attributes  # no duplica en el hijo

    def test_escA_ancestro_en_cadena_larga_retorna_vacio(self):
        a = mk_attr("color", data_type="text", is_static=False)
        root = mk_cat("Root")
        cat_add_attr(root, a)
        mid = mk_cat("Mid")
        cat_add_subcat(root, mid)
        leaf = mk_cat("Leaf")
        cat_add_subcat(mid, leaf)

        result = leaf.add_dinamic_attribute(a, [])
        assert result == {}

    # ── Escenario B — sin productos impactados ───────────────────────────

    def test_escB_sin_hijos_agrega_atributo(self):
        cat = mk_cat()
        a = mk_attr("color", data_type="text", is_static=False)

        result = cat.add_dinamic_attribute(a, [])

        assert result == {}
        assert a in cat.attributes

    def test_escB_productos_ya_tienen_atributo_propio(self):
        """Todos los productos descendientes ya poseen el attr → sin impacto."""
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)          # el producto ya lo tiene
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [])

        assert result == {}
        assert a in cat.attributes

    # ── Escenario C — hay productos impactados ───────────────────────────

    def test_escC_falta_producto_en_lista(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [])  # lista vacía → falta el producto

        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes   # sin modificación

    def test_escC_sobra_producto_en_lista(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]},
            {"product_id": 99, "variants": []},   # producto que no existe en riesgo
        ])
        assert isinstance(result, list)
        assert a not in cat.attributes

    def test_escC_product_id_duplicado(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]},
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "azul"}]},
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_falta_variante_en_producto(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v1 = mk_variant(id=10)
        v2 = mk_variant(id=11)
        p.variants.extend([v1, v2])
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]},
            # variante 11 falta
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_variant_id_duplicado(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [
                {"variant_id": 10, "value": "rojo"},
                {"variant_id": 10, "value": "azul"},
            ]},
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_valor_invalido(self):
        a = mk_attr("size", data_type="number", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "no_es_numero"}]},
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_cobertura_exacta_valores_validos(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]},
        ])
        assert result == {}
        assert a in cat.attributes
        assert any(i.attribute.key == "color" for i in v.attribute_implementations)

    def test_escC_dos_productos_cobertura_exacta(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        p1 = mk_prod("P1", cat, id=1)
        p2 = mk_prod("P2", cat, id=2)
        v1 = mk_variant(id=10)
        v2 = mk_variant(id=20)
        p1.variants.append(v1)
        p2.variants.append(v2)
        cat_add_product(cat, p1)
        cat_add_product(cat, p2)

        result = cat.add_dinamic_attribute(a, [
            {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]},
            {"product_id": 2, "variants": [{"variant_id": 20, "value": "azul"}]},
        ])
        assert result == {}
        assert a in cat.attributes
        assert any(i.attribute.key == "color" for i in v1.attribute_implementations)
        assert any(i.attribute.key == "color" for i in v2.attribute_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Category.add_static_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddStaticAttribute:
    """Sección 3 — Category.add_static_attribute"""

    def test_atributo_dinamico_lanza_valueerror(self):
        cat = mk_cat()
        a = mk_attr("peso", is_static=False)
        with pytest.raises(ValueError):
            cat.add_static_attribute(a, [])

    # ── Escenario A ──────────────────────────────────────────────────────

    def test_escA_ancestro_tiene_atributo_retorna_vacio(self):
        a = mk_attr("peso", is_static=True)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_subcat(parent, child)

        result = child.add_static_attribute(a, [])
        assert result == {}
        assert a not in child.attributes

    # ── Escenario B ──────────────────────────────────────────────────────

    def test_escB_sin_productos_agrega_atributo(self):
        cat = mk_cat()
        a = mk_attr("peso", is_static=True)

        result = cat.add_static_attribute(a, [])

        assert result == {}
        assert a in cat.attributes

    def test_escB_todos_los_productos_tienen_atributo_propio(self):
        a = mk_attr("peso", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [])
        assert result == {}
        assert a in cat.attributes

    # ── Escenario C ──────────────────────────────────────────────────────

    def test_escC_falta_producto_en_lista(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [])

        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_sobra_producto_en_lista(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [
            {"product_id": 1, "value": 500},
            {"product_id": 99, "value": 300},  # id inexistente
        ])
        assert isinstance(result, list)
        assert a not in cat.attributes

    def test_escC_product_id_duplicado(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [
            {"product_id": 1, "value": 500},
            {"product_id": 1, "value": 300},
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_valor_invalido(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [
            {"product_id": 1, "value": "no_es_numero"},
        ])
        assert isinstance(result, list)
        assert p in result
        assert a not in cat.attributes

    def test_escC_cobertura_exacta_valores_validos(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.add_static_attribute(a, [
            {"product_id": 1, "value": 500},
        ])
        assert result == {}
        assert a in cat.attributes
        assert any(i.attribute.key == "peso" for i in p.attributes_implementations)

    def test_escC_dos_productos_cobertura_exacta(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        p1 = mk_prod("P1", cat, id=1)
        p2 = mk_prod("P2", cat, id=2)
        cat_add_product(cat, p1)
        cat_add_product(cat, p2)

        result = cat.add_static_attribute(a, [
            {"product_id": 1, "value": 500},
            {"product_id": 2, "value": 200},
        ])
        assert result == {}
        assert a in cat.attributes
        assert any(i.value == 500 for i in p1.attributes_implementations)
        assert any(i.value == 200 for i in p2.attributes_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Category.del_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryDelAttribute:
    """Sección 4 — Category.del_attribute"""

    # ── sin productos en riesgo ──────────────────────────────────────────

    def test_sin_hijos_elimina_atributo(self):
        a = mk_attr("peso", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)

        result = cat.del_attribute(a)

        assert result == []
        assert a not in cat.attributes
        assert "peso" not in cat._attribute_keys

    def test_ancestro_cubre_no_hay_riesgo(self):
        """Ancestro ya tiene el attr → nadie queda sin cobertura → elimina."""
        a = mk_attr("peso", is_static=True)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = child.del_attribute(a)
        assert result == []
        assert a not in child.attributes

    def test_producto_tiene_atributo_propio_no_hay_riesgo(self):
        """Producto tiene el attr como propio → no queda en riesgo."""
        a = mk_attr("peso", is_static=True)
        cat = mk_cat("Cat", id=1)
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)   # producto lo tiene propio
        cat_add_product(cat, p)

        result = cat.del_attribute(a)
        assert result == []
        assert a not in cat.attributes

    def test_subcategoria_tiene_atributo_propio_corta_busqueda(self):
        """Subcategoría tiene el attr propio → no propaga riesgo hacia abajo."""
        a = mk_attr("peso", is_static=True)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_attr(child, a)   # child lo tiene propio → corta
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = parent.del_attribute(a)
        assert result == []
        assert a not in parent.attributes

    # ── delete_opt=0 (default) ───────────────────────────────────────────

    def test_opt0_hay_riesgo_retorna_lista_sin_modificar(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)
        cat_add_product(cat, p)

        result = cat.del_attribute(a, delete_opt=0)

        assert isinstance(result, list) and len(result) > 0
        assert p in result
        assert a in cat.attributes        # sin modificación

    # ── delete_opt=1 ────────────────────────────────────────────────────

    def test_opt1_estatico_elimina_implementaciones(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)
        cat_add_product(cat, p)

        result = cat.del_attribute(a, delete_opt=1)

        assert result == []
        assert a not in cat.attributes
        assert not any(i.attribute.key == "peso" for i in p.attributes_implementations)
        assert "peso" not in p._impl_keys

    def test_opt1_dinamico_elimina_implementaciones_de_variantes(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat("Cat", id=1)
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)
        cat_add_product(cat, p)

        result = cat.del_attribute(a, delete_opt=1)

        assert result == []
        assert a not in cat.attributes
        assert not any(i.attribute.key == "color" for i in v.attribute_implementations)

    # ── delete_opt=2 ────────────────────────────────────────────────────

    def test_opt2_inyecta_atributo_en_productos(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat("Cat", id=1)
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)
        cat_add_product(cat, p)

        result = cat.del_attribute(a, delete_opt=2)

        assert result == []
        assert a not in cat.attributes
        assert a in p.attributes      # inyectado en el producto
        # implementaciones se mantienen
        assert any(i.attribute.key == "peso" for i in p.attributes_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 5. Category.change_categorie_father
# ═══════════════════════════════════════════════════════════════════════════

class TestChangeCategorieFather:
    """Sección 5 — Category.change_categorie_father"""

    # ── condiciones previas ──────────────────────────────────────────────

    def test_nuevo_padre_tiene_productos_lanza_valueerror(self):
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        new_parent = mk_cat("NewParent")
        p = mk_prod("P1", new_parent, id=1)
        cat_add_product(new_parent, p)

        with pytest.raises(ValueError):
            child.change_categorie_father(new_parent, {})

    def test_ciclo_directo_lanza_valueerror(self):
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_subcat(parent, child)

        with pytest.raises(ValueError):
            parent.change_categorie_father(child, {})

    def test_ciclo_indirecto_lanza_valueerror(self):
        root = mk_cat("Root")
        mid = mk_cat("Mid")
        leaf = mk_cat("Leaf")
        cat_add_subcat(root, mid)
        cat_add_subcat(mid, leaf)

        with pytest.raises(ValueError):
            root.change_categorie_father(leaf, {})

    # ── del_option con atributos huérfanos ───────────────────────────────

    def _setup_orphan(self, key="peso"):
        """Devuelve (orphan_attr, old_parent, child, product, new_parent)."""
        orphan = mk_attr(key, data_type="number", is_static=True)
        old_parent = mk_cat("OldParent")
        cat_add_attr(old_parent, orphan)

        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)

        p = mk_prod("P1", child, id=1)
        impl_obj = mk_impl(orphan, 500)
        prod_add_static_impl(p, impl_obj)
        cat_add_product(child, p)

        new_parent = mk_cat("NewParent")
        return orphan, old_parent, child, p, new_parent

    def test_del_option_0_impacto_huerfano_retorna_sin_modificar(self):
        orphan, old_parent, child, p, new_parent = self._setup_orphan()

        result = child.change_categorie_father(new_parent, {}, del_option=0)

        assert isinstance(result, dict) and len(result) > 0
        assert child.father_categorie is old_parent  # sin modificación

    def test_del_option_0_sin_impacto_continua(self):
        """old_parent no tiene atributos → no hay huérfanos → cambia padre."""
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        new_parent = mk_cat("NewParent")

        result = child.change_categorie_father(new_parent, {}, del_option=0)

        assert result == {}
        assert child.father_categorie is new_parent

    def test_del_option_1_inyecta_huerfanos_en_self(self):
        orphan, old_parent, child, p, new_parent = self._setup_orphan("peso_h1")

        result = child.change_categorie_father(new_parent, {}, del_option=1)

        assert result == {}
        assert child.father_categorie is new_parent
        assert orphan in child.attributes  # inyectado
        # implementaciones intactas
        assert any(i.attribute.key == orphan.key for i in p.attributes_implementations)

    def test_del_option_2_elimina_implementaciones_huerfanas_estatico(self):
        orphan, old_parent, child, p, new_parent = self._setup_orphan("peso_h2")

        result = child.change_categorie_father(new_parent, {}, del_option=2)

        assert result == {}
        assert child.father_categorie is new_parent
        assert not any(i.attribute.key == orphan.key for i in p.attributes_implementations)

    def test_del_option_2_elimina_implementaciones_huerfanas_dinamico(self):
        orphan = mk_attr("color_h", data_type="text", is_static=False)
        old_parent = mk_cat("OldParent")
        cat_add_attr(old_parent, orphan)
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, orphan, "rojo")
        p.variants.append(v)
        # Para que el producto aparezca en orphan_impact, necesita impl_keys
        p._impl_keys.add(orphan.key)
        cat_add_product(child, p)
        new_parent = mk_cat("NewParent")

        result = child.change_categorie_father(new_parent, {}, del_option=2)

        assert result == {}
        assert not any(i.attribute.key == orphan.key for i in v.attribute_implementations)

    # ── Escenario A — nuevo padre no aporta atributos nuevos ─────────────

    def test_escA_sin_atributos_nuevos_cambia_padre(self):
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        new_parent = mk_cat("NewParent")

        result = child.change_categorie_father(new_parent, {})

        assert result == {}
        assert child.father_categorie is new_parent
        assert child in new_parent.subcategories
        assert child not in old_parent.subcategories

    def test_escA_nuevo_padre_tiene_attrs_que_descendientes_ya_poseen(self):
        a = mk_attr("material", data_type="text", is_static=True)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, a)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        prod_add_attr(p, a)   # ya lo tiene propio → no necesita implementación
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {})

        assert result == {}
        assert child.father_categorie is new_parent

    # ── Escenario B — nuevo padre aporta atributos nuevos ────────────────

    def test_escB_falta_atributo_en_implementations_retorna_impact_map(self):
        new_attr = mk_attr("material", data_type="text", is_static=True)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {})  # faltan implementations

        assert isinstance(result, dict) and len(result) > 0
        assert child.father_categorie is old_parent  # sin modificación

    def test_escB_falta_producto_en_attr_retorna_impact_map(self):
        new_attr = mk_attr("material_b2", data_type="text", is_static=True)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p1 = mk_prod("P1", child, id=1)
        p2 = mk_prod("P2", child, id=2)
        cat_add_product(child, p1)
        cat_add_product(child, p2)

        result = child.change_categorie_father(new_parent, {
            "material_b2": [(1, "madera")],   # p2 falta
        })
        assert isinstance(result, dict) and len(result) > 0
        assert child.father_categorie is old_parent

    def test_escB_valor_invalido_retorna_impact_map(self):
        new_attr = mk_attr("peso_b3", data_type="number", is_static=True)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {
            "peso_b3": [(1, "no_es_numero")],
        })
        assert isinstance(result, dict) and len(result) > 0
        assert child.father_categorie is old_parent

    def test_escB_cobertura_exacta_estatico_cambia_padre(self):
        new_attr = mk_attr("material_ok", data_type="text", is_static=True)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {
            "material_ok": [(1, "madera")],
        })
        assert result == {}
        assert child.father_categorie is new_parent
        assert any(i.attribute.key == "material_ok" for i in p.attributes_implementations)

    def test_escB_falta_variante_dinamico_retorna_impact_map(self):
        new_attr = mk_attr("color_dyn", data_type="text", is_static=False)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        v1 = mk_variant(id=10)
        v2 = mk_variant(id=11)
        p.variants.extend([v1, v2])
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {
            "color_dyn": [(1, [{"variant_id": 10, "value": "rojo"}])],  # falta v2
        })
        assert isinstance(result, dict) and len(result) > 0
        assert child.father_categorie is old_parent

    def test_escB_cobertura_exacta_dinamico_cambia_padre(self):
        new_attr = mk_attr("color_dyn_ok", data_type="text", is_static=False)
        new_parent = mk_cat("NewParent")
        cat_add_attr(new_parent, new_attr)
        old_parent = mk_cat("OldParent")
        child = mk_cat("Child")
        cat_add_subcat(old_parent, child)
        p = mk_prod("P1", child, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)
        cat_add_product(child, p)

        result = child.change_categorie_father(new_parent, {
            "color_dyn_ok": [(1, [{"variant_id": 10, "value": "rojo"}])],
        })
        assert result == {}
        assert child.father_categorie is new_parent
        assert any(i.attribute.key == "color_dyn_ok" for i in v.attribute_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 6. Category.del_categorie
# ═══════════════════════════════════════════════════════════════════════════

class TestDelCategorie:
    """Sección 6 — Category.del_categorie"""

    def test_categorie_no_es_hija_retorna_false(self):
        parent = mk_cat("Parent")
        orphan = mk_cat("Orphan")
        result = parent.del_categorie(orphan, del_option=0)
        assert result is False

    def test_sin_atributos_sobrantes_elimina_directo(self):
        a = mk_attr("peso", is_static=True)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_attr(child, a)   # padre ya lo cubre → no sobrante
        cat_add_subcat(parent, child)

        result = parent.del_categorie(child, del_option=0)

        assert result == []
        assert child not in parent.subcategories
        assert child.father_categorie is None

    def test_atributos_sobrantes_sin_productos_que_los_usen_elimina_directo(self):
        a = mk_attr("especial", is_static=True)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        # producto sin implementación del atributo sobrante
        p = mk_prod("P1", child, id=1)
        cat_add_product(child, p)

        result = parent.del_categorie(child, del_option=0)
        assert result == []
        assert child not in parent.subcategories

    # ── del_option=2 ─────────────────────────────────────────────────────

    def test_opt2_retorna_impactados_sin_modificar(self):
        a = mk_attr("unico", data_type="text", is_static=True)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        prod_add_static_impl(p, mk_impl(a, "x"))
        cat_add_product(child, p)

        result = parent.del_categorie(child, del_option=2)

        assert isinstance(result, list) and p in result
        assert child in parent.subcategories  # sin modificación

    # ── del_option=0 (migrar definición) ─────────────────────────────────

    def test_opt0_migra_definicion_mantiene_implementaciones_estatico(self):
        a = mk_attr("unico2", data_type="text", is_static=True)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        impl_obj = mk_impl(a, "x")
        prod_add_static_impl(p, impl_obj)
        cat_add_product(child, p)

        result = parent.del_categorie(child, del_option=0)

        assert result == []
        assert child not in parent.subcategories
        assert a in p.attributes                   # definición migrada
        assert impl_obj in p.attributes_implementations  # implementación intacta

    def test_opt0_migra_definicion_dinamico_via_subcategoria(self):
        """Usando subcategoría de child para verificar migración dinámica."""
        a = mk_attr("color_mig", data_type="text", is_static=False)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        grandchild = mk_cat("Grandchild")
        cat_add_subcat(child, grandchild)
        p = mk_prod("P1", grandchild, id=1)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)
        cat_add_product(grandchild, p)

        result = parent.del_categorie(child, del_option=0)

        assert result == []
        assert child not in parent.subcategories
        assert a in p.attributes  # definición migrada al producto

    # ── del_option=1 (eliminar implementaciones) ─────────────────────────

    def test_opt1_elimina_implementaciones_estatico(self):
        a = mk_attr("unico3", data_type="text", is_static=True)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        impl_obj = mk_impl(a, "x")
        prod_add_static_impl(p, impl_obj)
        cat_add_product(child, p)

        result = parent.del_categorie(child, del_option=1)

        assert result == []
        assert child not in parent.subcategories
        assert not any(i.attribute.key == a.key for i in p.attributes_implementations)

    def test_opt1_elimina_implementaciones_dinamico_via_subcategoria(self):
        a = mk_attr("color_del", data_type="text", is_static=False)
        parent = mk_cat("Parent")
        child = mk_cat("Child")
        cat_add_attr(child, a)
        cat_add_subcat(parent, child)
        grandchild = mk_cat("Grandchild")
        cat_add_subcat(child, grandchild)
        p = mk_prod("P1", grandchild, id=1)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)
        cat_add_product(grandchild, p)

        result = parent.del_categorie(child, del_option=1)

        assert result == []
        assert not any(i.attribute.key == a.key for i in v.attribute_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 7. Category.add_product
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddProduct:
    """Sección 7 — Category.add_product"""

    def test_categoria_con_subcategorias_lanza_valueerror(self):
        parent = mk_cat("Parent")
        sub = mk_cat("Sub")
        parent.subcategories.append(sub)
        p = mk_prod("P1", parent, id=1)

        with pytest.raises(ValueError):
            parent.add_product(p)

    def test_producto_ya_en_categoria_retorna_false(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        assert cat.add_product(p) is False

    def test_agrega_producto_exitosamente(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)

        result = cat.add_product(p)

        assert result is True
        assert p in cat.products
        assert "P1" in cat._product_codes


# ═══════════════════════════════════════════════════════════════════════════
# 8. Category.del_product
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryDelProduct:
    """Sección 8 — Category.del_product"""

    def test_producto_no_en_categoria_retorna_false(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        assert cat.del_product(p) is False

    def test_elimina_producto_exitosamente(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)

        result = cat.del_product(p)

        assert result is True
        assert p not in cat.products
        assert "P1" not in cat._product_codes

    def test_eliminar_no_borra_objeto_producto(self):
        """del_product solo desvincula, no destruye el objeto."""
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        cat_add_product(cat, p)
        cat.del_product(p)
        # p sigue siendo un objeto válido
        assert p.code == "P1"


# ═══════════════════════════════════════════════════════════════════════════
# 9. Product.add_dinamic_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestProductAddDinamicAttribute:
    """Sección 9 — Product.add_dinamic_attribute"""

    # ── Escenario A — atributo ya en los necesarios ──────────────────────

    def test_escA_atributo_cubierto_por_categoria_agrega_a_producto(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)

        result = p.add_dinamic_attribute(a, [])

        assert result is True
        assert a in p.attributes

    # ── Escenario A' — sin variantes, atributo no cubierto ───────────────

    def test_escA_prima_sin_variantes_agrega_atributo_sin_impls(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        # producto sin variantes

        result = p.add_dinamic_attribute(a, [])

        assert result is True
        assert a in p.attributes

    # ── Escenario B — hay variantes, atributo no cubierto ────────────────

    def test_escB_variant_ids_no_coinciden(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)

        result = p.add_dinamic_attribute(a, [])  # falta variant 10

        assert result is False
        assert a not in p.attributes

    def test_escB_variant_id_duplicado(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)

        result = p.add_dinamic_attribute(a, [
            {"variant_id": 10, "value": "rojo"},
            {"variant_id": 10, "value": "azul"},
        ])
        assert result is False
        assert a not in p.attributes

    def test_escB_valor_invalido_tipo_no_reconocido(self):
        """ValueError en check_value es capturado → retorna False."""
        a = Attribute(key="raro", name="raro", data_type="unknown_type", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)

        result = p.add_dinamic_attribute(a, [{"variant_id": 10, "value": "x"}])
        assert result is False
        assert a not in p.attributes

    def test_escB_cobertura_exacta_valores_validos(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)

        result = p.add_dinamic_attribute(a, [
            {"variant_id": 10, "value": "rojo"},
        ])
        assert result is True
        assert a in p.attributes
        assert any(i.attribute.key == "color" for i in v.attribute_implementations)

    def test_escB_multiples_variantes_cobertura_exacta(self):
        a = mk_attr("talle", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v1 = mk_variant(id=10)
        v2 = mk_variant(id=11)
        p.variants.extend([v1, v2])

        result = p.add_dinamic_attribute(a, [
            {"variant_id": 10, "value": "S"},
            {"variant_id": 11, "value": "M"},
        ])
        assert result is True
        assert a in p.attributes
        assert any(i.value == "S" for i in v1.attribute_implementations)
        assert any(i.value == "M" for i in v2.attribute_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 10. Product.add_static_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestProductAddStaticAttribute:
    """Sección 10 — Product.add_static_attribute"""

    def test_valor_invalido_lanza_valueerror(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)

        with pytest.raises(ValueError):
            p.add_static_attribute(a, mk_impl(a, "no_es_numero"))

    def test_atributo_no_suscripto_retorna_false(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()  # atributo no en la categoría
        p = mk_prod("P1", cat, id=1)

        result = p.add_static_attribute(a, mk_impl(a, 500))

        assert result is False

    def test_ya_implementado_lanza_valueerror(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)

        with pytest.raises(ValueError):
            p.add_static_attribute(a, mk_impl(a, 600))

    def test_valido_agrega_implementacion(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)

        result = p.add_static_attribute(a, impl_obj)

        assert result is True
        assert impl_obj in p.attributes_implementations
        assert "peso" in p._impl_keys

    def test_valido_con_atributo_en_categoria_ancestro(self):
        a = mk_attr("material", data_type="text", is_static=True)
        parent = mk_cat("Parent")
        cat_add_attr(parent, a)
        child = mk_cat("Child")
        cat_add_subcat(parent, child)
        p = mk_prod("P1", child, id=1)
        impl_obj = mk_impl(a, "madera")

        result = p.add_static_attribute(a, impl_obj)

        assert result is True


# ═══════════════════════════════════════════════════════════════════════════
# 11. Product.del_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestProductDelAttribute:
    """Sección 11 — Product.del_attribute"""

    def test_atributo_no_en_producto_retorna_false(self):
        a = mk_attr("peso", is_static=True)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)

        assert p.del_attribute(a) is False

    # ── Escenario A — categoría ya cubre el atributo ─────────────────────

    def test_escA_categoria_cubre_elimina_redundancia(self):
        a = mk_attr("peso", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)   # redundante

        result = p.del_attribute(a)

        assert result == []
        assert a not in p.attributes
        assert "peso" not in p._attribute_keys

    # ── Escenario B1 — sin implementaciones huérfanas ────────────────────

    def test_escB1_sin_impls_huerfanas_elimina_directo(self):
        a = mk_attr("peso", is_static=True)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)

        result = p.del_attribute(a)

        assert result == []
        assert a not in p.attributes

    # ── Escenario B2, delete_opt=0 ───────────────────────────────────────

    def test_escB2_opt0_estatico_retorna_impls_sin_modificar(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)

        result = p.del_attribute(a, delete_opt=0)

        assert isinstance(result, list) and impl_obj in result
        assert a in p.attributes  # sin modificación

    def test_escB2_opt0_dinamico_retorna_variantes_sin_modificar(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)

        result = p.del_attribute(a, delete_opt=0)

        assert isinstance(result, list) and v in result
        assert a in p.attributes  # sin modificación

    # ── Escenario B2, delete_opt=1 ───────────────────────────────────────

    def test_escB2_opt1_estatico_elimina_impls_y_atributo(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        prod_add_static_impl(p, mk_impl(a, 500))

        result = p.del_attribute(a, delete_opt=1)

        assert result == []
        assert a not in p.attributes
        assert not any(i.attribute.key == "peso" for i in p.attributes_implementations)
        assert "peso" not in p._impl_keys

    def test_escB2_opt1_dinamico_elimina_impls_variantes_y_atributo(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)

        result = p.del_attribute(a, delete_opt=1)

        assert result == []
        assert a not in p.attributes
        assert not any(i.attribute.key == "color" for i in v.attribute_implementations)


# ═══════════════════════════════════════════════════════════════════════════
# 12. Product.add_product_implementation
# ═══════════════════════════════════════════════════════════════════════════

class TestProductAddProductImplementation:
    """Sección 12 — Product.add_product_implementation"""

    def test_atributo_dinamico_lanza_valueerror(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)

        with pytest.raises(ValueError):
            p.add_product_implementation(mk_impl(a, "rojo"))

    def test_valor_invalido_retorna_false(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)

        result = p.add_product_implementation(mk_impl(a, "no_es_numero"))
        assert result is False

    def test_atributo_no_suscripto_retorna_false(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()  # sin el attr
        p = mk_prod("P1", cat, id=1)

        result = p.add_product_implementation(mk_impl(a, 500))
        assert result is False

    def test_ya_implementado_lanza_valueerror(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)
        prod_add_static_impl(p, impl_obj)

        with pytest.raises(ValueError):
            p.add_product_implementation(mk_impl(a, 600))

    def test_valido_agrega_implementacion(self):
        a = mk_attr("peso", data_type="number", is_static=True)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        impl_obj = mk_impl(a, 500)

        p.add_product_implementation(impl_obj)

        assert impl_obj in p.attributes_implementations
        assert "peso" in p._impl_keys


# ═══════════════════════════════════════════════════════════════════════════
# 13. Product.create_variant_by_implementations
# ═══════════════════════════════════════════════════════════════════════════

class TestProductCreateVariant:
    """Sección 13 — Product.create_variant_by_implementations"""

    def _prod_con_attr_dinamico(self, key="color"):
        a = mk_attr(key, data_type="text", is_static=False)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        return p, a

    def test_atributo_duplicado_en_lista_retorna_none(self):
        p, a = self._prod_con_attr_dinamico()

        result = p.create_variant_by_implementations([
            mk_impl(a, "rojo"),
            mk_impl(a, "azul"),   # mismo atributo dos veces
        ])
        assert result is None
        assert len(p.variants) == 0

    def test_falta_atributo_requerido_retorna_none(self):
        p, a = self._prod_con_attr_dinamico()

        result = p.create_variant_by_implementations([])  # falta "color"
        assert result is None
        assert len(p.variants) == 0

    def test_atributo_sobrante_retorna_none(self):
        p, a = self._prod_con_attr_dinamico()
        extra = mk_attr("talle_extra", data_type="text", is_static=False)

        result = p.create_variant_by_implementations([
            mk_impl(a, "rojo"),
            mk_impl(extra, "M"),   # atributo no requerido
        ])
        assert result is None
        assert len(p.variants) == 0

    def test_valor_invalido_tipo_no_reconocido_retorna_none(self):
        a = Attribute(key="raro_v", name="raro_v", data_type="unknown", is_static=False)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)

        result = p.create_variant_by_implementations([mk_impl(a, "x")])
        assert result is None
        assert len(p.variants) == 0

    def test_valido_crea_variante(self):
        p, a = self._prod_con_attr_dinamico()

        p.create_variant_by_implementations([mk_impl(a, "rojo")])

        assert len(p.variants) == 1
        assert any(i.attribute.key == "color" for i in p.variants[0].attribute_implementations)

    def test_valido_multiples_atributos_crea_variante(self):
        cat = mk_cat()
        a1 = mk_attr("color_m", data_type="text", is_static=False)
        a2 = mk_attr("talle_m", data_type="text", is_static=False)
        cat_add_attr(cat, a1)
        cat_add_attr(cat, a2)
        p = mk_prod("P1", cat, id=1)

        p.create_variant_by_implementations([
            mk_impl(a1, "rojo"),
            mk_impl(a2, "M"),
        ])
        assert len(p.variants) == 1
        keys = {i.attribute.key for i in p.variants[0].attribute_implementations}
        assert {"color_m", "talle_m"} == keys


# ═══════════════════════════════════════════════════════════════════════════
# 14. Product.del_variant
# ═══════════════════════════════════════════════════════════════════════════

class TestProductDelVariant:
    """Sección 14 — Product.del_variant"""

    def test_variante_no_existe_retorna_false(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)

        assert p.del_variant(99) is False

    def test_elimina_variante_exitosamente(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v = mk_variant(id=10)
        p.variants.append(v)

        result = p.del_variant(10)

        assert result is True
        assert v not in p.variants

    def test_eliminar_variante_no_afecta_atributos_del_producto(self):
        a = mk_attr("color", data_type="text", is_static=False)
        cat = mk_cat()
        cat_add_attr(cat, a)
        p = mk_prod("P1", cat, id=1)
        prod_add_attr(p, a)
        v = mk_variant(id=10)
        prod_add_dynamic_impl_to_variant(v, a, "rojo")
        p.variants.append(v)

        p.del_variant(10)

        assert a in p.attributes   # atributos del producto intactos

    def test_elimina_por_id_correcto_con_multiples_variantes(self):
        cat = mk_cat()
        p = mk_prod("P1", cat, id=1)
        v1 = mk_variant(id=10)
        v2 = mk_variant(id=11)
        p.variants.extend([v1, v2])

        p.del_variant(10)

        assert v1 not in p.variants
        assert v2 in p.variants
