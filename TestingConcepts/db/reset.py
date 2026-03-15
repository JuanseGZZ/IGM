import psycopg2
from psycopg2 import sql
import os

# ============================================================
# Configuración — modificá estas variables o usá env vars
# ============================================================
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "dbname":   os.getenv("DB_NAME",     "productos"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "13adsASD21."),
}


SQL_FILE = os.path.join(os.path.dirname(__file__), "create_tables.sql")

# ============================================================


def get_all_tables(cursor) -> list[str]:
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    return [row[0] for row in cursor.fetchall()]


def drop_all_tables(cursor, tables: list[str]):
    if not tables:
        print("  No hay tablas para eliminar.")
        return

    # DROP en cascada de todas a la vez, evita el problema de FK ordering
    tables_ident = ", ".join(
        sql.Identifier(t).as_string(cursor.connection) for t in tables
    )
    cursor.execute(f"DROP TABLE IF EXISTS {tables_ident} CASCADE;")
    print(f"  Tablas eliminadas: {', '.join(tables)}")


def run_sql_file(cursor, filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    cursor.execute(content)
    print(f"  Script ejecutado: {filepath}")


def main():
    print("\n=== Reset de base de datos ===\n")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:

            # 1. Obtener tablas actuales
            tables = get_all_tables(cur)
            print(f"[1/3] Tablas encontradas ({len(tables)}): {tables or 'ninguna'}")

            # 2. Drop de todo
            print("[2/3] Eliminando tablas...")
            drop_all_tables(cur, tables)

            # 3. Correr el create script
            print("[3/3] Corriendo create_tables.sql...")
            run_sql_file(cur, SQL_FILE)

        conn.commit()
        print("\n✓ Listo. Base de datos reseteada correctamente.\n")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error — se hizo rollback: {e}\n")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()