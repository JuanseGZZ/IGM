from psycopg import sql
from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase


class CrudOrderLines(CrudBase):
    SCHEMA = "public"
    TABLE = "order_lines"

    @staticmethod
    def list_by_order(order_id: str, limit: int = 200, offset: int = 0):
        m = CrudOrderLines.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} "
            "WHERE order_id = %s "
            "ORDER BY id "
            "LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (order_id, limit, offset))
            return cur.fetchall()

    @staticmethod
    def upsert_line(order_id: str, product_id: str, quantity: int):
        """
        Usa tu UNIQUE(order_id, product_id):
        - si existe la linea, suma quantity
        - si no existe, inserta
        Devuelve la fila final.
        """
        q = """
        INSERT INTO public.order_lines (order_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (order_id, product_id)
        DO UPDATE SET quantity = public.order_lines.quantity + EXCLUDED.quantity
        RETURNING *;
        """
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (order_id, product_id, quantity))
            row = cur.fetchone()
        conn.commit()
        return row