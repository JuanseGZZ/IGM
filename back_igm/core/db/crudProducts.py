from config import conn 



with conn.cursor() as cur:
    cur.execute(
        "SELECT id, nombre FROM usuarios WHERE id = %s;",
        (10,)
    )
    row = cur.fetchone()
    print(row)