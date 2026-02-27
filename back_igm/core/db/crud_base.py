from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Type, TypeVar

from psycopg import sql
from psycopg.rows import dict_row

from config import conn


class SchemaError(RuntimeError):
    pass


@dataclass(frozen=True)
class TableMeta:
    schema: str
    table: str
    columns: List[str]
    pk: str


def _read_table_meta(schema: str, table: str) -> TableMeta:
    # Columnas en orden real
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
            """,
            (schema, table),
        )
        cols = [r[0] for r in cur.fetchall()]

    if not cols:
        raise SchemaError(f"No existe la tabla {schema}.{table} o no tiene columnas")

    # PK simple
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(i.indkey)
            WHERE i.indisprimary = TRUE
              AND n.nspname = %s
              AND c.relname = %s
            ORDER BY a.attnum;
            """,
            (schema, table),
        )
        pk_rows = cur.fetchall()

    if not pk_rows:
        raise SchemaError(f"La tabla {schema}.{table} no tiene PRIMARY KEY")
    if len(pk_rows) != 1:
        raise SchemaError(
            f"La tabla {schema}.{table} tiene PK compuesta ({len(pk_rows)} cols). "
            "Este CRUD asume PK simple."
        )

    return TableMeta(schema=schema, table=table, columns=cols, pk=pk_rows[0][0])


T = TypeVar("T", bound="CrudBase")


class CrudBase:
    """
    Template Method:
    - Subclases definen SCHEMA y TABLE
    - Base implementa create/get/list/update/delete usando la meta real del DB
    """
    SCHEMA: str = "public"
    TABLE: str = ""

    _meta_cache: Optional[TableMeta] = None

    @classmethod
    def meta(cls) -> TableMeta:
        if not cls.TABLE:
            raise SchemaError(f"{cls.__name__}.TABLE no esta definido")
        if cls._meta_cache is None:
            cls._meta_cache = _read_table_meta(cls.SCHEMA, cls.TABLE)
        return cls._meta_cache

    @classmethod
    def refresh_meta(cls) -> None:
        cls._meta_cache = _read_table_meta(cls.SCHEMA, cls.TABLE)

    @classmethod
    def create(cls: Type[T], data: Dict[str, Any]) -> Dict[str, Any]:
        m = cls.meta()
        allowed = set(m.columns)
        insert_cols = [k for k in data.keys() if k in allowed]

        if not insert_cols:
            raise ValueError("data no contiene columnas validas para insertar")

        q = sql.SQL(
            "INSERT INTO {schema}.{table} ({cols}) VALUES ({vals}) RETURNING *"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in insert_cols),
            vals=sql.SQL(", ").join(sql.Placeholder(c) for c in insert_cols),
        )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, {c: data[c] for c in insert_cols})
            row = cur.fetchone()

        conn.commit()
        return row

    @classmethod
    def get(cls: Type[T], pk_value: Any) -> Optional[Dict[str, Any]]:
        m = cls.meta()
        q = sql.SQL("SELECT * FROM {schema}.{table} WHERE {pk} = %s").format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (pk_value,))
            return cur.fetchone()

    @classmethod
    def list(cls: Type[T], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        m = cls.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} ORDER BY {pk} LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (limit, offset))
            return cur.fetchall()

    @classmethod
    def update(cls: Type[T], pk_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        m = cls.meta()
        allowed = set(m.columns) - {m.pk}
        upd_cols = [k for k in data.keys() if k in allowed]

        if not upd_cols:
            raise ValueError("data no contiene columnas validas para actualizar")

        assignments = sql.SQL(", ").join(
            sql.SQL("{col} = {ph}").format(col=sql.Identifier(c), ph=sql.Placeholder(c))
            for c in upd_cols
        )

        q = sql.SQL(
            "UPDATE {schema}.{table} SET {assignments} WHERE {pk} = {pkph} RETURNING *"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            assignments=assignments,
            pk=sql.Identifier(m.pk),
            pkph=sql.Placeholder("__pk"),
        )

        params = {c: data[c] for c in upd_cols}
        params["__pk"] = pk_value

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, params)
            row = cur.fetchone()

        conn.commit()
        return row

    @classmethod
    def delete(cls: Type[T], pk_value: Any) -> bool:
        m = cls.meta()
        q = sql.SQL("DELETE FROM {schema}.{table} WHERE {pk} = %s").format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor() as cur:
            cur.execute(q, (pk_value,))
            ok = cur.rowcount == 1
        conn.commit()
        return ok

    @classmethod
    def delete_all(cls: Type[T]) -> int:
        m = cls.meta()
        q = sql.SQL("DELETE FROM {schema}.{table}").format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
        )
        with conn.cursor() as cur:
            cur.execute(q)
            n = cur.rowcount
        conn.commit()
        return n