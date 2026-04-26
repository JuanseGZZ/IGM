from app.models import Attribute, AttributeImplementation, Category, Product, Variant
from app.schemas import AttributeOut, CategoryOut, ImplOut, VariantOut, ProductOut


def attr_out(a: Attribute) -> AttributeOut:
    return AttributeOut(
        id=a.id, key=a.key, name=a.name,
        data_type=a.data_type, is_static=a.is_static,
        enum_values=list(a.enum_values),
    )

def cat_out(cat: Category) -> CategoryOut:
    return CategoryOut(
        id=cat.id, name=cat.name,
        father_id=cat.father_categorie.id if cat.father_categorie else None,
        attributes=[attr_out(a) for a in cat.attributes],
    )

def impl_out(impl: AttributeImplementation) -> ImplOut:
    return ImplOut(id=impl.id, attribute=attr_out(impl.attribute), value=impl.value)

def variant_out(v: Variant) -> VariantOut:
    return VariantOut(
        id=v.id,
        attribute_implementations=[impl_out(i) for i in v.attribute_implementations],
    )

def product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id, code=p.code, title=p.title,
        price=p.price, description=p.description, brand=p.brand,
        category_id=p.category.id,
        attributes_implementations=[impl_out(i) for i in p.attributes_implementations],
        variants=[variant_out(v) for v in p.variants],
    )
