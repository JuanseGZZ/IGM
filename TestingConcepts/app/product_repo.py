from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase
from attributes_repo import AttributeRepo
from models import Product, Category, Variant, Attribute, AttributeImplementation


class ProductRepo(CrudBase[Product]):
    TABLE = "product"
    MODEL_CLASS = Product

    @classmethod
    def _obj_to_row(cls, obj: Product):
        return {
            "id": obj.id,
            "code": obj.code,
            "title": obj.title,
            "price": obj.price,
            "description": obj.description,
            "brand": obj.brand,
            "category_id": obj.category.id,
        }

    @classmethod
    def _load_category_attributes(cls, category_id: int) -> list:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT a.id, a.key, a.name, a.data_type, a.is_static
                FROM category_atributes ca
                JOIN atribute a ON a.id = ca.atribute_id
                WHERE ca.category_id = %s
                ORDER BY ca.id
                """,
                (category_id,),
            )
            rows = cur.fetchall()

        attributes = []
        for row in rows:
            attribute = AttributeRepo.read(row["id"])
            if attribute is None:
                attribute = Attribute(
                    id=row["id"],
                    key=row["key"],
                    name=row["name"],
                    data_type=row["data_type"],
                    is_static=row["is_static"],
                )
            attributes.append(attribute)

        return attributes

    @classmethod
    def _load_category(cls, category_id: int):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, name
                FROM category
                WHERE id = %s
                """,
                (category_id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return Category(
            id=row["id"],
            name=row["name"],
            attributes=cls._load_category_attributes(category_id),
        )

    @classmethod
    def _resolve_attribute(cls, attribute_id: int, fallback_row: dict | None = None):
        attribute = AttributeRepo.read(attribute_id)
        if attribute is not None:
            return attribute

        if fallback_row is None:
            return None

        return Attribute(
            id=fallback_row["attribute_id"],
            key=fallback_row["key"],
            name=fallback_row["name"],
            data_type=fallback_row["data_type"],
            is_static=fallback_row["is_static"],
        )

    @classmethod
    def _load_variant_implementations(cls, variant_id: int):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    ai.id AS implementation_id,
                    ai.value,
                    a.id AS attribute_id,
                    a.key,
                    a.name,
                    a.data_type,
                    a.is_static
                FROM variant_implementation vi
                JOIN atr_implementation ai ON ai.id = vi.atr_imp_id
                JOIN atribute a ON a.id = ai.atribute_id
                WHERE vi.variant_id = %s
                ORDER BY ai.id
                """,
                (variant_id,),
            )
            rows = cur.fetchall()

        implementations = []

        for row in rows:
            attribute = cls._resolve_attribute(row["attribute_id"], row)

            implementation = AttributeImplementation(
                id=row["implementation_id"],
                attribute=attribute,
                value=row["value"],
            )

            implementations.append(implementation)

        return implementations

    @classmethod
    def _load_product_attributes(cls, product_id: int):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT a.id, a.key, a.name, a.data_type, a.is_static
                FROM products_atributes pa
                JOIN atribute a ON a.id = pa.atribute_id
                WHERE pa.product_id = %s
                ORDER BY pa.id
                """,
                (product_id,),
            )
            rows = cur.fetchall()

        attributes = []
        for row in rows:
            attribute = AttributeRepo.read(row["id"])
            if attribute is None:
                attribute = Attribute(
                    id=row["id"],
                    key=row["key"],
                    name=row["name"],
                    data_type=row["data_type"],
                    is_static=row["is_static"],
                )
            attributes.append(attribute)

        return attributes

    @classmethod
    def _load_product_implementations(cls, product_id: int):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT
                    ai.id AS implementation_id,
                    ai.value,
                    a.id AS attribute_id,
                    a.key,
                    a.name,
                    a.data_type,
                    a.is_static
                FROM product_implementation pi
                JOIN atr_implementation ai ON ai.id = pi.atr_imp_id
                JOIN atribute a ON a.id = ai.atribute_id
                WHERE pi.product_id = %s
                ORDER BY pi.id
                """,
                (product_id,),
            )
            rows = cur.fetchall()

        implementations = []
        for row in rows:
            attribute = cls._resolve_attribute(row["attribute_id"], row)

            implementations.append(
                AttributeImplementation(
                    id=row["implementation_id"],
                    attribute=attribute,
                    value=row["value"],
                )
            )

        return implementations

    @classmethod
    def _load_variants(cls, product: Product):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, code, product_id
                FROM variant
                WHERE product_id = %s
                ORDER BY id
                """,
                (product.id,),
            )
            rows = cur.fetchall()

        variants = []

        for row in rows:
            implementations = cls._load_variant_implementations(row["id"])

            variant = Variant(
                id=row["id"],
                attribute_implementations=implementations,
            )

            variants.append(variant)

        return variants

    @classmethod
    def _save_variants(cls, product: Product):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT DISTINCT vi.atr_imp_id
                FROM variant v
                JOIN variant_implementation vi ON vi.variant_id = v.id
                WHERE v.product_id = %s
                """,
                (product.id,),
            )
            old_implementation_rows = cur.fetchall()

            for row in old_implementation_rows:
                cur.execute(
                    "DELETE FROM atr_implementation WHERE id = %s",
                    (row["atr_imp_id"],),
                )

            cur.execute(
                "DELETE FROM variant WHERE product_id = %s",
                (product.id,),
            )

            for index, variant in enumerate(product.variants, start=1):
                variant_code = f"{product.code}-v{index}"

                cur.execute(
                    """
                    INSERT INTO variant (code, product_id)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (variant_code, product.id),
                )
                variant_row = cur.fetchone()
                variant.id = variant_row["id"]

                for implementation in variant.attribute_implementations:
                    cur.execute(
                        """
                        INSERT INTO atr_implementation (atribute_id, value)
                        VALUES (%s, %s)
                        RETURNING id
                        """,
                        (implementation.attribute.id, str(implementation.value)),
                    )
                    implementation_row = cur.fetchone()
                    implementation.id = implementation_row["id"]

                    cur.execute(
                        """
                        INSERT INTO variant_implementation (variant_id, atr_imp_id)
                        VALUES (%s, %s)
                        """,
                        (variant.id, implementation.id),
                    )

    @classmethod
    def _save_product_attributes(cls, product: Product):
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM products_atributes WHERE product_id = %s",
                (product.id,),
            )

            for attribute in product.attributes:
                if attribute.id is None:
                    raise ValueError("No se puede asociar un atributo sin id al producto")

                cur.execute(
                    """
                    INSERT INTO products_atributes (product_id, atribute_id)
                    VALUES (%s, %s)
                    """,
                    (product.id, attribute.id),
                )

    @classmethod
    def _save_product_implementations(cls, product: Product):
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT atr_imp_id FROM product_implementation WHERE product_id = %s",
                (product.id,),
            )
            old_rows = cur.fetchall()

            cur.execute(
                "DELETE FROM product_implementation WHERE product_id = %s",
                (product.id,),
            )

            for row in old_rows:
                cur.execute(
                    "DELETE FROM atr_implementation WHERE id = %s",
                    (row["atr_imp_id"],),
                )

            for implementation in product.attributes_implementations:
                if implementation.attribute is None or implementation.attribute.id is None:
                    raise ValueError("No se puede guardar implementacion sin atributo con id")

                cur.execute(
                    """
                    INSERT INTO atr_implementation (atribute_id, value)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (implementation.attribute.id, str(implementation.value)),
                )
                implementation_row = cur.fetchone()
                implementation.id = implementation_row["id"]

                cur.execute(
                    """
                    INSERT INTO product_implementation (product_id, atr_imp_id)
                    VALUES (%s, %s)
                    """,
                    (product.id, implementation.id),
                )

    @classmethod
    def _row_to_obj(cls, row):
        if row is None:
            return None

        category = cls._load_category(row["category_id"])
        if category is None:
            raise ValueError("No existe la categoria del producto")

        product = Product(
            id=row["id"],
            code=row["code"],
            title=row["title"],
            price=float(row["price"]),
            description=row["description"],
            brand=row["brand"],
            category=category,
            attributes_implementations=cls._load_product_implementations(row["id"]),
            attributes=cls._load_product_attributes(row["id"]),
            variants=[],
        )

        product.variants = cls._load_variants(product)
        return product


    @classmethod
    def read_by_code(cls, code: str) -> Product | None:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, code, title, price, description, brand, category_id
                FROM product
                WHERE code = %s
                """,
                (code,),
            )
            row = cur.fetchone()

        return cls._row_to_obj(row)

    @classmethod
    def save(cls, obj: Product) -> Product:
        saved = super().save(obj)

        obj.id = saved.id
        obj.code = saved.code

        for variant in obj.variants:
            variant.product = obj

        cls._save_product_attributes(obj)
        cls._save_product_implementations(obj)
        cls._save_variants(obj)
        conn.commit()
        return cls.read(saved.id)