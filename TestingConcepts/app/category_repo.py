from psycopg.rows import dict_row

from config import conn
from models import Category
from models import Attribute
from crud_base import CrudBase


class CategoryRepo(CrudBase[Category]):
    TABLE = "category"
    MODEL_CLASS = Category

    @classmethod
    def _obj_to_row(cls, obj: Category):
        return {
            "id": obj.id,
            "name": obj.name,
        }

    @classmethod
    def _load_attributes(cls, category_id: int) -> list[Attribute]:
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

        attributes: list[Attribute] = []
        for row in rows:
            attribute = Attribute(
                id=row["id"],
                key=row["key"],
                name=row["name"],
                data_type=row["data_type"],
                is_static=row["is_static"],
            )

            if attribute.data_type == "enum":
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT value
                        FROM enum_values
                        WHERE atribute_id = %s
                        ORDER BY id
                        """,
                        (attribute.id,),
                    )
                    attribute.enum_values = [value_row[0] for value_row in cur.fetchall()]

            attributes.append(attribute)

        return attributes

    @classmethod
    def _load_products(cls, category) -> list:
        from product_repo import ProductRepo

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, code, title, price, description, brand, category_id
                FROM product
                WHERE category_id = %s
                ORDER BY id
                """,
                (category.id,),
            )
            rows = cur.fetchall()

        products = []
        for row in rows:
            product = ProductRepo._row_to_obj(row)
            if product is not None:
                product.category = category
                products.append(product)

        return products

    @classmethod
    def _row_to_obj(cls, row):
        if row is None:
            return None

        category = Category(
            id=row["id"],
            name=row["name"],
            attributes=cls._load_attributes(row["id"]),
        )

        for product in cls._load_products(category):
            category.products.append(product)
            category._product_codes.add(product.code)

        return category

    @classmethod
    def save(cls, obj: Category) -> Category:
        saved = super().save(obj)

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM category_atributes WHERE category_id = %s",
                (saved.id,),
            )

            for attribute in obj.attributes:
                if attribute.id is None:
                    raise ValueError("No se puede asociar un atributo sin id a la categoria")

                cur.execute(
                    """
                    INSERT INTO category_atributes (category_id, atribute_id)
                    VALUES (%s, %s)
                    """,
                    (saved.id, attribute.id),
                )

        conn.commit()
        return cls.read(saved.id)