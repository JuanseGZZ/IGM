from db_handler.repositories import AttributeRepo, CategoryRepo, ProductRepo, VariantRepo
from app.models import Attribute, Category, Product, Variant

_attr_repo = AttributeRepo()
_cat_repo  = CategoryRepo()
_prod_repo = ProductRepo()
_var_repo  = VariantRepo()


def get_category(cat_id: int) -> Category | None:
    return _cat_repo.get(cat_id)

def get_product(prod_id: int) -> Product | None:
    return _prod_repo.get(prod_id)

def get_attribute(attr_id: int) -> Attribute | None:
    return _attr_repo.get(attr_id)

def get_variant(var_id: int) -> Variant | None:
    return _var_repo.get(var_id)

def get_products_by_ids(ids: list[int]) -> dict[int, Product]:
    result = {}
    for i in ids:
        p = _prod_repo.get(i)
        if p:
            result[i] = p
    return result

def save_category(cat: Category) -> Category:
    return _cat_repo.save(cat)

def save_product(prod: Product) -> Product:
    return _prod_repo.save(prod)

def save_attribute(attr: Attribute) -> Attribute:
    return _attr_repo.save(attr)

def save_variant(variant: Variant, product_id: int) -> Variant:
    return _var_repo.save(variant, product_id)

def delete_category(cat_id: int) -> None:
    _cat_repo.delete(cat_id)

def delete_product(prod_id: int) -> None:
    _prod_repo.delete(prod_id)

def delete_attribute(attr_id: int) -> None:
    _attr_repo.delete(attr_id)

def delete_variant(var_id: int) -> None:
    _var_repo.delete(var_id)

def list_attributes() -> list[Attribute]:
    return _attr_repo.list_all()

def list_products() -> list[Product]:
    return _prod_repo.list_all()

def list_products_by_category(cat_id: int) -> list[Product]:
    return _prod_repo.list_by_category(cat_id)

def load_category_tree() -> dict[int, Category]:
    return _cat_repo.load_tree()
