from __future__ import annotations

import os
from typing import Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection as Connection

# ============================================================
# Conexión
# ============================================================

def get_connection() -> Connection:
    return psycopg2.connect(
        host=os.getenv("DB_HOST",     "localhost"),
        port=os.getenv("DB_PORT",     "5432"),
        dbname=os.getenv("DB_NAME",   "productos"),
        user=os.getenv("DB_USER",     "postgres"),
        password=os.getenv("DB_PASSWORD", "13adsASD21."),
    )


# ============================================================
# BaseCRUD
# ============================================================

class BaseCRUD:
    table: str  # cada subclase define su tabla

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    # ── helpers internos ──────────────────────────────────────

    def _cursor(self) -> RealDictCursor:
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def _commit(self) -> None:
        self.conn.commit()

    def _rollback(self) -> None:
        self.conn.rollback()

    # ── CRUD base ────────────────────────────────────────────

    def get_all(self) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(f"SELECT * FROM {self.table};")
            return [dict(row) for row in cur.fetchall()]

    def get_by_id(self, record_id: int) -> Optional[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                f"SELECT * FROM {self.table} WHERE id = %s;",
                (record_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        columns = list(data.keys())
        values  = list(data.values())
        cols_sql  = ", ".join(columns)
        vals_sql  = ", ".join(["%s"] * len(values))
        query = (
            f"INSERT INTO {self.table} ({cols_sql}) "
            f"VALUES ({vals_sql}) RETURNING *;"
        )
        try:
            with self._cursor() as cur:
                cur.execute(query, values)
                row = cur.fetchone()
            self._commit()
            return dict(row)
        except Exception:
            self._rollback()
            raise

    def update(self, record_id: int, data: dict[str, Any]) -> Optional[dict[str, Any]]:
        if not data:
            return self.get_by_id(record_id)
        columns = list(data.keys())
        values  = list(data.values())
        set_sql = ", ".join(f"{col} = %s" for col in columns)
        query = (
            f"UPDATE {self.table} SET {set_sql} "
            f"WHERE id = %s RETURNING *;"
        )
        try:
            with self._cursor() as cur:
                cur.execute(query, values + [record_id])
                row = cur.fetchone()
            self._commit()
            return dict(row) if row else None
        except Exception:
            self._rollback()
            raise

    def delete(self, record_id: int) -> bool:
        query = f"DELETE FROM {self.table} WHERE id = %s RETURNING id;"
        try:
            with self._cursor() as cur:
                cur.execute(query, (record_id,))
                deleted = cur.fetchone()
            self._commit()
            return deleted is not None
        except Exception:
            self._rollback()
            raise

    def filter_by(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Filtro simple por igualdad de columnas.
        Ejemplo: crud.filter_by(category_id=3, is_static=True)
        """
        if not kwargs:
            return self.get_all()
        conditions = " AND ".join(f"{col} = %s" for col in kwargs)
        values = list(kwargs.values())
        query = f"SELECT * FROM {self.table} WHERE {conditions};"
        with self._cursor() as cur:
            cur.execute(query, values)
            return [dict(row) for row in cur.fetchall()]


# ============================================================
# CRUDs de cada tabla
# ============================================================

class CategoryCRUD(BaseCRUD):
    table = "category"

    def get_by_name(self, name: str) -> Optional[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM category WHERE name = %s;",
                (name,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


class AtributeCRUD(BaseCRUD):
    table = "atribute"

    def get_by_key(self, key: str) -> Optional[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM atribute WHERE key = %s;",
                (key,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_static(self) -> list[dict[str, Any]]:
        return self.filter_by(is_static=True)

    def get_dynamic(self) -> list[dict[str, Any]]:
        return self.filter_by(is_static=False)


class EnumValuesCRUD(BaseCRUD):
    table = "enum_values"

    def get_by_atribute(self, atribute_id: int) -> list[dict[str, Any]]:
        return self.filter_by(atribute_id=atribute_id)


class CategoryAtributesCRUD(BaseCRUD):
    table = "category_atributes"

    def get_by_category(self, category_id: int) -> list[dict[str, Any]]:
        return self.filter_by(category_id=category_id)

    def get_by_atribute(self, atribute_id: int) -> list[dict[str, Any]]:
        return self.filter_by(atribute_id=atribute_id)

    def get_atributes_of_category(self, category_id: int) -> list[dict[str, Any]]:
        """Devuelve los atributos completos de una categoría (join)."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT a.*
                FROM atribute a
                JOIN category_atributes ca ON ca.atribute_id = a.id
                WHERE ca.category_id = %s;
                """,
                (category_id,),
            )
            return [dict(row) for row in cur.fetchall()]


class ProductCRUD(BaseCRUD):
    table = "product"

    def get_by_code(self, code: str) -> Optional[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM product WHERE code = %s;",
                (code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_category(self, category_id: int) -> list[dict[str, Any]]:
        return self.filter_by(category_id=category_id)

    def get_by_brand(self, brand: str) -> list[dict[str, Any]]:
        return self.filter_by(brand=brand)


class ProductsAtributesCRUD(BaseCRUD):
    table = "products_atributes"

    def get_by_product(self, product_id: int) -> list[dict[str, Any]]:
        return self.filter_by(product_id=product_id)

    def get_atributes_of_product(self, product_id: int) -> list[dict[str, Any]]:
        """Devuelve los atributos completos de un producto (join)."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT a.*
                FROM atribute a
                JOIN products_atributes pa ON pa.atribute_id = a.id
                WHERE pa.product_id = %s;
                """,
                (product_id,),
            )
            return [dict(row) for row in cur.fetchall()]


class AtrImplementationCRUD(BaseCRUD):
    table = "atr_implementation"

    def get_by_atribute(self, atribute_id: int) -> list[dict[str, Any]]:
        return self.filter_by(atribute_id=atribute_id)


class ProductImplementationCRUD(BaseCRUD):
    table = "product_implementation"

    def get_by_product(self, product_id: int) -> list[dict[str, Any]]:
        return self.filter_by(product_id=product_id)

    def get_full_implementation(self, product_id: int) -> list[dict[str, Any]]:
        """Devuelve las implementaciones de un producto con nombre y valor del atributo."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT
                    pi.id             AS impl_id,
                    a.key             AS atribute_key,
                    a.name            AS atribute_name,
                    a.data_type,
                    ai.value
                FROM product_implementation pi
                JOIN atr_implementation ai ON ai.id = pi.atr_imp_id
                JOIN atribute a            ON a.id  = ai.atribute_id
                WHERE pi.product_id = %s;
                """,
                (product_id,),
            )
            return [dict(row) for row in cur.fetchall()]


class VariantCRUD(BaseCRUD):
    table = "variant"

    def get_by_code(self, code: str) -> Optional[dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM variant WHERE code = %s;",
                (code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_product(self, product_id: int) -> list[dict[str, Any]]:
        return self.filter_by(product_id=product_id)


class VariantImplementationCRUD(BaseCRUD):
    table = "variant_implementation"

    def get_by_variant(self, variant_id: int) -> list[dict[str, Any]]:
        return self.filter_by(variant_id=variant_id)

    def get_full_implementation(self, variant_id: int) -> list[dict[str, Any]]:
        """Devuelve las implementaciones de una variante con nombre y valor del atributo."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT
                    vi.id             AS impl_id,
                    a.key             AS atribute_key,
                    a.name            AS atribute_name,
                    a.data_type,
                    ai.value
                FROM variant_implementation vi
                JOIN atr_implementation ai ON ai.id = vi.atr_imp_id
                JOIN atribute a            ON a.id  = ai.atribute_id
                WHERE vi.variant_id = %s;
                """,
                (variant_id,),
            )
            return [dict(row) for row in cur.fetchall()]


# ============================================================
# Factory — acceso único desde el repository
# ============================================================

class DB:
    """Punto de entrada. Abre una conexión y expone todos los CRUDs.

    Uso:
        with DB() as db:
            product = db.product.get_by_code("SKU-001")
            variants = db.variant.get_by_product(product["id"])
    """

    def __init__(self, conn: Optional[Connection] = None) -> None:
        self._external_conn = conn is not None
        self.conn: Connection = conn or get_connection()

        self.category               = CategoryCRUD(self.conn)
        self.atribute               = AtributeCRUD(self.conn)
        self.enum_values            = EnumValuesCRUD(self.conn)
        self.category_atributes     = CategoryAtributesCRUD(self.conn)
        self.product                = ProductCRUD(self.conn)
        self.products_atributes     = ProductsAtributesCRUD(self.conn)
        self.atr_implementation     = AtrImplementationCRUD(self.conn)
        self.product_implementation = ProductImplementationCRUD(self.conn)
        self.variant                = VariantCRUD(self.conn)
        self.variant_implementation = VariantImplementationCRUD(self.conn)

    def __enter__(self) -> "DB":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._external_conn:
            self.conn.close()