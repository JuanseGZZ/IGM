"""
testing_models_repos.py — Tests de integración: repos contra la BD real.

Verifica que cada repo serialice y deserialice correctamente los modelos,
incluyendo los fixes recientes:
  - ProductRepo._load_category carga attributes de la categoría
  - CategoryRepo._row_to_obj carga products

Para correr: pytest TestingConcepts/app/testing_models_repos.py -v
"""

import pytest
from models import Attribute, AttributeImplementation, Category, Variant, Product
from attributes_repo import AttributeRepo
from category_repo import CategoryRepo
from product_repo import ProductRepo
from config import conn


@pytest.fixture(autouse=True)
def rollback_on_error():
    """Hace rollback de la conexión global después de cada test para que
    un fallo no deje la transacción abortada y envenene los tests siguientes."""
    yield
    try:
        conn.rollback()
    except Exception:
        pass


# ─── helpers ────────────────────────────────────────────────────────────────

def mk_attr(key, data_type="text", is_static=True):
    return Attribute(key=key, name=key, data_type=data_type, is_static=is_static)

def mk_enum_attr(key, values, is_static=True):
    a = Attribute(key=key, name=key, data_type="enum", is_static=is_static)
    a.enum_values = list(values)
    return a

def mk_cat(name):
    return Category(name=name)

def mk_prod(code, cat, price=10.0):
    return Product(
        code=code, title=code, price=price,
        description="desc", brand="brand",
        category=cat,
    )


# ─── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def saved_attr():
    """Crea un atributo text, lo guarda y lo borra al terminar."""
    attr = AttributeRepo.save(mk_attr("test_text_key"))
    yield attr
    AttributeRepo.delete(attr.id)

@pytest.fixture
def saved_enum_attr():
    """Crea un atributo enum con valores, lo guarda y lo borra al terminar."""
    a = mk_enum_attr("test_enum_key", ["rojo", "azul", "verde"], is_static=False)
    saved = AttributeRepo.save(a)
    yield saved
    AttributeRepo.delete(saved.id)

@pytest.fixture
def saved_cat():
    """Crea una categoría sin atributos y la borra al terminar."""
    cat = CategoryRepo.save(mk_cat("TestCat"))
    yield cat
    CategoryRepo.delete(cat.id)

@pytest.fixture
def saved_cat_with_attr(saved_attr):
    """Crea una categoría con un atributo estático asociado."""
    cat = mk_cat("TestCatWithAttr")
    cat.attributes.append(saved_attr)
    cat._attribute_keys.add(saved_attr.key)
    saved = CategoryRepo.save(cat)
    yield saved
    CategoryRepo.delete(saved.id)

@pytest.fixture
def saved_product(saved_cat):
    """Crea un producto básico y lo borra al terminar."""
    prod = ProductRepo.save(mk_prod("TEST-001", saved_cat))
    yield prod
    ProductRepo.delete(prod.id)


# ─── AttributeRepo ──────────────────────────────────────────────────────────

class TestAttributeRepo:

    def test_save_and_read_text(self):
        attr = AttributeRepo.save(mk_attr("ar_text_key", data_type="text"))
        try:
            result = AttributeRepo.read(attr.id)
            assert result is not None
            assert result.key == "ar_text_key"
            assert result.data_type == "text"
            assert result.is_static is True
        finally:
            AttributeRepo.delete(attr.id)

    def test_save_and_read_number(self):
        attr = AttributeRepo.save(mk_attr("ar_num_key", data_type="number"))
        try:
            result = AttributeRepo.read(attr.id)
            assert result.data_type == "number"
        finally:
            AttributeRepo.delete(attr.id)

    def test_save_and_read_boolean(self):
        attr = AttributeRepo.save(mk_attr("ar_bool_key", data_type="boolean", is_static=False))
        try:
            result = AttributeRepo.read(attr.id)
            assert result.is_static is False
            assert result.data_type == "boolean"
        finally:
            AttributeRepo.delete(attr.id)

    def test_save_and_read_enum_with_values(self):
        a = mk_enum_attr("ar_enum_key", ["S", "M", "L", "XL"], is_static=False)
        saved = AttributeRepo.save(a)
        try:
            result = AttributeRepo.read(saved.id)
            assert result.data_type == "enum"
            assert set(result.enum_values) == {"S", "M", "L", "XL"}
        finally:
            AttributeRepo.delete(saved.id)

    def test_update_name(self, saved_attr):
        saved_attr.name = "nombre_actualizado"
        updated = AttributeRepo.save(saved_attr)
        assert updated.name == "nombre_actualizado"

    def test_delete(self):
        attr = AttributeRepo.save(mk_attr("ar_del_key"))
        attr_id = attr.id
        result = AttributeRepo.delete(attr_id)
        assert result is True
        assert AttributeRepo.read(attr_id) is None

    def test_delete_nonexistent_returns_false(self):
        assert AttributeRepo.delete(999999) is False

    def test_read_nonexistent_returns_none(self):
        assert AttributeRepo.read(999999) is None

    def test_bring_all_returns_list(self):
        attr = AttributeRepo.save(mk_attr("ar_all_key"))
        try:
            result = AttributeRepo.bring_all()
            assert isinstance(result, list)
            ids = [a.id for a in result]
            assert attr.id in ids
        finally:
            AttributeRepo.delete(attr.id)


# ─── CategoryRepo ───────────────────────────────────────────────────────────

class TestCategoryRepo:

    def test_save_and_read_bare(self):
        cat = CategoryRepo.save(mk_cat("CR_Bare"))
        try:
            result = CategoryRepo.read(cat.id)
            assert result is not None
            assert result.name == "CR_Bare"
            assert result.attributes == []
        finally:
            CategoryRepo.delete(cat.id)

    def test_save_with_attributes_and_read_back(self):
        attr = AttributeRepo.save(mk_attr("cr_attr_key", data_type="text"))
        cat = mk_cat("CR_WithAttr")
        cat.attributes.append(attr)
        cat._attribute_keys.add(attr.key)
        saved = CategoryRepo.save(cat)
        try:
            result = CategoryRepo.read(saved.id)
            assert len(result.attributes) == 1
            assert result.attributes[0].key == "cr_attr_key"
            # _attribute_keys cacheado correctamente
            assert "cr_attr_key" in result._attribute_keys
        finally:
            CategoryRepo.delete(saved.id)
            AttributeRepo.delete(attr.id)

    def test_read_loads_products(self):
        """
        FIX: CategoryRepo._row_to_obj ahora carga products desde la BD.
        Verificamos que al leer una categoría, sus productos aparecen.
        """
        cat = CategoryRepo.save(mk_cat("CR_WithProds"))
        prod = ProductRepo.save(mk_prod("CR-PROD-001", cat))
        try:
            result = CategoryRepo.read(cat.id)
            assert len(result.products) == 1
            assert result.products[0].code == "CR-PROD-001"
            assert "CR-PROD-001" in result._product_codes
        finally:
            ProductRepo.delete(prod.id)
            CategoryRepo.delete(cat.id)

    def test_update_name(self, saved_cat):
        saved_cat.name = "CatRenombrada"
        updated = CategoryRepo.save(saved_cat)
        assert updated.name == "CatRenombrada"

    def test_save_removes_old_attributes_on_update(self):
        attr1 = AttributeRepo.save(mk_attr("cr_upd_attr1"))
        attr2 = AttributeRepo.save(mk_attr("cr_upd_attr2"))
        cat = mk_cat("CR_UpdateAttrs")
        cat.attributes.append(attr1)
        cat._attribute_keys.add(attr1.key)
        saved = CategoryRepo.save(cat)
        try:
            # ahora actualizamos con solo attr2
            saved.attributes = [attr2]
            saved._attribute_keys = {attr2.key}
            updated = CategoryRepo.save(saved)
            assert len(updated.attributes) == 1
            assert updated.attributes[0].key == "cr_upd_attr2"
        finally:
            CategoryRepo.delete(saved.id)
            AttributeRepo.delete(attr1.id)
            AttributeRepo.delete(attr2.id)

    def test_bring_all_returns_list(self, saved_cat):
        result = CategoryRepo.bring_all()
        assert isinstance(result, list)
        assert any(c.id == saved_cat.id for c in result)


# ─── ProductRepo ────────────────────────────────────────────────────────────

class TestProductRepo:

    def test_save_and_read_basic(self, saved_cat):
        prod = ProductRepo.save(mk_prod("PR-001", saved_cat, price=99.99))
        try:
            result = ProductRepo.read(prod.id)
            assert result is not None
            assert result.code == "PR-001"
            assert result.price == 99.99
            assert result.category.id == saved_cat.id
        finally:
            ProductRepo.delete(prod.id)

    def test_read_by_code(self, saved_cat):
        prod = ProductRepo.save(mk_prod("PR-BYCODE", saved_cat))
        try:
            result = ProductRepo.read_by_code("PR-BYCODE")
            assert result is not None
            assert result.id == prod.id
        finally:
            ProductRepo.delete(prod.id)

    def test_read_by_code_nonexistent_returns_none(self):
        assert ProductRepo.read_by_code("NO-EXISTE-NUNCA") is None

    def test_category_attributes_loaded(self):
        """
        FIX: ProductRepo._load_category ahora carga los attributes de la categoría.
        Verificamos que product.get_attributes() incluye los attrs de la categoría.
        """
        attr = AttributeRepo.save(mk_attr("pr_cat_attr", data_type="text"))
        cat = mk_cat("PR_CatWithAttr")
        cat.attributes.append(attr)
        cat._attribute_keys.add(attr.key)
        saved_cat = CategoryRepo.save(cat)

        prod = ProductRepo.save(mk_prod("PR-CATATTR-001", saved_cat))
        try:
            result = ProductRepo.read(prod.id)
            all_attr_keys = {a.key for a in result.get_attributes()}
            assert "pr_cat_attr" in all_attr_keys, (
                "El atributo de la categoría no se cargó en product.category.attributes"
            )
        finally:
            ProductRepo.delete(prod.id)
            CategoryRepo.delete(saved_cat.id)
            AttributeRepo.delete(attr.id)

    def test_save_with_static_attribute_implementation(self):
        attr = AttributeRepo.save(mk_attr("pr_static_attr", data_type="text", is_static=True))
        cat = mk_cat("PR_StaticCat")
        cat.attributes.append(attr)
        cat._attribute_keys.add(attr.key)
        saved_cat = CategoryRepo.save(cat)

        prod = mk_prod("PR-STATIC-001", saved_cat)
        impl = AttributeImplementation(attribute=attr, value="algodón")
        prod.attributes_implementations.append(impl)
        prod._impl_keys.add(attr.key)

        saved_prod = ProductRepo.save(prod)
        try:
            result = ProductRepo.read(saved_prod.id)
            assert len(result.attributes_implementations) == 1
            assert result.attributes_implementations[0].value == "algodón"
            assert result.attributes_implementations[0].attribute.key == "pr_static_attr"
        finally:
            ProductRepo.delete(saved_prod.id)
            CategoryRepo.delete(saved_cat.id)
            AttributeRepo.delete(attr.id)

    def test_save_with_own_dynamic_attribute(self):
        enum_attr = AttributeRepo.save(mk_enum_attr("pr_dyn_attr", ["rojo", "azul"], is_static=False))
        cat = CategoryRepo.save(mk_cat("PR_DynCat"))

        prod = mk_prod("PR-DYN-001", cat)
        prod.attributes.append(enum_attr)
        prod._attribute_keys.add(enum_attr.key)

        saved_prod = ProductRepo.save(prod)
        try:
            result = ProductRepo.read(saved_prod.id)
            own_keys = {a.key for a in result.attributes}
            assert "pr_dyn_attr" in own_keys
        finally:
            ProductRepo.delete(saved_prod.id)
            CategoryRepo.delete(cat.id)
            AttributeRepo.delete(enum_attr.id)

    def test_save_and_read_with_variants(self):
        enum_attr = AttributeRepo.save(mk_enum_attr("pr_var_attr", ["S", "M", "L"], is_static=False))
        cat = CategoryRepo.save(mk_cat("PR_VarCat"))

        prod = mk_prod("PR-VAR-001", cat)
        prod.attributes.append(enum_attr)
        prod._attribute_keys.add(enum_attr.key)

        for size in ["S", "M", "L"]:
            impl = AttributeImplementation(attribute=enum_attr, value=size)
            variant = Variant(attribute_implementations=[impl])
            prod.variants.append(variant)

        saved_prod = ProductRepo.save(prod)
        try:
            result = ProductRepo.read(saved_prod.id)
            assert len(result.variants) == 3
            values = {
                impl.value
                for v in result.variants
                for impl in v.attribute_implementations
            }
            assert values == {"S", "M", "L"}
        finally:
            ProductRepo.delete(saved_prod.id)
            CategoryRepo.delete(cat.id)
            AttributeRepo.delete(enum_attr.id)

    def test_update_product_price(self, saved_product):
        saved_product.price = 250.0
        updated = ProductRepo.save(saved_product)
        assert updated.price == 250.0

    def test_delete(self, saved_cat):
        prod = ProductRepo.save(mk_prod("PR-DEL-001", saved_cat))
        prod_id = prod.id
        ProductRepo.delete(prod_id)
        assert ProductRepo.read(prod_id) is None

    def test_bring_all_returns_list(self, saved_product):
        result = ProductRepo.bring_all()
        assert isinstance(result, list)
        assert any(p.id == saved_product.id for p in result)


# ─── Integración cruzada: modelo ↔ repo ──────────────────────────────────────

class TestIntegration:

    def test_category_get_attributes_after_round_trip(self):
        """
        product.category.get_attributes() devuelve los atributos correctos
        luego de un ciclo completo save → read.
        """
        attr_cat = AttributeRepo.save(mk_attr("int_cat_attr", data_type="text"))
        cat = mk_cat("INT_Cat")
        cat.attributes.append(attr_cat)
        cat._attribute_keys.add(attr_cat.key)
        saved_cat = CategoryRepo.save(cat)

        prod = ProductRepo.save(mk_prod("INT-PROD-001", saved_cat))
        try:
            result = ProductRepo.read(prod.id)
            keys = {a.key for a in result.category.get_attributes()}
            assert "int_cat_attr" in keys
        finally:
            ProductRepo.delete(prod.id)
            CategoryRepo.delete(saved_cat.id)
            AttributeRepo.delete(attr_cat.id)

    def test_category_read_products_match_product_read(self):
        """
        El producto leído desde CategoryRepo.read() coincide con el leído desde ProductRepo.read().
        """
        cat = CategoryRepo.save(mk_cat("INT_CatProds"))
        prod = ProductRepo.save(mk_prod("INT-CPROD-001", cat))
        try:
            cat_result = CategoryRepo.read(cat.id)
            assert len(cat_result.products) == 1
            cat_prod = cat_result.products[0]

            prod_result = ProductRepo.read(prod.id)
            assert cat_prod.id == prod_result.id
            assert cat_prod.code == prod_result.code
            assert cat_prod.price == prod_result.price
        finally:
            ProductRepo.delete(prod.id)
            CategoryRepo.delete(cat.id)

    def test_needed_attributes_after_round_trip(self):
        """
        product.get_needed_atributes_implementations() devuelve los atributos
        de la categoría correctamente luego del ciclo save → read.
        """
        static_attr = AttributeRepo.save(mk_attr("int_needed_static", data_type="text", is_static=True))
        dyn_attr = AttributeRepo.save(mk_enum_attr("int_needed_dyn", ["x", "y"], is_static=False))

        cat = mk_cat("INT_NeededCat")
        cat.attributes += [static_attr, dyn_attr]
        cat._attribute_keys = {static_attr.key, dyn_attr.key}
        saved_cat = CategoryRepo.save(cat)

        prod = ProductRepo.save(mk_prod("INT-NEEDED-001", saved_cat))
        try:
            result = ProductRepo.read(prod.id)
            static_needed = {a.key for a in result.get_needed_atributes_implementations(is_static=True)}
            dyn_needed = {a.key for a in result.get_needed_atributes_implementations(is_static=False)}
            assert "int_needed_static" in static_needed
            assert "int_needed_dyn" in dyn_needed
        finally:
            ProductRepo.delete(prod.id)
            CategoryRepo.delete(saved_cat.id)
            AttributeRepo.delete(static_attr.id)
            AttributeRepo.delete(dyn_attr.id)
