import sqlite3

DB_PATH = "organizers.db"  # cambia esto si tu db se llama distinto

def print_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # listar tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cur.fetchall()]

    if not tables:
        print("No hay tablas en la base")
        return

    for table in tables:
        print("\n==============================")
        print(f"Tabla: {table}")
        print("==============================")

        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()

        if not rows:
            print("(vacia)")
            continue

        # headers
        headers = rows[0].keys()
        print(" | ".join(headers))
        print("-" * 80)

        for row in rows:
            print(" | ".join(str(row[h]) for h in headers))

    conn.close()

if __name__ == "__main__":
    print_db(DB_PATH)
