from .crud_base import CrudBase


class CrudProducts(CrudBase):
    SCHEMA = "public"
    TABLE = "products"

    # opcional: helpers especificos
    @staticmethod
    def list_by_shop(shop_id: str, limit: int = 50, offset: int = 0):
        # Reusa el metodo generico si lo tenes (si no, decime como se llama)
        # Si tu CrudBase no tiene "filter", usa list() + SQL propio.
        from psycopg import sql
        from psycopg.rows import dict_row
        from config import conn

        m = CrudProducts.meta()
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