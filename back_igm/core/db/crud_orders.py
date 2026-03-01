from psycopg import sql
from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase


class CrudOrders(CrudBase):
    SCHEMA = "public"
    TABLE = "orders"

    @staticmethod
    def list_by_client(client_id: int, limit: int = 50, offset: int = 0):
        m = CrudOrders.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} "
            "WHERE client_id = %s "
            "ORDER BY {pk} "
            "LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (client_id, limit, offset))
            return cur.fetchall()