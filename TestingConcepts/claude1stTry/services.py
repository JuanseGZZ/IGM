from models import Attribute, Category, Product, AttributeImplementation
from attributes_repo import AttributeRepo
from category_repo import CategoryRepo
from product_repo import ProductRepo
from dtos import (
    AttributeCreate, AttributeUpdate,
    CategoryCreate, CategoryUpdate,
    ProductCreate, ProductUpdate,
    VariantIn,
)

VALID_DATA_TYPES = {"text", "number", "boolean", "enum"}


def _resolve_is_static(data_type: str, requested: bool) -> bool:
    """
    Regla de negocio: text y number siempre estaticos, boolean siempre dinamico,
    enum lo elige el usuario.
    """
    if data_type in ("text", "number"):
        return True
    if data_type == "boolean":
        return False
    return requested  # enum


def _load_attribute_or_raise(attr_id: int) -> Attribute:
    attr = AttributeRepo.read(attr_id)
    if attr is None:
        raise ValueError(f"Atributo {attr_id} no encontrado")
    return attr


def _load_category_or_raise(cat_id: int) -> Category:
    cat = CategoryRepo.read(cat_id)
    if cat is None:
        raise ValueError(f"Categoría {cat_id} no encontrada")
    return cat


def _load_product_or_raise(prod_id: int) -> Product:
    product = ProductRepo.read(prod_id)
    if product is None:
        raise ValueError(f"Producto {prod_id} no encontrado")
    # ProductRepo carga la categoría sin sus atributos; recargamos desde CategoryRepo
    # para que la lógica de dominio (variantes, validaciones) funcione correctamente.
    product.category = _load_category_or_raise(product.category.id)
    return product


# ── Attribute Service ─────────────────────────────────────────────────────────

class AttributeService:

    @staticmethod
    def get_all() -> list[Attribute]:
        return AttributeRepo.bring_all()

    @staticmethod
    def get(attr_id: int) -> Attribute:
        return _load_attribute_or_raise(attr_id)

    @staticmethod
    def create(dto: AttributeCreate) -> Attribute:
        if dto.data_type not in VALID_DATA_TYPES:
            raise ValueError(f"data_type inválido: {dto.data_type}")

        is_static = _resolve_is_static(dto.data_type, dto.is_static)
        attr = Attribute(key=dto.key, name=dto.name, data_type=dto.data_type, is_static=is_static)

        if dto.data_type == "enum":
            for v in dto.enum_values:
                attr.add_enum_value(v)

        return AttributeRepo.save(attr)

    @staticmethod
    def update(attr_id: int, dto: AttributeUpdate) -> Attribute:
        attr = _load_attribute_or_raise(attr_id)
        attr.name = dto.name
        attr.is_static = _resolve_is_static(attr.data_type, dto.is_static)

        if attr.data_type == "enum":
            attr.enum_values = []
            for v in dto.enum_values:
                attr.add_enum_value(v)

        return AttributeRepo.save(attr)

    @staticmethod
    def delete(attr_id: int) -> bool:
        return AttributeRepo.delete(attr_id)


# ── Category Service ──────────────────────────────────────────────────────────

class CategoryService:

    @staticmethod
    def get_all() -> list[Category]:
        return CategoryRepo.bring_all()

    @staticmethod
    def get(cat_id: int) -> Category:
        return _load_category_or_raise(cat_id)

    @staticmethod
    def create(dto: CategoryCreate) -> Category:
        cat = Category(name=dto.name)
        for attr_id in dto.attribute_ids:
            cat.add_attribute(_load_attribute_or_raise(attr_id))
        return CategoryRepo.save(cat)

    @staticmethod
    def update(cat_id: int, dto: CategoryUpdate) -> Category:
        cat = _load_category_or_raise(cat_id)
        cat.name = dto.name
        cat.attributes = []
        for attr_id in dto.attribute_ids:
            cat.add_attribute(_load_attribute_or_raise(attr_id))
        return CategoryRepo.save(cat)

    @staticmethod
    def delete(cat_id: int) -> bool:
        return CategoryRepo.delete(cat_id)


# ── Product Service ───────────────────────────────────────────────────────────

class ProductService:

    @staticmethod
    def get_all() -> list[Product]:
        return ProductRepo.bring_all()

    @staticmethod
    def get(prod_id: int) -> Product:
        return _load_product_or_raise(prod_id)

    @staticmethod
    def create(dto: ProductCreate) -> Product:
        cat = _load_category_or_raise(dto.category_id)

        product = Product(
            code=dto.code,
            title=dto.title,
            price=dto.price,
            description=dto.description,
            brand=dto.brand,
            category=cat,
        )

        for attr_id in dto.attribute_ids:
            product.add_attribute(_load_attribute_or_raise(attr_id))

        for impl_dto in dto.static_implementations:
            attr = _load_attribute_or_raise(impl_dto.attribute_id)
            impl = AttributeImplementation(attribute=attr, value=impl_dto.value)
            product.add_product_implementation(impl)

        return ProductRepo.save(product)

    @staticmethod
    def update(prod_id: int, dto: ProductUpdate) -> Product:
        product = _load_product_or_raise(prod_id)

        if product.category.id != dto.category_id:
            product.category = _load_category_or_raise(dto.category_id)

        product.title = dto.title
        product.price = dto.price
        product.description = dto.description
        product.brand = dto.brand

        product.attributes = []
        for attr_id in dto.attribute_ids:
            product.add_attribute(_load_attribute_or_raise(attr_id))

        product.attributes_implementations = []
        for impl_dto in dto.static_implementations:
            attr = _load_attribute_or_raise(impl_dto.attribute_id)
            impl = AttributeImplementation(attribute=attr, value=impl_dto.value)
            product.add_product_implementation(impl)

        return ProductRepo.save(product)

    @staticmethod
    def delete(prod_id: int) -> bool:
        return ProductRepo.delete(prod_id)

    @staticmethod
    def add_variant(prod_id: int, dto: VariantIn) -> Product:
        product = _load_product_or_raise(prod_id)

        implementations = []
        for impl_dto in dto.implementations:
            attr = _load_attribute_or_raise(impl_dto.attribute_id)
            implementations.append(AttributeImplementation(attribute=attr, value=impl_dto.value))

        variant = product.create_variant_by_implementations(implementations)
        if variant is None:
            raise ValueError(
                "No se pudo crear la variante. "
                "Verificá que las implementaciones sean correctas y cubran todos los atributos dinámicos."
            )

        return ProductRepo.save(product)

    @staticmethod
    def delete_variant(prod_id: int, variant_id: int) -> Product:
        product = _load_product_or_raise(prod_id)

        original_count = len(product.variants)
        product.variants = [v for v in product.variants if v.id != variant_id]

        if len(product.variants) == original_count:
            raise ValueError(f"Variante {variant_id} no encontrada en producto {prod_id}")

        return ProductRepo.save(product)