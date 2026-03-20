from __future__ import annotations

from typing import Any, Dict, Generic, Optional, Type, TypeVar

from psycopg import sql
from psycopg.rows import dict_row

from config import conn


T = TypeVar("T")


class CrudBase(Generic[T]):
    TABLE: str = ""
    MODEL_CLASS: Type[T] | None = None

    @classmethod
    def _obj_to_row(cls, obj: T) -> Dict[str, Any]:
        return vars(obj).copy()

    @classmethod
    def _row_to_obj(cls, row: Optional[Dict[str, Any]]) -> Optional[T]:
        if row is None:
            return None
        if cls.MODEL_CLASS is None:
            return row
        return cls.MODEL_CLASS(**row)

    @classmethod
    def save(cls, obj: T) -> T:
        if not cls.TABLE:
            raise ValueError("TABLE no definido")
        if cls.MODEL_CLASS is None:
            raise ValueError("MODEL_CLASS no definido")

        data = cls._obj_to_row(obj)
        obj_id = data.get("id")

        if obj_id is None:
            cols = [k for k, v in data.items() if k != "id" and v is not None]
            values = {k: data[k] for k in cols}

            q = sql.SQL(
                "INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING *"
            ).format(
                table=sql.Identifier(cls.TABLE),
                cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
                vals=sql.SQL(", ").join(sql.Placeholder(c) for c in cols),
            )

            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(q, values)
                row = cur.fetchone()

            conn.commit()
            return cls._row_to_obj(row)

        cols = [k for k in data.keys() if k != "id"]
        values = {k: data[k] for k in cols}
        values["id"] = obj_id

        assignments = sql.SQL(", ").join(
            sql.SQL("{col} = {ph}").format(
                col=sql.Identifier(c),
                ph=sql.Placeholder(c),
            )
            for c in cols
        )

        q_update = sql.SQL(
            "UPDATE {table} SET {assignments} WHERE id = {id_ph} RETURNING *"
        ).format(
            table=sql.Identifier(cls.TABLE),
            assignments=assignments,
            id_ph=sql.Placeholder("id"),
        )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q_update, values)
            row = cur.fetchone()

        if row is None:
            insert_cols = list(data.keys())
            insert_values = {k: data[k] for k in insert_cols}

            q_insert = sql.SQL(
                "INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING *"
            ).format(
                table=sql.Identifier(cls.TABLE),
                cols=sql.SQL(", ").join(sql.Identifier(c) for c in insert_cols),
                vals=sql.SQL(", ").join(sql.Placeholder(c) for c in insert_cols),
            )

            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(q_insert, insert_values)
                row = cur.fetchone()

        conn.commit()
        return cls._row_to_obj(row)

    @classmethod
    def read(cls, obj_id: Any) -> Optional[T]:
        q = sql.SQL("SELECT * FROM {table} WHERE id = %s").format(
            table=sql.Identifier(cls.TABLE)
        )

        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (obj_id,))
            row = cur.fetchone()

        return cls._row_to_obj(row)

    @classmethod
    def delete(cls, obj_id: Any) -> bool:
        q = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
            table=sql.Identifier(cls.TABLE)
        )

        with conn.cursor() as cur:
            cur.execute(q, (obj_id,))
            deleted = cur.rowcount > 0

        conn.commit()
        return deleted

    @classmethod
    def query(cls, *args, **kwargs):
        raise NotImplementedError("Aca despues podes agregar queries dinamicas")

    @classmethod
    def bring_all(cls) -> list[T]:
        if not cls.TABLE:
            raise ValueError("TABLE no definido")
    
        q = sql.SQL("SELECT * FROM {table}").format(
            table=sql.Identifier(cls.TABLE)
        )
    
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q)
            rows = cur.fetchall()
    
        return [cls._row_to_obj(row) for row in rows]