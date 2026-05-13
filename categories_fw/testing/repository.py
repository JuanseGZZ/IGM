import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "catalog.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS attributes (
            id          INTEGER PRIMARY KEY,
            key         TEXT    UNIQUE NOT NULL,
            name        TEXT    NOT NULL,
            data_type   TEXT    NOT NULL,
            is_static   INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS attribute_enum_values (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            attribute_id INTEGER NOT NULL REFERENCES attributes(id) ON DELETE CASCADE,
            value        TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS categories (
            id                 INTEGER PRIMARY KEY,
            name               TEXT    NOT NULL,
            father_category_id INTEGER REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS category_attributes (
            category_id  INTEGER NOT NULL REFERENCES categories(id)  ON DELETE CASCADE,
            attribute_id INTEGER NOT NULL REFERENCES attributes(id)  ON DELETE CASCADE,
            PRIMARY KEY (category_id, attribute_id)
        );
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY,
            code        TEXT    UNIQUE NOT NULL,
            title       TEXT    NOT NULL,
            price       REAL    NOT NULL DEFAULT 0,
            description TEXT    DEFAULT '',
            brand       TEXT    DEFAULT '',
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS variants (
            id         INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS attribute_implementations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            attribute_id INTEGER NOT NULL REFERENCES attributes(id)  ON DELETE CASCADE,
            value        TEXT    NOT NULL,
            product_id   INTEGER REFERENCES products(id)  ON DELETE CASCADE,
            variant_id   INTEGER REFERENCES variants(id)  ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def get_full_state() -> dict:
    """Carga el estado completo desde la DB y lo retorna como dict serializable."""
    conn = _connect()
    try:
        # Atributos
        attrs = [dict(r) for r in conn.execute(
            "SELECT id, key, name, data_type, is_static FROM attributes ORDER BY id"
        ).fetchall()]
        for a in attrs:
            a["is_static"] = bool(a["is_static"])
            evs = conn.execute(
                "SELECT value FROM attribute_enum_values WHERE attribute_id=? ORDER BY id",
                (a["id"],)
            ).fetchall()
            a["enum_values"] = [r["value"] for r in evs]

        attr_key_map = {a["id"]: a["key"] for a in attrs}

        # Categorías
        cat_rows = conn.execute(
            "SELECT id, name, father_category_id FROM categories"
        ).fetchall()
        cat_map = {
            r["id"]: {
                "id": r["id"], "name": r["name"],
                "_father_id": r["father_category_id"],
                "attribute_ids": [], "subcategories": [], "products": []
            }
            for r in cat_rows
        }
        for r in conn.execute("SELECT category_id, attribute_id FROM category_attributes").fetchall():
            if r["category_id"] in cat_map:
                cat_map[r["category_id"]]["attribute_ids"].append(r["attribute_id"])

        # Productos
        prod_rows = conn.execute(
            "SELECT id, code, title, price, description, brand, category_id FROM products ORDER BY id"
        ).fetchall()
        prod_map = {
            r["id"]: {
                "id": r["id"], "code": r["code"], "title": r["title"],
                "price": r["price"], "description": r["description"], "brand": r["brand"],
                "_category_id": r["category_id"],
                "attributes_implementations": [], "variants": []
            }
            for r in prod_rows
        }

        # Variantes
        var_rows = conn.execute("SELECT id, product_id FROM variants ORDER BY id").fetchall()
        var_map = {
            r["id"]: {
                "id": r["id"], "_product_id": r["product_id"],
                "attribute_implementations": []
            }
            for r in var_rows
        }

        # Implementaciones
        for r in conn.execute(
            "SELECT attribute_id, value, product_id, variant_id FROM attribute_implementations"
        ).fetchall():
            impl = {"attribute_key": attr_key_map.get(r["attribute_id"], ""), "value": r["value"]}
            if r["variant_id"] is not None and r["variant_id"] in var_map:
                var_map[r["variant_id"]]["attribute_implementations"].append(impl)
            elif r["product_id"] is not None and r["product_id"] in prod_map:
                prod_map[r["product_id"]]["attributes_implementations"].append(impl)

        # Ensamblar: variantes → productos
        for var in var_map.values():
            pid = var.pop("_product_id")
            if pid in prod_map:
                prod_map[pid]["variants"].append(var)

        # Ensamblar: productos → categorías
        for prod in prod_map.values():
            cid = prod.pop("_category_id")
            if cid in cat_map:
                cat_map[cid]["products"].append(prod)

        # Ensamblar: árbol de categorías (top-down por referencia)
        root_id = None
        for cat in cat_map.values():
            father_id = cat.pop("_father_id")
            if father_id is None:
                root_id = cat["id"]
            elif father_id in cat_map:
                cat_map[father_id]["subcategories"].append(cat)

        tree = cat_map.get(root_id)
        return {"attributes": attrs, "tree": tree}
    finally:
        conn.close()


def save_full_state(attrs: list, root_cat) -> None:
    """Reemplaza todo el estado de la DB de forma atómica."""
    conn = _connect()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM attribute_implementations")
        conn.execute("DELETE FROM variants")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM category_attributes")
        conn.execute("DELETE FROM categories")
        conn.execute("DELETE FROM attribute_enum_values")
        conn.execute("DELETE FROM attributes")

        for attr in attrs:
            conn.execute(
                "INSERT INTO attributes (id, key, name, data_type, is_static) VALUES (?,?,?,?,?)",
                (attr.id, attr.key, attr.name, attr.data_type, int(attr.is_static))
            )
            for ev in attr.enum_values:
                conn.execute(
                    "INSERT INTO attribute_enum_values (attribute_id, value) VALUES (?,?)",
                    (attr.id, ev)
                )

        _insert_category(conn, root_cat, father_id=None)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def _insert_category(conn: sqlite3.Connection, cat, father_id) -> None:
    cur = conn.execute(
        "INSERT INTO categories (id, name, father_category_id) VALUES (?,?,?)",
        (cat.id, cat.name, father_id)
    )
    cat_id = cat.id if cat.id is not None else cur.lastrowid
    for attr in cat.attributes:
        conn.execute(
            "INSERT INTO category_attributes (category_id, attribute_id) VALUES (?,?)",
            (cat_id, attr.id)
        )
    for prod in cat.products:
        _insert_product(conn, prod, cat_id)
    for sub in cat.subcategories:
        _insert_category(conn, sub, cat_id)


def _insert_product(conn: sqlite3.Connection, prod, category_id: int) -> None:
    cur = conn.execute(
        "INSERT INTO products (id, code, title, price, description, brand, category_id) VALUES (?,?,?,?,?,?,?)",
        (prod.id, prod.code, prod.title, prod.price, prod.description, prod.brand, category_id)
    )
    prod_id = prod.id if prod.id is not None else cur.lastrowid
    for impl in prod.attributes_implementations:
        conn.execute(
            "INSERT INTO attribute_implementations (attribute_id, value, product_id, variant_id) VALUES (?,?,?,NULL)",
            (impl.attribute.id, impl.value, prod_id)
        )
    for var in prod.variants:
        cur_v = conn.execute(
            "INSERT INTO variants (id, product_id) VALUES (?,?)",
            (var.id, prod_id)
        )
        var_id = var.id if var.id is not None else cur_v.lastrowid
        for impl in var.attribute_implementations:
            conn.execute(
                "INSERT INTO attribute_implementations (attribute_id, value, product_id, variant_id) VALUES (?,?,NULL,?)",
                (impl.attribute.id, impl.value, var_id)
            )
