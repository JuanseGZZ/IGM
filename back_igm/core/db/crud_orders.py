from psycopg import sql
from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase


class CrudSubscriptions(CrudBase):
    SCHEMA = "public"
    TABLE = "subscriptions"

    @staticmethod
    def list_by_customer(customer_id: int, limit: int = 50, offset: int = 0):
        m = CrudSubscriptions.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} "
            "WHERE customer_id = %s "
            "ORDER BY {pk} "
            "LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (customer_id, limit, offset))
            return cur.fetchall()

    @staticmethod
    def get_by_shop(shop_id: str):
        # En tu DDL subscriptions.shop_id es UNIQUE, asi que devuelve 0 o 1 fila
        m = CrudSubscriptions.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} WHERE shop_id = %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (shop_id,))
            return cur.fetchone()