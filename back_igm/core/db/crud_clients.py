from .crud_base import CrudBase


class CrudClients(CrudBase):
    SCHEMA = "public"
    TABLE = "clients"

    # opcional: helpers especificos
    @staticmethod
    def list_by_shop(shop_id: str, limit: int = 50, offset: int = 0):
        from psycopg import sql
        from psycopg.rows import dict_row
        from config import conn

        m = CrudClients.meta()
        q = sql.SQL(
            "SELECT * FROM {schema}.{table} WHERE shop_id = %s ORDER BY {pk} LIMIT %s OFFSET %s"
        ).format(
            schema=sql.Identifier(m.schema),
            table=sql.Identifier(m.table),
            pk=sql.Identifier(m.pk),
        )
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(q, (shop_id, limit, offset))
            return cur.fetchall()