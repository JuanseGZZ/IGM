import os
import sqlite3
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "organizers.db")

TARGET_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    external_reference TEXT PRIMARY KEY,
    mp_id TEXT NOT NULL,
    user_email TEXT,
    associated TEXT
);
"""

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)  # espera locks
    conn.execute("PRAGMA busy_timeout = 15000;")
    conn.execute("PRAGMA journal_mode = WAL;")   # mejor concurrencia
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def table_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info({table});")
    return [r[1] for r in cur.fetchall()]  # name

def ensure_orders_migrated():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"No existe DB en: {DB_PATH}")

    conn = connect()
    try:
        cur = conn.cursor()

        # Si no existe orders, crearla final y listo
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
        exists = cur.fetchone() is not None
        if not exists:
            cur.execute(TARGET_SQL)
            conn.commit()
            print("OK: orders no existia, creada con schema final.")
            return

        cols = table_columns(conn, "orders")
        print("orders columns actuales:", cols)

        # Si ya esta como queremos, terminar
        if cols == ["external_reference", "mp_id", "user_email", "associated"] or (
            "user_email" in cols and "external_reference" in cols and "mp_id" in cols and "associated" in cols
        ):
            # Asegurar NOT NULL de mp_id no se puede alterar facil, pero asumimos ok
            print("OK: orders ya tiene user_email. No migro.")
            return

        # Crear tabla nueva final
        cur.execute("DROP TABLE IF EXISTS orders_new;")
        cur.execute("""
            CREATE TABLE orders_new (
                external_reference TEXT PRIMARY KEY,
                mp_id TEXT NOT NULL,
                user_email TEXT,
                associated TEXT
            );
        """)

        # Copiar datos desde la tabla vieja mapeando columnas segun existan
        src_cols = set(cols)

        # external_reference
        if "external_reference" not in src_cols:
            raise SystemExit("La tabla orders vieja no tiene external_reference, no puedo migrar.")

        # mp id puede llamarse mp_id o id o preference_id, etc (fallback)
        mp_expr = None
        for cand in ["mp_id", "id", "preference_id", "mp_preference_id"]:
            if cand in src_cols:
                mp_expr = cand
                break
        if mp_expr is None:
            raise SystemExit("No encuentro columna de mp id en orders vieja (mp_id/id/preference_id/mp_preference_id).")

        # user email puede ser user_email o user_id o payer_email
        user_expr = None
        for cand in ["user_email", "user_id", "payer_email"]:
            if cand in src_cols:
                user_expr = cand
                break
        if user_expr is None:
            user_expr = "NULL"

        assoc_expr = "associated" if "associated" in src_cols else "'none'"

        sql_copy = f"""
            INSERT INTO orders_new (external_reference, mp_id, user_email, associated)
            SELECT external_reference, {mp_expr}, {user_expr}, {assoc_expr}
            FROM orders
            WHERE {mp_expr} IS NOT NULL AND {mp_expr} <> '';
        """
        cur.execute(sql_copy)

        # Swap atomico
        cur.execute("ALTER TABLE orders RENAME TO orders_old;")
        cur.execute("ALTER TABLE orders_new RENAME TO orders;")
        cur.execute("DROP TABLE orders_old;")

        conn.commit()
        print("OK: migracion completada. Schema final aplicado.")
        print("orders columns finales:", table_columns(conn, "orders"))

    except sqlite3.OperationalError as e:
        conn.rollback()
        if "locked" in str(e).lower():
            raise SystemExit(
                "DB LOCKED. Cerra TODO lo que use organizers.db (uvicorn, sqlite shell, otro python) y reintenta."
            )
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("DB:", DB_PATH)
    ensure_orders_migrated()