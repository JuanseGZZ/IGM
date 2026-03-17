from category_repo import CategoryRepo
from attributes_repo import AttributeRepo
from product_repo import ProductRepo
from models import Category, Attribute, AttributeImplementation, Product, Variant


def main():
    print("1. crear category")
    category = Category(
        id=None,
        name="Ropa",
        attributes=[],
    )
    saved_category = CategoryRepo.save(category)
    print("category:", saved_category.id, saved_category.name)

    print("\n2. crear attributes")
    color_attr = Attribute(
        id=None,
        key="color",
        name="Color",
        data_type="string",
        is_static=False,
    )
    saved_color_attr = AttributeRepo.save(color_attr)
    print("attribute color:", saved_color_attr.id, saved_color_attr.name)

    size_attr = Attribute(
        id=None,
        key="size",
        name="Talle",
        data_type="string",
        is_static=False,
    )
    saved_size_attr = AttributeRepo.save(size_attr)
    print("attribute size:", saved_size_attr.id, saved_size_attr.name)

    print("\n3. crear product con variants")
    product = Product(
        id=None,
        code="remera-001",
        title="Remera basica",
        price=19999.90,
        description="Remera de algodon",
        brand="MarcaX",
        category=saved_category,
        attributes_implementations=[],
        attributes=[],
        variants=[],
    )

    variant_1 = Variant(
        id=None,
        product=product,
        attribute_implementations=[
            AttributeImplementation(
                id=None,
                attribute=saved_color_attr,
                value="rojo",
            ),
            AttributeImplementation(
                id=None,
                attribute=saved_size_attr,
                value="M",
            ),
        ],
    )

    variant_2 = Variant(
        id=None,
        product=product,
        attribute_implementations=[
            AttributeImplementation(
                id=None,
                attribute=saved_color_attr,
                value="azul",
            ),
            AttributeImplementation(
                id=None,
                attribute=saved_size_attr,
                value="L",
            ),
        ],
    )

    product.variants = [variant_1, variant_2]

    saved_product = ProductRepo.save(product)
    print("product:", saved_product.id, saved_product.code, saved_product.title)

    print("\n4. leer product")
    found = ProductRepo.read(saved_product.id)

    print("product leido:")
    print("id:", found.id)
    print("code:", found.code)
    print("title:", found.title)
    print("price:", found.price)
    print("category:", found.category.id, found.category.name)

    print("\nvariants:")
    for variant in found.variants:
        print("variant id:", variant.id)
        for implementation in variant.attribute_implementations:
            print(
                "  impl:",
                implementation.id,
                implementation.attribute.name,
                "=",
                implementation.value,
            )

    input("Borramos ?")

    print("\n5. borrar product")
    deleted = ProductRepo.delete(saved_product.id)
    print("product borrado:", deleted)

    print("\n6. comprobar lectura")
    again = ProductRepo.read(saved_product.id)
    print("resultado:", again)


if __name__ == "__main__":
    main()