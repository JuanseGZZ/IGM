from collections import defaultdict
from db_handler.db import get_connection
from app.models import Attribute, AttributeImplementation, Category, Product, Variant


# ── AttributeRepo ─────────────────────────────────────────────────────────────

class AttributeRepo:

    def save(self, attr: Attribute) -> Attribute:
        conn = get_connection()
        if attr.id is None:
            cur = conn.execute(
                "INSERT INTO attribute (key, name, data_type, is_static) VALUES (?, ?, ?, ?)",
                (attr.key, attr.name, attr.data_type, int(attr.is_static)),
            )
            attr.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE attribute SET key=?, name=?, data_type=?, is_static=? WHERE id=?",
                (attr.key, attr.name, attr.data_type, int(attr.is_static), attr.id),
            )
        # sync enum values
        conn.execute("DELETE FROM enum_value WHERE attribute_id=?", (attr.id,))
        for v in attr.enum_values:
            conn.execute(
                "INSERT OR IGNORE INTO enum_value (attribute_id, value) VALUES (?, ?)",
                (attr.id, v),
            )
        conn.commit()
        conn.close()
        return attr

    def get(self, attr_id: int) -> Attribute | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM attribute WHERE id=?", (attr_id,)).fetchone()
        if row is None:
            conn.close()
            return None
        attr = self._row_to_attr(row, conn)
        conn.close()
        return attr

    def list_all(self) -> list[Attribute]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM attribute").fetchall()
        attrs = [self._row_to_attr(r, conn) for r in rows]
        conn.close()
        return attrs

    def delete(self, attr_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM attribute WHERE id=?", (attr_id,))
        conn.commit()
        conn.close()

    def _row_to_attr(self, row, conn) -> Attribute:
        attr = Attribute(
            id=row["id"], key=row["key"], name=row["name"],
            data_type=row["data_type"], is_static=bool(row["is_static"]),
        )
        enum_rows = conn.execute(
            "SELECT value FROM enum_value WHERE attribute_id=?", (row["id"],)
        ).fetchall()
        attr.enum_values = [r["value"] for r in enum_rows]
        return attr


# ── CategoryRepo ──────────────────────────────────────────────────────────────

class CategoryRepo:

    def save(self, cat: Category) -> Category:
        conn = get_connection()
        father_id = cat.father_categorie.id if cat.father_categorie else None
        if cat.id is None:
            cur = conn.execute(
                "INSERT INTO category (name, father_id) VALUES (?, ?)",
                (cat.name, father_id),
            )
            cat.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE category SET name=?, father_id=? WHERE id=?",
                (cat.name, father_id, cat.id),
            )
        # sync attributes
        conn.execute("DELETE FROM category_attribute WHERE category_id=?", (cat.id,))
        for attr in cat.attributes:
            if attr.id is not None:
                conn.execute(
                    "INSERT OR IGNORE INTO category_attribute (category_id, attribute_id) VALUES (?, ?)",
                    (cat.id, attr.id),
                )
        conn.commit()
        conn.close()
        return cat

    def get(self, cat_id: int) -> Category | None:
        """Carga la categoria con su contexto de arbol completo."""
        tree = self.load_tree()
        return tree.get(cat_id)

    def load_tree(self) -> dict[int, Category]:
        """Carga todas las categorias y arma el arbol en Python."""
        conn = get_connection()

        cat_rows  = conn.execute("SELECT * FROM category").fetchall()
        attr_rows = conn.execute("""
            SELECT ca.category_id, a.id, a.key, a.name, a.data_type, a.is_static
            FROM category_attribute ca
            JOIN attribute a ON a.id = ca.attribute_id
        """).fetchall()
        enum_rows = conn.execute("SELECT * FROM enum_value").fetchall()
        prod_rows = conn.execute(
            "SELECT id, code, title, price, description, brand, category_id FROM product"
        ).fetchall()
        conn.close()

        # Construir atributos (sin duplicar por id)
        attrs_by_id: dict[int, Attribute] = {}
        enum_by_attr: dict[int, list] = defaultdict(list)
        for r in enum_rows:
            enum_by_attr[r["attribute_id"]].append(r["value"])
        for r in attr_rows:
            if r["id"] not in attrs_by_id:
                a = Attribute(
                    id=r["id"], key=r["key"], name=r["name"],
                    data_type=r["data_type"], is_static=bool(r["is_static"]),
                )
                a.enum_values = enum_by_attr.get(r["id"], [])
                attrs_by_id[r["id"]] = a

        # Construir categorias vacias
        cats: dict[int, Category] = {}
        father_ids: dict[int, int | None] = {}
        for r in cat_rows:
            cat = Category(name=r["name"], id=r["id"])
            cats[r["id"]] = cat
            father_ids[r["id"]] = r["father_id"]

        # Asignar atributos
        for r in attr_rows:
            cat = cats.get(r["category_id"])
            if cat:
                cat.attributes.append(attrs_by_id[r["id"]])
                cat._attribute_keys.add(r["key"])

        # Armar relaciones padre-hijo
        for cat_id, father_id in father_ids.items():
            if father_id is not None and father_id in cats:
                parent = cats[father_id]
                child  = cats[cat_id]
                child.father_categorie = parent
                parent.subcategories.append(child)

        # Poblar productos (stubs) para que _descend_impact y _check_exclusive_children funcionen
        for r in prod_rows:
            cat = cats.get(r["category_id"])
            if cat:
                stub = Product(
                    id=r["id"], code=r["code"], title=r["title"],
                    price=r["price"],
                    description=r["description"] or "",
                    brand=r["brand"] or "",
                    category=cat,
                )
                cat.products.append(stub)
                cat._product_codes.add(r["code"])

        return cats

    def delete(self, cat_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM product WHERE category_id=?", (cat_id,))
        conn.execute("DELETE FROM category WHERE id=?", (cat_id,))
        conn.commit()
        conn.close()


# ── ProductRepo ───────────────────────────────────────────────────────────────

class ProductRepo:

    def __init__(self):
        self._attr_repo = AttributeRepo()

    def save(self, prod: Product) -> Product:
        conn = get_connection()
        cat_id = prod.category.id
        if prod.id is None:
            cur = conn.execute(
                "INSERT INTO product (code, title, price, description, brand, category_id)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (prod.code, prod.title, prod.price, prod.description, prod.brand, cat_id),
            )
            prod.id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE product SET code=?, title=?, price=?, description=?, brand=?, category_id=?"
                " WHERE id=?",
                (prod.code, prod.title, prod.price, prod.description, prod.brand, cat_id, prod.id),
            )
        # sync static attribute implementations
        conn.execute("DELETE FROM product_implementation WHERE product_id=?", (prod.id,))
        for impl in prod.attributes_implementations:
            if impl.attribute.id is not None:
                conn.execute(
                    "INSERT INTO product_implementation (product_id, attribute_id, value)"
                    " VALUES (?, ?, ?)",
                    (prod.id, impl.attribute.id, impl.value),
                )
        conn.commit()
        conn.close()

        # sync variants
        for v in prod.variants:
            VariantRepo().save(v, prod.id)

        return prod

    def get(self, prod_id: int) -> Product | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM product WHERE id=?", (prod_id,)).fetchone()
        if row is None:
            conn.close()
            return None
        prod = self._load_product(row, conn)
        conn.close()
        return prod

    def list_by_category(self, cat_id: int) -> list[Product]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM product WHERE category_id=?", (cat_id,)).fetchall()
        prods = [self._load_product(r, conn) for r in rows]
        conn.close()
        return prods

    def list_all(self) -> list[Product]:
        conn = get_connection()
        rows = conn.execute("SELECT * FROM product").fetchall()
        prods = [self._load_product(r, conn) for r in rows]
        conn.close()
        return prods

    def delete(self, prod_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM product WHERE id=?", (prod_id,))
        conn.commit()
        conn.close()

    def _load_product(self, row, conn) -> Product:
        # Necesitamos la categoria — cargamos solo el objeto minimo con id
        cat_stub = Category(name="", id=row["category_id"])

        impl_rows = conn.execute("""
            SELECT pi.id, pi.value, a.id as attr_id, a.key, a.name, a.data_type, a.is_static
            FROM product_implementation pi
            JOIN attribute a ON a.id = pi.attribute_id
            WHERE pi.product_id = ?
        """, (row["id"],)).fetchall()

        impls = [
            AttributeImplementation(
                id=r["id"],
                attribute=Attribute(
                    id=r["attr_id"], key=r["key"], name=r["name"],
                    data_type=r["data_type"], is_static=bool(r["is_static"]),
                ),
                value=r["value"],
            )
            for r in impl_rows
        ]

        var_rows = conn.execute(
            "SELECT * FROM variant WHERE product_id=?", (row["id"],)
        ).fetchall()
        variants = [self._load_variant(vr, conn) for vr in var_rows]

        return Product(
            id=row["id"], code=row["code"], title=row["title"],
            price=row["price"], description=row["description"], brand=row["brand"],
            category=cat_stub,
            attributes_implementations=impls,
            variants=variants,
        )

    def _load_variant(self, row, conn) -> Variant:
        impl_rows = conn.execute("""
            SELECT vi.id, vi.value, a.id as attr_id, a.key, a.name, a.data_type, a.is_static
            FROM variant_implementation vi
            JOIN attribute a ON a.id = vi.attribute_id
            WHERE vi.variant_id = ?
        """, (row["id"],)).fetchall()

        impls = [
            AttributeImplementation(
                id=r["id"],
                attribute=Attribute(
                    id=r["attr_id"], key=r["key"], name=r["name"],
                    data_type=r["data_type"], is_static=bool(r["is_static"]),
                ),
                value=r["value"],
            )
            for r in impl_rows
        ]
        return Variant(id=row["id"], attribute_implementations=impls)


# ── VariantRepo ───────────────────────────────────────────────────────────────

class VariantRepo:

    def save(self, variant: Variant, product_id: int) -> Variant:
        conn = get_connection()
        if variant.id is None:
            cur = conn.execute(
                "INSERT INTO variant (product_id) VALUES (?)", (product_id,)
            )
            variant.id = cur.lastrowid
        # sync dynamic implementations
        conn.execute("DELETE FROM variant_implementation WHERE variant_id=?", (variant.id,))
        for impl in variant.attribute_implementations:
            if impl.attribute.id is not None:
                conn.execute(
                    "INSERT INTO variant_implementation (variant_id, attribute_id, value)"
                    " VALUES (?, ?, ?)",
                    (variant.id, impl.attribute.id, impl.value),
                )
        conn.commit()
        conn.close()
        return variant

    def get(self, var_id: int) -> Variant | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM variant WHERE id=?", (var_id,)).fetchone()
        if row is None:
            conn.close()
            return None
        impl_rows = conn.execute("""
            SELECT vi.id, vi.value, a.id as attr_id, a.key, a.name, a.data_type, a.is_static
            FROM variant_implementation vi
            JOIN attribute a ON a.id = vi.attribute_id
            WHERE vi.variant_id = ?
        """, (var_id,)).fetchall()
        impls = [
            AttributeImplementation(
                id=r["id"],
                attribute=Attribute(
                    id=r["attr_id"], key=r["key"], name=r["name"],
                    data_type=r["data_type"], is_static=bool(r["is_static"]),
                ),
                value=r["value"],
            )
            for r in impl_rows
        ]
        conn.close()
        return Variant(id=row["id"], attribute_implementations=impls)

    def delete(self, var_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM variant WHERE id=?", (var_id,))
        conn.commit()
        conn.close()
