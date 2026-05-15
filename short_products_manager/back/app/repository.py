from .db import BaseRepository, DB_PATH


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
            brand_id    TEXT,
            photo       TEXT
        )
    """

    def __init__(self, db_path: str = DB_PATH) -> None:
        super().__init__(db_path)
        from .db import _conn
        with _conn(self._db) as conn:
            try:
                conn.execute("ALTER TABLE products ADD COLUMN photo TEXT")
            except Exception:
                pass  # column already exists


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


class StockRepository(BaseRepository):
    table = "stocks"
    create_sql = """
        CREATE TABLE IF NOT EXISTS stocks (
            id              TEXT PRIMARY KEY,
            variant_id      TEXT NOT NULL,
            quantity        REAL NOT NULL DEFAULT 0,
            date            TEXT NOT NULL,
            cost_unit_price REAL NOT NULL DEFAULT 0
        )
    """

    def get_by_variant(self, variant_id: str) -> list[dict]:
        return self.get_by_field("variant_id", variant_id)


class VariantRepository(BaseRepository):
    table = "variants"
    create_sql = """
        CREATE TABLE IF NOT EXISTS variants (
            id              TEXT PRIMARY KEY,
            product_id      TEXT NOT NULL,
            price           REAL NOT NULL DEFAULT 0,
            implementations TEXT NOT NULL DEFAULT '[]',
            oferta          REAL
        )
    """

    def __init__(self, db_path: str = DB_PATH) -> None:
        super().__init__(db_path)
        from .db import _conn
        with _conn(self._db) as conn:
            try:
                conn.execute("ALTER TABLE variants ADD COLUMN oferta REAL")
            except Exception:
                pass  # column already exists

    def get_by_product(self, product_id: str) -> list[dict]:
        return self.get_by_field("product_id", product_id)

    def delete_by_product(self, product_id: str) -> None:
        from .db import _conn
        with _conn(self._db) as conn:
            conn.execute("DELETE FROM variants WHERE product_id = ?", (product_id,))
