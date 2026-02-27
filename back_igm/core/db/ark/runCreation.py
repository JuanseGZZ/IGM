import argparse
from pathlib import Path
import psycopg


def reset_public_schema(conn: psycopg.Connection) -> None:
    # DANGER: deletes all objects in public schema
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        # optional but typical defaults:
        cur.execute("GRANT ALL ON SCHEMA public TO public;")
        cur.execute("GRANT ALL ON SCHEMA public TO CURRENT_USER;")


def run_sql_file(conn: psycopg.Connection, sql_path: Path) -> None:
    sql = sql_path.read_text(encoding="utf-8")
    if not sql.strip():
        raise RuntimeError(f"SQL file is empty: {sql_path}")

    with conn.cursor() as cur:
        cur.execute(sql)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=5432)
    ap.add_argument("--dbname", default="appdatabase")
    ap.add_argument("--user", default="backend")
    ap.add_argument("--password", default="chimichangas")
    ap.add_argument("--sql", default="SQL.sql", help="Path to your create script")
    args = ap.parse_args()

    sql_path = Path(args.sql).resolve()
    if not sql_path.exists():
        raise SystemExit(f"SQL file not found: {sql_path}")

    conn = psycopg.connect(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password,
    )

    try:
        with conn:
            reset_public_schema(conn)
            run_sql_file(conn, sql_path)
    finally:
        conn.close()

    print("OK: schema reset + SQL executed")


if __name__ == "__main__":
    main()