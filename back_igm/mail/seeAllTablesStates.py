# dump_all_tables.py
# Muestra el contenido completo de todas las tablas SQLite.

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "gmail_oauth.sqlite3"


def main():
    if not DB_PATH.exists():
        print(f"No encuentro la DB en: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Obtener todas las tablas reales (no internas sqlite_)
        tables = conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        if not tables:
            print("No hay tablas en la base.")
            return

        for t in tables:
            table_name = t["name"]
            print("\n" + "=" * 60)
            print(f"TABLA: {table_name}")
            print("=" * 60)

            rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()

            if not rows:
                print("(sin registros)")
                continue

            # imprimir columnas
            columns = rows[0].keys()
            print(" | ".join(columns))
            print("-" * 60)

            for row in rows:
                print(" | ".join(str(row[col]) for col in columns))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
