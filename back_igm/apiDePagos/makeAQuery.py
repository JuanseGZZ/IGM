# sql_console.py
# Consola SQL interactiva para tu database.sqlite

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "organizers.db"


def main():
    if not DB_PATH.exists():
        print(f"No encuentro la DB en: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("Conectado a:", DB_PATH)
    print("Escribi cualquier SQL. 'exit' para salir.\n")

    try:
        while True:
            query = input("sql> ").strip()

            if not query:
                continue

            if query.lower() in ("exit", "quit"):
                break

            try:
                cursor = conn.execute(query)

                if query.lower().startswith("select"):
                    rows = cursor.fetchall()

                    if not rows:
                        print("(sin resultados)")
                        continue

                    columns = rows[0].keys()
                    print(" | ".join(columns))
                    print("-" * 60)

                    for row in rows:
                        print(" | ".join(str(row[col]) for col in columns))
                else:
                    conn.commit()
                    print(f"OK. Filas afectadas: {cursor.rowcount}")

            except Exception as e:
                print("Error:", e)

    finally:
        conn.close()
        print("Conexion cerrada.")


if __name__ == "__main__":
    main()
