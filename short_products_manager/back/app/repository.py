from .db import BaseRepository


class BrandRepository(BaseRepository):
    table = "brands"
    create_sql = """
        CREATE TABLE IF NOT EXISTS brands (
            id   TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """


class ProductRepository(BaseRepository):
    table = "products"
    create_sql = """
        CREATE TABLE IF NOT EXISTS products (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            brand_id    TEXT
        )
    """


class AttributeRepository(BaseRepository):
    table = "attributes"
    create_sql = """
        CREATE TABLE IF NOT EXISTS attributes (
            id          TEXT PRIMARY KEY,
            product_id  TEXT NOT NULL,
            key         TEXT NOT NULL,
            attr_values TEXT NOT NULL DEFAULT '[]'
        )
    """

    def get_by_product(self, product_id: str) -> list[dict]:
        return self.get_by_field("product_id", product_id)

    def delete_by_product(self, product_id: str) -> None:
        from .db import _conn
        with _conn(self._db) as conn:
            conn.execute("DELETE FROM attributes WHERE product_id = ?", (product_id,))


class VariantRepository(BaseRepository):
    table = "variants"
    create_sql = """
        CREATE TABLE IF NOT EXISTS variants (
            id              TEXT PRIMARY KEY,
            product_id      TEXT NOT NULL,
            price           REAL NOT NULL DEFAULT 0,
            implementations TEXT NOT NULL DEFAULT '[]'
        )
    """

    def get_by_product(self, product_id: str) -> list[dict]:
        return self.get_by_field("product_id", product_id)

    def delete_by_product(self, product_id: str) -> None:
        from .db import _conn
        with _conn(self._db) as conn:
            conn.execute("DELETE FROM variants WHERE product_id = ?", (product_id,))
