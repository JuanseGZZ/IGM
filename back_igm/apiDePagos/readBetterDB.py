import sqlite3
from typing import List, Dict, Any

DB_PATH = "organizers.db"  # cambia esto si tu db se llama distinto

MAX_COL_WIDTH = 48          # limite para que no explote la consola
MASK_SENSITIVE = True       # True para ocultar tokens
SENSITIVE_COLS = {"access_token", "refresh_token", "card_token"}


def _to_str(v: Any) -> str:
    if v is None:
        return "NULL"
    return str(v)


def _mask_value(v: str, keep_start: int = 6, keep_end: int = 4) -> str:
    if v is None:
        return "NULL"
    s = str(v)
    if len(s) <= keep_start + keep_end + 3:
        return "***"
    return f"{s[:keep_start]}...{s[-keep_end:]}"


def _truncate(s: str, width: int) -> str:
    if len(s) <= width:
        return s
    if width <= 3:
        return s[:width]
    return s[: width - 3] + "..."


def _compute_widths(headers: List[str], rows: List[Dict[str, str]]) -> Dict[str, int]:
    widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            widths[h] = max(widths[h], len(r.get(h, "")))
    for h in headers:
        widths[h] = min(widths[h], MAX_COL_WIDTH)
    return widths


def _print_table(headers: List[str], rows: List[Dict[str, str]]) -> None:
    widths = _compute_widths(headers, rows)

    def line(char: str = "-") -> str:
        # +-----+-----+
        return "+" + "+".join(char * (widths[h] + 2) for h in headers) + "+"

    def render_row(r: Dict[str, str]) -> str:
        cells = []
        for h in headers:
            cell = r.get(h, "")
            cell = _truncate(cell, widths[h])
            cells.append(" " + cell.ljust(widths[h]) + " ")
        return "|" + "|".join(cells) + "|"

    print(line("-"))
    print(render_row({h: h for h in headers}))
    print(line("="))
    for r in rows:
        print(render_row(r))
    print(line("-"))


def print_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row["name"] for row in cur.fetchall()]

    if not tables:
        print("No hay tablas en la base")
        conn.close()
        return

    for table in tables:
        print()
        print("=" * 70)
        print(f"Tabla: {table}")
        print("=" * 70)

        cur.execute(f'SELECT * FROM "{table}"')
        raw_rows = cur.fetchall()

        if not raw_rows:
            print("(vacia)")
            continue

        headers = list(raw_rows[0].keys())

        # normaliza filas a dict[str,str] y aplica masking/truncado logico
        rows: List[Dict[str, str]] = []
        for rr in raw_rows:
            d: Dict[str, str] = {}
            for h in headers:
                val = rr[h]
                s = _to_str(val)

                if MASK_SENSITIVE and h in SENSITIVE_COLS:
                    s = _mask_value(s)

                d[h] = s
            rows.append(d)

        print(f"Filas: {len(rows)}")
        _print_table(headers, rows)

    conn.close()


if __name__ == "__main__":
    print_db(DB_PATH)
