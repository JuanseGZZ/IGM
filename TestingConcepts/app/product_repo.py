from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase
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
            attributes=[],
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
            attribute = Attribute(
                id=row["attribute_id"],
                key=row["key"],
                name=row["name"],
                data_type=row["data_type"],
                is_static=row["is_static"],
            )

            implementation = AttributeImplementation(
                id=row["implementation_id"],
                attribute=attribute,
                value=row["value"],
            )

            implementations.append(implementation)

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
            attributes_implementations=[],
            attributes=[],
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

        cls._save_variants(obj)
        conn.commit()
        return cls.read(saved.id)