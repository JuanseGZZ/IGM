"""
testing_apis_service.py — Tests de reglas de negocio sobre la capa de servicio.

Cubre todos los escenarios de acciones_reglas_negocio.md probando a través del
service (no del HTTP ni de los repos directamente).

Para correr: pytest TestingConcepts/app/testing_apis_service.py -v
"""

import uuid
import pytest
from config import conn
from service import AttributeService, CategoryService, ProductService


def _uid():
    """Short unique suffix to avoid DB key conflicts on repeated runs."""
    return uuid.uuid4().hex[:8]


# ─── fixture global: rollback entre tests ───────────────────────────────────

@pytest.fixture(autouse=True)
def rollback_on_error():
    yield
    try:
        conn.rollback()
    except Exception:
        pass


# ─── helpers de construcción ─────────────────────────────────────────────────

def mk_text_attr(key="t_key", is_static=True):
    return AttributeService.create(key=key, name=key, data_type="text", is_static=is_static)

def mk_num_attr(key="n_key", is_static=True):
    return AttributeService.create(key=key, name=key, data_type="number", is_static=is_static)

def mk_bool_attr(key="b_key"):
    return AttributeService.create(key=key, name=key, data_type="boolean", is_static=False)

def mk_enum_attr(key="e_key", values=None, is_static=False):
    return AttributeService.create(
        key=key, name=key, data_type="enum", is_static=is_static,
        enum_values=values or ["A", "B", "C"],
    )

def mk_cat(name="Cat"):
    return CategoryService.create(name)

def mk_prod(cat_id, code=None):
    code = code or f"P-{_uid()}"
    return ProductService.create(
        code=code, title=code, price=10.0,
        description="", brand="B", category_id=cat_id,
    )

def mk_variant(prod_id, attr_id, value="A"):
    return ProductService.create_variant(
        prod_id,
        [{"attribute_id": attr_id, "value": value}],
    )

def cleanup(*ids_by_type):
    """
    Borra en orden seguro respecto a FKs.
    ids_by_type: ("prod", [id, ...]), ("cat", [id, ...]), ("attr", [id, ...])
    """
    order = {"prod": 0, "cat": 1, "attr": 2}
    for kind, ids in sorted(ids_by_type, key=lambda x: order.get(x[0], 99)):
        svc = {"prod": ProductService, "cat": CategoryService, "attr": AttributeService}[kind]
        for obj_id in ids:
            try:
                svc.delete(obj_id)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════════
# AttributeService
# ═══════════════════════════════════════════════════════════════════════════

class TestAttributeService:

    # ── CRUD básico ──────────────────────────────────────────────────────────

    def test_create_text(self):
        a = mk_text_attr("as_text")
        try:
            assert a.id is not None
            assert a.key == "as_text"
            assert a.data_type == "text"
            assert a.is_static is True
        finally:
            cleanup(("attr", [a.id]))

    def test_create_enum_with_values(self):
        a = mk_enum_attr("as_enum", ["X", "Y", "Z"])
        try:
            assert set(a.enum_values) == {"X", "Y", "Z"}
        finally:
            cleanup(("attr", [a.id]))

    def test_get_found(self):
        a = mk_text_attr("as_get")
        try:
            result = AttributeService.get(a.id)
            assert result is not None
            assert result.key == "as_get"
        finally:
            cleanup(("attr", [a.id]))

    def test_get_not_found_returns_none(self):
        assert AttributeService.get(999999) is None

    def test_get_all_includes_created(self):
        a = mk_text_attr("as_all")
        try:
            ids = [x.id for x in AttributeService.get_all()]
            assert a.id in ids
        finally:
            cleanup(("attr", [a.id]))

    def test_update_name(self):
        a = mk_text_attr("as_upd")
        try:
            updated = AttributeService.update(a.id, name="nuevo_nombre")
            assert updated.name == "nuevo_nombre"
        finally:
            cleanup(("attr", [a.id]))

    def test_update_enum_values_replaces_all(self):
        a = mk_enum_attr("as_upd_enum", ["X", "Y"])
        try:
            updated = AttributeService.update(a.id, enum_values=["M", "L", "XL"])
            assert set(updated.enum_values) == {"M", "L", "XL"}
        finally:
            cleanup(("attr", [a.id]))

    def test_update_none_params_no_change(self):
        a = mk_text_attr("as_nochg")
        try:
            updated = AttributeService.update(a.id)   # sin params
            assert updated.name == "as_nochg"
        finally:
            cleanup(("attr", [a.id]))

    def test_update_not_found_returns_none(self):
        assert AttributeService.update(999999, name="x") is None

    def test_delete_success(self):
        a = mk_text_attr("as_del")
        attr_id = a.id
        assert AttributeService.delete(attr_id) is True
        assert AttributeService.get(attr_id) is None

    def test_delete_not_found_returns_false(self):
        assert AttributeService.delete(999999) is False

    # ── add_enum_value ────────────────────────────────────────────────────────

    def test_add_enum_value_success(self):
        a = mk_enum_attr("as_ev", ["A"])
        try:
            updated = AttributeService.add_enum_value(a.id, "B")
            assert "B" in updated.enum_values
            assert "A" in updated.enum_values
        finally:
            cleanup(("attr", [a.id]))

    def test_add_enum_value_not_found_returns_none(self):
        assert AttributeService.add_enum_value(999999, "X") is None

    def test_add_enum_value_non_enum_raises(self):
        a = mk_text_attr("as_ev_nontype")
        try:
            with pytest.raises(ValueError, match="enum"):
                AttributeService.add_enum_value(a.id, "algo")
        finally:
            cleanup(("attr", [a.id]))

    def test_add_enum_value_duplicate_raises(self):
        a = mk_enum_attr("as_ev_dup", ["A"])
        try:
            with pytest.raises(ValueError):
                AttributeService.add_enum_value(a.id, "A")
        finally:
            cleanup(("attr", [a.id]))


# ═══════════════════════════════════════════════════════════════════════════
# CategoryService — CRUD
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryServiceCRUD:

    def test_create_and_get(self):
        cat = mk_cat("CS_cat")
        try:
            result = CategoryService.get(cat.id)
            assert result.name == "CS_cat"
        finally:
            cleanup(("cat", [cat.id]))

    def test_get_not_found_returns_none(self):
        assert CategoryService.get(999999) is None

    def test_get_all_includes_created(self):
        cat = mk_cat("CS_all")
        try:
            ids = [c.id for c in CategoryService.get_all()]
            assert cat.id in ids
        finally:
            cleanup(("cat", [cat.id]))

    def test_update_name(self):
        cat = mk_cat("CS_upd")
        try:
            updated = CategoryService.update_name(cat.id, "CS_renamed")
            assert updated.name == "CS_renamed"
        finally:
            cleanup(("cat", [cat.id]))

    def test_update_not_found_returns_none(self):
        assert CategoryService.update_name(999999, "x") is None

    def test_delete_success(self):
        cat = mk_cat("CS_del")
        cat_id = cat.id
        assert CategoryService.delete(cat_id) is True
        assert CategoryService.get(cat_id) is None

    def test_delete_with_products_fails(self):
        """Regla: ON DELETE RESTRICT en product.category_id."""
        cat  = mk_cat("CS_del_prod")
        prod = mk_prod(cat.id)
        try:
            with pytest.raises(Exception):
                CategoryService.delete(cat.id)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))


# ═══════════════════════════════════════════════════════════════════════════
# CategoryService — add_dynamic_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddDynamicAttribute:

    def test_no_products_adds_directly(self):
        """Escenario B: categoría sin productos → atributo agregado sin pedir nada."""
        attr = mk_enum_attr("cad_nopr")
        cat  = mk_cat("CAD_NoProd")
        try:
            result = CategoryService.add_dynamic_attribute(cat.id, attr.id)
            assert result["needs_implementations"] is False
            assert any(a.key == "cad_nopr" for a in result["category"].attributes)
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))

    def test_static_attr_raises(self):
        """Regla: add_dinamic_attribute lanza ValueError si el atributo es estático."""
        attr = mk_text_attr("cad_static")   # is_static=True
        cat  = mk_cat("CAD_Static")
        try:
            with pytest.raises(ValueError):
                CategoryService.add_dynamic_attribute(cat.id, attr.id)
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))

    def test_product_no_variants_adds_directly(self):
        """Producto sin variantes: no hay variantes que cubrir → agrega libre."""
        attr = mk_enum_attr("cad_novr")
        cat  = mk_cat("CAD_NoVar")
        prod = mk_prod(cat.id, "CAD-NOVR-001")
        try:
            result = CategoryService.add_dynamic_attribute(cat.id, attr.id)
            assert result["needs_implementations"] is False
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_product_with_variants_needs_implementations(self):
        """Escenario C: producto con variantes → primera llamada retorna impact."""
        attr1 = mk_enum_attr("cad_a1", ["X", "Y"])
        attr2 = mk_enum_attr("cad_a2", ["P", "Q"])
        cat   = mk_cat("CAD_WithVar")
        try:
            # Armamos: categoría → attr1 → producto → variante
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod = mk_prod(cat.id, "CAD-VAR-001")
            mk_variant(prod.id, attr1.id, "X")

            # Primera llamada sin implementations → necesita valores para variantes
            result = CategoryService.add_dynamic_attribute(cat.id, attr2.id)
            assert result["needs_implementations"] is True
            assert len(result["impact"]) == 1
            assert result["impact"][0]["product_id"] == prod.id
            assert len(result["impact"][0]["variants"]) == 1
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))

    def test_product_with_variants_wrong_implementations_still_needs(self):
        """Implementaciones incompletas (falta variante) → sigue pidiendo."""
        attr1 = mk_enum_attr("cad_wr1", ["X", "Y"])
        attr2 = mk_enum_attr("cad_wr2", ["P", "Q"])
        cat   = mk_cat("CAD_WrongImpl")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod = mk_prod(cat.id, "CAD-WR-001")
            r = mk_variant(prod.id, attr1.id, "X")
            prod_fresh = ProductService.get(r["product"].id)
            var_id = prod_fresh.variants[0].id

            # implementations con product_id incorrecto
            bad_impls = [{"product_id": 999999, "variants": [{"variant_id": var_id, "value": "P"}]}]
            result = CategoryService.add_dynamic_attribute(cat.id, attr2.id, bad_impls)
            assert result["needs_implementations"] is True
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))

    def test_product_with_variants_correct_implementations_succeeds(self):
        """Segunda llamada con implementations completas y válidas → éxito."""
        attr1 = mk_enum_attr("cad_ok1", ["X", "Y"])
        attr2 = mk_enum_attr("cad_ok2", ["P", "Q"])
        cat   = mk_cat("CAD_OkImpl")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod = mk_prod(cat.id, "CAD-OK-001")
            r = mk_variant(prod.id, attr1.id, "X")
            prod_fresh = ProductService.get(r["product"].id)
            var_id = prod_fresh.variants[0].id

            impls = [{"product_id": prod_fresh.id, "variants": [{"variant_id": var_id, "value": "P"}]}]
            result = CategoryService.add_dynamic_attribute(cat.id, attr2.id, impls)

            assert result["needs_implementations"] is False
            # el atributo está en la categoría
            cat_keys = {a.key for a in result["category"].attributes}
            assert "cad_ok2" in cat_keys
            # la variante tiene la implementación
            prod_after = ProductService.get(prod_fresh.id)
            variant_impls = {i.attribute.key for i in prod_after.variants[0].attribute_implementations}
            assert "cad_ok2" in variant_impls
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))

    def test_attr_already_covered_by_ancestor_no_impact(self):
        """Escenario A: si un ancestro ya tiene el atributo, no hay nada que hacer."""
        attr = mk_enum_attr("cad_anc")
        cat  = mk_cat("CAD_Anc")
        try:
            # primera vez agrega normalmente
            r1 = CategoryService.add_dynamic_attribute(cat.id, attr.id)
            assert r1["needs_implementations"] is False
            # segunda vez: el ancestro (la misma cat) ya lo tiene → nada que hacer
            r2 = CategoryService.add_dynamic_attribute(cat.id, attr.id)
            assert r2["needs_implementations"] is False
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# CategoryService — add_static_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddStaticAttribute:

    def test_no_products_adds_directly(self):
        attr = mk_text_attr("cas_nopr")
        cat  = mk_cat("CAS_NoProd")
        try:
            result = CategoryService.add_static_attribute(cat.id, attr.id)
            assert result["needs_implementations"] is False
            assert any(a.key == "cas_nopr" for a in result["category"].attributes)
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))

    def test_dynamic_attr_raises(self):
        """Regla: add_static_attribute lanza ValueError si el atributo es dinámico."""
        attr = mk_enum_attr("cas_dyn")  # is_static=False
        cat  = mk_cat("CAS_Dyn")
        try:
            with pytest.raises(ValueError):
                CategoryService.add_static_attribute(cat.id, attr.id)
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))

    def test_product_without_impl_needs_implementations(self):
        """Producto existe pero no tiene el atributo → primera llamada retorna impact."""
        attr = mk_text_attr("cas_ni")
        cat  = mk_cat("CAS_NoImpl")
        prod = mk_prod(cat.id, "CAS-NI-001")
        try:
            result = CategoryService.add_static_attribute(cat.id, attr.id)
            assert result["needs_implementations"] is True
            assert result["impact"][0]["product_id"] == prod.id
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_product_with_correct_implementation_succeeds(self):
        """Segunda llamada con value válido → atributo y impl guardados."""
        attr = mk_text_attr("cas_ok")
        cat  = mk_cat("CAS_Ok")
        prod = mk_prod(cat.id, "CAS-OK-001")
        try:
            impls = [{"product_id": prod.id, "value": "algodon"}]
            result = CategoryService.add_static_attribute(cat.id, attr.id, impls)

            assert result["needs_implementations"] is False
            prod_after = ProductService.get(prod.id)
            impl_keys = {i.attribute.key for i in prod_after.attributes_implementations}
            assert "cas_ok" in impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_wrong_product_id_in_implementations(self):
        """product_id incorrecto → sigue pidiendo implementations."""
        attr = mk_text_attr("cas_wr")
        cat  = mk_cat("CAS_Wrong")
        prod = mk_prod(cat.id, "CAS-WR-001")
        try:
            bad_impls = [{"product_id": 999999, "value": "algo"}]
            result = CategoryService.add_static_attribute(cat.id, attr.id, bad_impls)
            assert result["needs_implementations"] is True
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# CategoryService — del_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryDelAttribute:

    def _setup_cat_with_static_impl(self, attr_key, cat_name, prod_code, value="dato"):
        """Crea categoría + atributo + producto con implementación."""
        attr = mk_text_attr(attr_key)
        cat  = mk_cat(cat_name)
        CategoryService.add_static_attribute(cat.id, attr.id)
        prod = mk_prod(cat.id, prod_code)
        # agrega implementación al producto
        impls = [{"product_id": prod.id, "value": value}]
        CategoryService.add_static_attribute(cat.id, attr.id, impls)
        return attr, cat, mk_prod   # retornamos para cleanup

    def test_no_impact_deletes_directly(self):
        """Categoría con atributo pero sin productos con impl → elimina sin preguntar."""
        attr = mk_text_attr("cda_noi")
        cat  = mk_cat("CDA_NoImpact")
        try:
            CategoryService.add_static_attribute(cat.id, attr.id)
            result = CategoryService.del_attribute(cat.id, attr.id)
            assert result["needs_decision"] is False
            cat_after = CategoryService.get(cat.id)
            assert all(a.key != "cda_noi" for a in cat_after.attributes)
        finally:
            cleanup(("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_opt_0_returns_impact_without_modifying(self):
        """del_opt=0 con producto impactado → retorna needs_decision, no modifica."""
        attr = mk_text_attr("cda_0")
        cat  = mk_cat("CDA_Opt0")
        prod = mk_prod(cat.id, "CDA-0-001")
        try:
            # agregar attr y impl al producto
            CategoryService.add_static_attribute(cat.id, attr.id,
                                                 [{"product_id": prod.id, "value": "v"}])
            result = CategoryService.del_attribute(cat.id, attr.id, del_opt=0)
            assert result["needs_decision"] is True
            assert any(e["product_id"] == prod.id for e in result["impact"])
            # el atributo sigue en la categoría
            cat_after = CategoryService.get(cat.id)
            assert any(a.key == "cda_0" for a in cat_after.attributes)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_opt_1_deletes_implementations(self):
        """del_opt=1 → elimina implementaciones huérfanas en el producto."""
        attr = mk_text_attr("cda_1")
        cat  = mk_cat("CDA_Opt1")
        prod = mk_prod(cat.id, "CDA-1-001")
        try:
            CategoryService.add_static_attribute(cat.id, attr.id,
                                                 [{"product_id": prod.id, "value": "v"}])
            result = CategoryService.del_attribute(cat.id, attr.id, del_opt=1)
            assert result["needs_decision"] is False
            prod_after = ProductService.get(prod.id)
            impl_keys = {i.attribute.key for i in prod_after.attributes_implementations}
            assert "cda_1" not in impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_opt_2_injects_attr_into_products(self):
        """del_opt=2 → inyecta el atributo en el producto, mantiene implementaciones."""
        attr = mk_text_attr("cda_2")
        cat  = mk_cat("CDA_Opt2")
        prod = mk_prod(cat.id, "CDA-2-001")
        try:
            CategoryService.add_static_attribute(cat.id, attr.id,
                                                 [{"product_id": prod.id, "value": "v"}])
            result = CategoryService.del_attribute(cat.id, attr.id, del_opt=2)
            assert result["needs_decision"] is False
            prod_after = ProductService.get(prod.id)
            # el atributo ahora es propio del producto
            own_keys = {a.key for a in prod_after.attributes}
            assert "cda_2" in own_keys
            # la implementación se mantiene
            impl_keys = {i.attribute.key for i in prod_after.attributes_implementations}
            assert "cda_2" in impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_dynamic_opt_1_clears_variant_implementations(self):
        """del_opt=1 en atributo dinámico → limpia implementaciones en variantes."""
        attr = mk_enum_attr("cda_dyn1", ["X", "Y"])
        cat  = mk_cat("CDA_Dyn1")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod = mk_prod(cat.id, "CDA-DYN1-001")
            r    = mk_variant(prod.id, attr.id, "X")
            prod_id = r["product"].id
            var_id  = ProductService.get(prod_id).variants[0].id

            result = CategoryService.del_attribute(cat.id, attr.id, del_opt=1)
            assert result["needs_decision"] is False
            prod_after = ProductService.get(prod_id)
            variant_impl_keys = {
                i.attribute.key
                for v in prod_after.variants
                for i in v.attribute_implementations
            }
            assert "cda_dyn1" not in variant_impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# CategoryService — add_product_to_category
# ═══════════════════════════════════════════════════════════════════════════

class TestCategoryAddProduct:

    def test_reassigns_product_category(self):
        cat1 = mk_cat("CAP_Cat1")
        cat2 = mk_cat("CAP_Cat2")
        prod = mk_prod(cat1.id, "CAP-001")
        try:
            updated = CategoryService.add_product_to_category(cat2.id, prod.id)
            assert updated.category.id == cat2.id
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat1.id, cat2.id]))

    def test_not_found_cat_raises(self):
        with pytest.raises(ValueError, match="Categoría"):
            CategoryService.add_product_to_category(999999, 1)

    def test_not_found_prod_raises(self):
        cat = mk_cat("CAP_NoProd")
        try:
            with pytest.raises(ValueError, match="Producto"):
                CategoryService.add_product_to_category(cat.id, 999999)
        finally:
            cleanup(("cat", [cat.id]))


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — CRUD
# ═══════════════════════════════════════════════════════════════════════════

class TestProductServiceCRUD:

    def test_create_and_get(self):
        cat  = mk_cat("PS_cat")
        prod = mk_prod(cat.id, "PS-001")
        try:
            result = ProductService.get(prod.id)
            assert result.code == "PS-001"
            assert result.category.id == cat.id
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))

    def test_get_not_found_returns_none(self):
        assert ProductService.get(999999) is None

    def test_get_by_code(self):
        cat  = mk_cat("PS_bycode")
        prod = mk_prod(cat.id, "PS-BYCODE-001")
        try:
            result = ProductService.get_by_code("PS-BYCODE-001")
            assert result.id == prod.id
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))

    def test_get_by_code_not_found(self):
        assert ProductService.get_by_code("NO-EXISTE") is None

    def test_get_all_includes_created(self):
        cat  = mk_cat("PS_all")
        prod = mk_prod(cat.id, "PS-ALL-001")
        try:
            ids = [p.id for p in ProductService.get_all()]
            assert prod.id in ids
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))

    def test_update_price_and_title(self):
        cat  = mk_cat("PS_upd")
        prod = mk_prod(cat.id, "PS-UPD-001")
        try:
            updated = ProductService.update(prod.id, title="Nuevo Título", price=999.0)
            assert updated.title == "Nuevo Título"
            assert updated.price == 999.0
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))

    def test_update_category(self):
        cat1 = mk_cat("PS_uc1")
        cat2 = mk_cat("PS_uc2")
        prod = mk_prod(cat1.id, "PS-UC-001")
        try:
            updated = ProductService.update(prod.id, category_id=cat2.id)
            assert updated.category.id == cat2.id
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat1.id, cat2.id]))

    def test_update_not_found_returns_none(self):
        assert ProductService.update(999999, title="x") is None

    def test_delete_success(self):
        cat    = mk_cat("PS_del")
        prod   = mk_prod(cat.id, "PS-DEL-001")
        prod_id = prod.id
        try:
            assert ProductService.delete(prod_id) is True
            assert ProductService.get(prod_id) is None
        finally:
            cleanup(("cat", [cat.id]))

    def test_create_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Categoría"):
            ProductService.create("X-001", "X", 1.0, "", "B", category_id=999999)


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — add_dynamic_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestProductAddDynamicAttribute:

    def test_no_variants_adds_directly(self):
        """Producto sin variantes → agrega el atributo sin pedir opciones."""
        attr = mk_enum_attr("pad_nv", ["A", "B"])
        cat  = mk_cat("PAD_NoVar")
        prod = mk_prod(cat.id, "PAD-NV-001")
        try:
            result = ProductService.add_dynamic_attribute(prod.id, attr.id)
            assert result["needs_implementations"] is False
            prod_after = ProductService.get(prod.id)
            own_keys = {a.key for a in prod_after.attributes}
            assert "pad_nv" in own_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_static_attr_raises(self):
        """Regla: no se puede agregar atributo estático como dinámico."""
        attr = mk_text_attr("pad_static")
        cat  = mk_cat("PAD_Static")
        prod = mk_prod(cat.id, "PAD-ST-001")
        try:
            with pytest.raises(ValueError):
                ProductService.add_dynamic_attribute(prod.id, attr.id)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_has_variants_no_options_needs_implementations(self):
        """Producto con variantes, sin variant_options → retorna impact."""
        attr1 = mk_enum_attr("pad_hv1", ["X", "Y"])
        attr2 = mk_enum_attr("pad_hv2", ["P", "Q"])
        cat   = mk_cat("PAD_HasVar")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod = mk_prod(cat.id, "PAD-HV-001")
            mk_variant(prod.id, attr1.id, "X")

            result = ProductService.add_dynamic_attribute(prod.id, attr2.id)
            assert result["needs_implementations"] is True
            assert len(result["impact"]) == 1
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))

    def test_has_variants_wrong_options_needs_implementations(self):
        """variant_options con variant_id incorrecto → sigue pidiendo."""
        attr1 = mk_enum_attr("pad_wr1", ["X", "Y"])
        attr2 = mk_enum_attr("pad_wr2", ["P", "Q"])
        cat   = mk_cat("PAD_Wrong")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod = mk_prod(cat.id, "PAD-WR-001")
            mk_variant(prod.id, attr1.id, "X")

            bad_opts = [{"variant_id": 999999, "value": "P"}]
            result = ProductService.add_dynamic_attribute(prod.id, attr2.id, bad_opts)
            assert result["needs_implementations"] is True
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))

    def test_has_variants_correct_options_succeeds(self):
        """variant_options completas y válidas → atributo e implementations guardados."""
        attr1 = mk_enum_attr("pad_ok1", ["X", "Y"])
        attr2 = mk_enum_attr("pad_ok2", ["P", "Q"])
        cat   = mk_cat("PAD_OkOpts")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr1.id)
            prod    = mk_prod(cat.id, "PAD-OK-001")
            r       = mk_variant(prod.id, attr1.id, "X")
            prod_id = r["product"].id
            var_id  = ProductService.get(prod_id).variants[0].id

            opts   = [{"variant_id": var_id, "value": "P"}]
            result = ProductService.add_dynamic_attribute(prod_id, attr2.id, opts)
            assert result["needs_implementations"] is False

            prod_after = ProductService.get(prod_id)
            own_keys   = {a.key for a in prod_after.attributes}
            assert "pad_ok2" in own_keys
            var_impl_keys = {
                i.attribute.key for i in prod_after.variants[0].attribute_implementations
            }
            assert "pad_ok2" in var_impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]),
                    ("attr", [attr1.id, attr2.id]))


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — add_implementation
# ═══════════════════════════════════════════════════════════════════════════

class TestProductAddImplementation:

    def test_success_subscribed_via_category(self):
        """Atributo suscripto en la categoría → implementación guardada."""
        attr = mk_text_attr(f"pai_ok_{_uid()}")
        cat  = mk_cat("PAI_Ok")
        # attr must be subscribed to category BEFORE product is created
        CategoryService.add_static_attribute(cat.id, attr.id)
        prod = mk_prod(cat.id)
        try:
            prod_after = ProductService.add_implementation(prod.id, attr.id, "hola")
            impl_keys  = {i.attribute.key for i in prod_after.attributes_implementations}
            assert attr.key in impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_not_subscribed_raises(self):
        """Atributo no suscripto en la categoría del producto → ValueError."""
        attr = mk_text_attr(f"pai_ns_{_uid()}")
        cat  = mk_cat("PAI_NS")
        prod = mk_prod(cat.id)
        try:
            with pytest.raises(ValueError):
                ProductService.add_implementation(prod.id, attr.id, "hola")
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_duplicate_raises(self):
        """Implementación ya existente → ValueError."""
        attr = mk_text_attr(f"pai_dup_{_uid()}")
        cat  = mk_cat("PAI_Dup")
        CategoryService.add_static_attribute(cat.id, attr.id)
        prod = mk_prod(cat.id)
        try:
            ProductService.add_implementation(prod.id, attr.id, "v1")
            with pytest.raises(ValueError):
                ProductService.add_implementation(prod.id, attr.id, "v2")
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_wrong_type_raises(self):
        """Valor del tipo incorrecto → ValueError."""
        attr = mk_num_attr(f"pai_type_{_uid()}")   # number
        cat  = mk_cat("PAI_Type")
        CategoryService.add_static_attribute(cat.id, attr.id)
        prod = mk_prod(cat.id)
        try:
            with pytest.raises(ValueError):
                ProductService.add_implementation(prod.id, attr.id, "no_es_numero")
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_dynamic_attr_raises(self):
        """Regla: no se puede agregar atributo dinámico como implementación estática."""
        attr = mk_bool_attr(f"pai_dyn_{_uid()}")
        cat  = mk_cat("PAI_Dyn")
        prod = mk_prod(cat.id)
        try:
            with pytest.raises(ValueError):
                ProductService.add_implementation(prod.id, attr.id, True)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — del_own_attribute
# ═══════════════════════════════════════════════════════════════════════════

class TestProductDelOwnAttribute:

    def test_attr_not_own_raises(self):
        """Atributo heredado de la categoría (no propio) → ValueError."""
        attr = mk_text_attr("pda_notown")
        cat  = mk_cat("PDA_NotOwn")
        prod = mk_prod(cat.id, "PDA-NO-001")
        try:
            CategoryService.add_static_attribute(cat.id, attr.id)
            # el attr es de la categoría, no del producto
            with pytest.raises(ValueError):
                ProductService.del_own_attribute(prod.id, "pda_notown")
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_no_impact_deletes_directly(self):
        """Atributo propio sin implementaciones → eliminado directamente."""
        attr = mk_enum_attr("pda_noi", ["A", "B"])
        cat  = mk_cat("PDA_NoImpact")
        prod = mk_prod(cat.id, "PDA-NI-001")
        try:
            # agregamos el atributo al producto (producto sin variantes → agrega libre)
            ProductService.add_dynamic_attribute(prod.id, attr.id)
            result = ProductService.del_own_attribute(prod.id, "pda_noi")
            assert result["needs_decision"] is False
            prod_after = ProductService.get(prod.id)
            assert all(a.key != "pda_noi" for a in prod_after.attributes)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_opt_0_with_impl_returns_impact(self):
        """del_opt=0 con implementaciones huérfanas → needs_decision, no modifica."""
        attr = mk_enum_attr("pda_0", ["X", "Y"])
        cat  = mk_cat("PDA_Opt0")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod = mk_prod(cat.id, "PDA-0-001")
            r    = mk_variant(prod.id, attr.id, "X")
            prod_id = r["product"].id

            # eliminamos el attr de la categoría con del_opt=2 para que quede en el producto
            prod_fresh = ProductService.get(prod_id)
            var_id = prod_fresh.variants[0].id
            CategoryService.del_attribute(cat.id, attr.id, del_opt=2)

            # ahora el attr es del producto; del_opt=0 → debe reportar el impacto
            result = ProductService.del_own_attribute(prod_id, "pda_0", del_opt=0)
            assert result["needs_decision"] is True
            # el atributo sigue en el producto
            prod_check = ProductService.get(prod_id)
            assert any(a.key == "pda_0" for a in prod_check.attributes)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_opt_1_clears_variant_implementations(self):
        """del_opt=1 → elimina implementaciones de las variantes."""
        attr = mk_enum_attr("pda_1", ["X", "Y"])
        cat  = mk_cat("PDA_Opt1")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod = mk_prod(cat.id, "PDA-1-001")
            r    = mk_variant(prod.id, attr.id, "X")
            prod_id = r["product"].id

            CategoryService.del_attribute(cat.id, attr.id, del_opt=2)

            result = ProductService.del_own_attribute(prod_id, "pda_1", del_opt=1)
            assert result["needs_decision"] is False
            prod_after = ProductService.get(prod_id)
            var_impl_keys = {
                i.attribute.key
                for v in prod_after.variants
                for i in v.attribute_implementations
            }
            assert "pda_1" not in var_impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — create_variant
# ═══════════════════════════════════════════════════════════════════════════

class TestProductCreateVariant:

    def test_single_attr_creates_variant(self):
        """Implementations exactas → variante creada."""
        attr = mk_enum_attr("pcv_ok", ["S", "M", "L"])
        cat  = mk_cat("PCV_Ok")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod   = mk_prod(cat.id, "PCV-OK-001")
            result = ProductService.create_variant(prod.id, [{"attribute_id": attr.id, "value": "S"}])
            assert "product" in result
            assert len(result["product"].variants) == 1
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_multiple_attrs_creates_variant(self):
        """Dos atributos dinámicos → variante con ambos."""
        a1 = mk_enum_attr("pcv_m1", ["S", "M"])
        a2 = mk_enum_attr("pcv_m2", ["rojo", "azul"])
        cat = mk_cat("PCV_Multi")
        try:
            CategoryService.add_dynamic_attribute(cat.id, a1.id)
            CategoryService.add_dynamic_attribute(cat.id, a2.id)
            prod = mk_prod(cat.id, "PCV-M-001")
            result = ProductService.create_variant(prod.id, [
                {"attribute_id": a1.id, "value": "S"},
                {"attribute_id": a2.id, "value": "rojo"},
            ])
            assert "product" in result
            assert len(result["product"].variants) == 1
            impl_keys = {i.attribute.key
                         for i in result["product"].variants[0].attribute_implementations}
            assert {"pcv_m1", "pcv_m2"} == impl_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [a1.id, a2.id]))

    def test_missing_attribute_returns_error(self):
        """Faltan atributos en implementations → error con needed_attributes."""
        a1 = mk_enum_attr("pcv_mi1", ["A"])
        a2 = mk_enum_attr("pcv_mi2", ["B"])
        cat = mk_cat("PCV_Missing")
        try:
            CategoryService.add_dynamic_attribute(cat.id, a1.id)
            CategoryService.add_dynamic_attribute(cat.id, a2.id)
            prod = mk_prod(cat.id, "PCV-MI-001")
            # solo pasamos un attr cuando se necesitan dos
            result = ProductService.create_variant(prod.id, [{"attribute_id": a1.id, "value": "A"}])
            assert "error" in result
            assert result["error"] == "implementations_invalid"
            needed_keys = {a["key"] for a in result["needed_attributes"]}
            assert "pcv_mi1" in needed_keys
            assert "pcv_mi2" in needed_keys
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [a1.id, a2.id]))

    def test_extra_attribute_returns_error(self):
        """Attr de más en implementations → error."""
        a1 = mk_enum_attr("pcv_ex1", ["A"])
        a2 = mk_enum_attr("pcv_ex2", ["B"])  # no suscripto
        cat = mk_cat("PCV_Extra")
        try:
            CategoryService.add_dynamic_attribute(cat.id, a1.id)
            prod = mk_prod(cat.id, "PCV-EX-001")
            result = ProductService.create_variant(prod.id, [
                {"attribute_id": a1.id, "value": "A"},
                {"attribute_id": a2.id, "value": "B"},
            ])
            assert "error" in result
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [a1.id, a2.id]))

    def test_invalid_value_type_returns_error(self):
        """Valor de tipo incorrecto para el atributo → error."""
        attr = mk_enum_attr("pcv_iv", ["A", "B"])
        cat  = mk_cat("PCV_InvVal")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod = mk_prod(cat.id, "PCV-IV-001")
            # "Z" no es un valor posible del enum
            result = ProductService.create_variant(prod.id, [{"attribute_id": attr.id, "value": "Z"}])
            assert "error" in result
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_multiple_variants_persist(self):
        """Tres variantes → todas guardadas."""
        attr = mk_enum_attr("pcv_mv", ["S", "M", "L"])
        cat  = mk_cat("PCV_MultiV")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod = mk_prod(cat.id, "PCV-MV-001")
            for val in ["S", "M", "L"]:
                ProductService.create_variant(prod.id, [{"attribute_id": attr.id, "value": val}])
            prod_after = ProductService.get(prod.id)
            assert len(prod_after.variants) == 3
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))


# ═══════════════════════════════════════════════════════════════════════════
# ProductService — del_variant
# ═══════════════════════════════════════════════════════════════════════════

class TestProductDelVariant:

    def test_del_variant_success(self):
        attr = mk_enum_attr("pdv_ok", ["X", "Y"])
        cat  = mk_cat("PDV_Ok")
        try:
            CategoryService.add_dynamic_attribute(cat.id, attr.id)
            prod   = mk_prod(cat.id, "PDV-OK-001")
            r      = mk_variant(prod.id, attr.id, "X")
            prod_id = r["product"].id
            var_id  = ProductService.get(prod_id).variants[0].id

            prod_after = ProductService.del_variant(prod_id, var_id)
            assert len(prod_after.variants) == 0
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]), ("attr", [attr.id]))

    def test_del_variant_not_found_raises(self):
        cat  = mk_cat("PDV_NF")
        prod = mk_prod(cat.id, "PDV-NF-001")
        try:
            with pytest.raises(ValueError, match="Variante"):
                ProductService.del_variant(prod.id, 999999)
        finally:
            cleanup(("prod", [prod.id]), ("cat", [cat.id]))
