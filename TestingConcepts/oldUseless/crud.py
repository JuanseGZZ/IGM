"""
crud.py — Acceso a Postgres para el schema híbrido Opción C

Instalación:
    pip install psycopg2-binary

Cada repo expone exactamente los métodos que necesita su entidad.
No hay magia, no hay ORM. Cada método es una query SQL explícita.

Los repos se acceden a través de la clase Database:
    db = Database()
    db.categories.create("Zapatillas")
    db.products.create(category_id=1, title="Air Max 90")
    ...
"""

import json
import psycopg2
import psycopg2.extras
from typing import Optional, Any

from models import (
    Category, Product,
    ProductOption, ProductOptionValue,
    Variant, VariantOptionValue,
    Attribute, AttributeEnumValue,
    CategoryAttribute, ProductAttributeValue,
    VariantGenerator,
)


# ──────────────────────────────────────────────
# Configuración de conexión
# Modificá estas variables con los datos de tu Postgres en Docker
# ──────────────────────────────────────────────

DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "productos"
DB_USER     = "postgres"
DB_PASSWORD = "13adsASD21."

DB_DSN = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"


# ──────────────────────────────────────────────
# Conexión y setup
# ──────────────────────────────────────────────

class Database:
    """
    Punto de entrada único al CRUD.

    Uso:
        db = Database()
        db.create_tables()

        cat_id  = db.categories.create("Zapatillas")
        prod_id = db.products.create(category_id=cat_id, title="Air Max 90")

    Todos los repos comparten la misma conexión.
    autocommit=False → cada operación hace commit explícito.
    """

    def __init__(self, dsn: str = DB_DSN):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = False
        psycopg2.extras.register_default_jsonb(self.conn)

        self.categories             = CategoryRepo(self.conn)
        self.products               = ProductRepo(self.conn)
        self.product_options        = ProductOptionRepo(self.conn)
        self.product_option_values  = ProductOptionValueRepo(self.conn)
        self.variants               = VariantRepo(self.conn)
        self.variant_option_values  = VariantOptionValueRepo(self.conn)
        self.attributes             = AttributeRepo(self.conn)
        self.attribute_enum_values  = AttributeEnumValueRepo(self.conn)
        self.category_attributes    = CategoryAttributeRepo(self.conn)
        self.product_attributes     = ProductAttributeValueRepo(self.conn)

    def create_tables(self) -> None:
        """
        Crea todas las tablas y el trigger de validación de enum.
        Idempotente — se puede llamar múltiples veces sin error.
        """
        with self.conn.cursor() as cur:
            cur.execute("""

                CREATE TABLE IF NOT EXISTS categories (
                    id   SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS products (
                    id          SERIAL PRIMARY KEY,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    title       TEXT NOT NULL,
                    description TEXT,
                    brand       TEXT,
                    is_active   BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS product_options (
                    id         SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    name       TEXT NOT NULL,
                    position   INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS product_option_values (
                    id         SERIAL PRIMARY KEY,
                    option_id  INTEGER NOT NULL REFERENCES product_options(id) ON DELETE CASCADE,
                    value      TEXT NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS variants (
                    id          SERIAL PRIMARY KEY,
                    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    sku         TEXT NOT NULL UNIQUE,
                    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
                    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                    is_active   BOOLEAN NOT NULL DEFAULT TRUE
                );

                CREATE TABLE IF NOT EXISTS variant_option_values (
                    variant_id      INTEGER NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
                    option_value_id INTEGER NOT NULL REFERENCES product_option_values(id) ON DELETE CASCADE,
                    PRIMARY KEY (variant_id, option_value_id)
                );

                CREATE TABLE IF NOT EXISTS attributes (
                    id        SERIAL PRIMARY KEY,
                    key       TEXT NOT NULL UNIQUE,
                    name      TEXT NOT NULL,
                    data_type TEXT NOT NULL CHECK (data_type IN ('enum','number','boolean','text'))
                );

                CREATE TABLE IF NOT EXISTS attribute_enum_values (
                    id           SERIAL PRIMARY KEY,
                    attribute_id INTEGER NOT NULL REFERENCES attributes(id) ON DELETE CASCADE,
                    value        TEXT NOT NULL,
                    sort_order   INTEGER NOT NULL DEFAULT 0,
                    UNIQUE (attribute_id, value)
                );

                CREATE TABLE IF NOT EXISTS category_attributes (
                    category_id   INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                    attribute_id  INTEGER NOT NULL REFERENCES attributes(id) ON DELETE CASCADE,
                    is_filterable BOOLEAN NOT NULL DEFAULT FALSE,
                    is_required   BOOLEAN NOT NULL DEFAULT FALSE,
                    filter_type   TEXT CHECK (filter_type IN ('enum_multi','range','toggle','text')),
                    ui_control    TEXT CHECK (ui_control IN ('chips','dropdown','checkbox','slider','toggle')),
                    PRIMARY KEY (category_id, attribute_id)
                );

                CREATE TABLE IF NOT EXISTS product_attribute_values (
                    product_id   INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    attribute_id INTEGER NOT NULL REFERENCES attributes(id) ON DELETE CASCADE,
                    value        JSONB NOT NULL,
                    PRIMARY KEY (product_id, attribute_id)
                );

                CREATE INDEX IF NOT EXISTS idx_pav_value
                    ON product_attribute_values USING GIN (value);

                -- Trigger: valida que enum_id exista en attribute_enum_values
                -- antes de insertar o actualizar un product_attribute_value de tipo enum
                CREATE OR REPLACE FUNCTION validate_enum_value()
                RETURNS TRIGGER AS $$
                DECLARE
                    attr_type TEXT;
                BEGIN
                    SELECT data_type INTO attr_type
                    FROM attributes WHERE id = NEW.attribute_id;

                    IF attr_type = 'enum' THEN
                        IF NOT EXISTS (
                            SELECT 1 FROM attribute_enum_values
                            WHERE id = (NEW.value->>'enum_id')::integer
                        ) THEN
                            RAISE EXCEPTION
                                'enum_id % no existe en attribute_enum_values',
                                NEW.value->>'enum_id';
                        END IF;
                    END IF;

                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS trg_validate_enum ON product_attribute_values;
                CREATE TRIGGER trg_validate_enum
                BEFORE INSERT OR UPDATE ON product_attribute_values
                FOR EACH ROW EXECUTE FUNCTION validate_enum_value();

            """)
        self.conn.commit()

    def drop_tables(self) -> None:
        """
        Elimina todas las tablas. Útil para tests o reset completo.
        ¡Cuidado en producción!
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS product_attribute_values  CASCADE;
                DROP TABLE IF EXISTS category_attributes       CASCADE;
                DROP TABLE IF EXISTS attribute_enum_values     CASCADE;
                DROP TABLE IF EXISTS attributes                CASCADE;
                DROP TABLE IF EXISTS variant_option_values     CASCADE;
                DROP TABLE IF EXISTS variants                  CASCADE;
                DROP TABLE IF EXISTS product_option_values     CASCADE;
                DROP TABLE IF EXISTS product_options           CASCADE;
                DROP TABLE IF EXISTS products                  CASCADE;
                DROP TABLE IF EXISTS categories                CASCADE;
                DROP FUNCTION IF EXISTS validate_enum_value    CASCADE;
            """)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


# ──────────────────────────────────────────────
# Base repo
# ──────────────────────────────────────────────

class BaseRepo:
    def __init__(self, conn):
        self.conn = conn

    def _fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def _fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def _execute(self, sql: str, params: tuple = ()) -> Optional[int]:
        """Ejecuta y retorna el id generado si hay RETURNING id."""
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            self.conn.commit()
            if cur.description and cur.description[0].name == "id":
                row = cur.fetchone()
                return row[0] if row else None
        return None


# ──────────────────────────────────────────────
# CategoryRepo
# ──────────────────────────────────────────────

class CategoryRepo(BaseRepo):

    def create(self, name: str) -> int:
        return self._execute(
            "INSERT INTO categories (name) VALUES (%s) RETURNING id",
            (name,)
        )

    def get(self, id: int) -> Optional[Category]:
        row = self._fetchone("SELECT * FROM categories WHERE id = %s", (id,))
        return Category(**row) if row else None

    def list(self) -> list[Category]:
        rows = self._fetchall("SELECT * FROM categories ORDER BY name")
        return [Category(**r) for r in rows]

    def update(self, id: int, name: str) -> None:
        self._execute(
            "UPDATE categories SET name = %s WHERE id = %s",
            (name, id)
        )

    def delete(self, id: int) -> None:
        """Falla si hay productos asociados (ON DELETE RESTRICT en products)."""
        self._execute("DELETE FROM categories WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# ProductRepo
# ──────────────────────────────────────────────

class ProductRepo(BaseRepo):

    def create(
        self,
        category_id: int,
        title: str,
        description: Optional[str] = None,
        brand: Optional[str] = None,
        is_active: bool = True,
    ) -> int:
        return self._execute("""
            INSERT INTO products (category_id, title, description, brand, is_active)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (category_id, title, description, brand, is_active))

    def get(self, id: int) -> Optional[Product]:
        row = self._fetchone("SELECT * FROM products WHERE id = %s", (id,))
        return Product(**row) if row else None

    def list(
        self,
        category_id: Optional[int] = None,
        active_only: bool = False,
        search: Optional[str] = None,
    ) -> list[Product]:
        conditions, params = [], []

        if category_id is not None:
            conditions.append("category_id = %s")
            params.append(category_id)
        if active_only:
            conditions.append("is_active = TRUE")
        if search:
            conditions.append("(title ILIKE %s OR brand ILIKE %s)")
            params += [f"%{search}%", f"%{search}%"]

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows  = self._fetchall(f"SELECT * FROM products {where} ORDER BY title", params)
        return [Product(**r) for r in rows]

    def update(self, id: int, **fields) -> None:
        allowed = {"category_id", "title", "description", "brand", "is_active"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        self._execute(
            f"UPDATE products SET {set_clause} WHERE id = %s",
            (*updates.values(), id)
        )

    def delete(self, id: int) -> None:
        """Elimina en cascada: opciones, variantes y atributos del producto."""
        self._execute("DELETE FROM products WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# ProductOptionRepo
# ──────────────────────────────────────────────

class ProductOptionRepo(BaseRepo):

    def create(self, product_id: int, name: str, position: int = 0) -> int:
        return self._execute("""
            INSERT INTO product_options (product_id, name, position)
            VALUES (%s, %s, %s) RETURNING id
        """, (product_id, name, position))

    def get(self, id: int) -> Optional[ProductOption]:
        row = self._fetchone("SELECT * FROM product_options WHERE id = %s", (id,))
        return ProductOption(**row) if row else None

    def list(self, product_id: int) -> list[ProductOption]:
        rows = self._fetchall(
            "SELECT * FROM product_options WHERE product_id = %s ORDER BY position",
            (product_id,)
        )
        return [ProductOption(**r) for r in rows]

    def update(self, id: int, name: Optional[str] = None, position: Optional[int] = None) -> None:
        if name is not None:
            self._execute("UPDATE product_options SET name = %s WHERE id = %s", (name, id))
        if position is not None:
            self._execute("UPDATE product_options SET position = %s WHERE id = %s", (position, id))

    def delete(self, id: int) -> None:
        """Elimina en cascada los OptionValues y sus VariantOptionValues."""
        self._execute("DELETE FROM product_options WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# ProductOptionValueRepo
# ──────────────────────────────────────────────

class ProductOptionValueRepo(BaseRepo):

    def create(self, option_id: int, value: str, sort_order: int = 0) -> int:
        return self._execute("""
            INSERT INTO product_option_values (option_id, value, sort_order)
            VALUES (%s, %s, %s) RETURNING id
        """, (option_id, value, sort_order))

    def get(self, id: int) -> Optional[ProductOptionValue]:
        row = self._fetchone("SELECT * FROM product_option_values WHERE id = %s", (id,))
        return ProductOptionValue(**row) if row else None

    def list(self, option_id: int) -> list[ProductOptionValue]:
        rows = self._fetchall(
            "SELECT * FROM product_option_values WHERE option_id = %s ORDER BY sort_order",
            (option_id,)
        )
        return [ProductOptionValue(**r) for r in rows]

    def update(self, id: int, value: Optional[str] = None, sort_order: Optional[int] = None) -> None:
        if value is not None:
            self._execute(
                "UPDATE product_option_values SET value = %s WHERE id = %s", (value, id)
            )
        if sort_order is not None:
            self._execute(
                "UPDATE product_option_values SET sort_order = %s WHERE id = %s", (sort_order, id)
            )

    def delete(self, id: int) -> None:
        self._execute("DELETE FROM product_option_values WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# VariantRepo
# ──────────────────────────────────────────────

class VariantRepo(BaseRepo):

    def create(
        self,
        product_id: int,
        sku: str,
        price_cents: int,
        stock: int = 0,
        is_active: bool = True,
    ) -> int:
        return self._execute("""
            INSERT INTO variants (product_id, sku, price_cents, stock, is_active)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (product_id, sku, price_cents, stock, is_active))

    def get(self, id: int) -> Optional[Variant]:
        row = self._fetchone("SELECT * FROM variants WHERE id = %s", (id,))
        return Variant(**row) if row else None

    def get_by_sku(self, sku: str) -> Optional[Variant]:
        row = self._fetchone("SELECT * FROM variants WHERE sku = %s", (sku,))
        return Variant(**row) if row else None

    def list(self, product_id: int, active_only: bool = False) -> list[Variant]:
        sql = "SELECT * FROM variants WHERE product_id = %s"
        params: list = [product_id]
        if active_only:
            sql += " AND is_active = TRUE"
        sql += " ORDER BY sku"
        rows = self._fetchall(sql, params)
        return [Variant(**r) for r in rows]

    def update(self, id: int, **fields) -> None:
        allowed = {"sku", "price_cents", "stock", "is_active"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        self._execute(
            f"UPDATE variants SET {set_clause} WHERE id = %s",
            (*updates.values(), id)
        )

    def update_stock(self, id: int, delta: int) -> int:
        """
        Incrementa o decrementa el stock de forma atómica.
        Retorna el stock resultante.
        Falla con IntegrityError si el stock resultante sería negativo (CHECK constraint).

        delta positivo → entrada de stock
        delta negativo → salida (venta)
        """
        row = self._fetchone(
            "UPDATE variants SET stock = stock + %s WHERE id = %s RETURNING stock",
            (delta, id)
        )
        self.conn.commit()
        return row["stock"] if row else 0

    def delete(self, id: int) -> None:
        self._execute("DELETE FROM variants WHERE id = %s", (id,))

    def generate(
        self,
        product_id: int,
        base_price_cents: int,
        sku_prefix: str = "",
    ) -> list[Variant]:
        """
        Genera automáticamente variantes como producto cartesiano
        de todas las opciones del producto.

        Requiere que el producto ya tenga ProductOptions y ProductOptionValues cargados.
        Retorna la lista de Variants creados.
        """
        from itertools import product as cartesian_product

        # Traer opciones con sus valores ordenados
        options_raw = self._fetchall("""
            SELECT po.id AS option_id, po.name, po.position,
                   pov.id AS value_id, pov.value, pov.sort_order
            FROM product_options po
            JOIN product_option_values pov ON pov.option_id = po.id
            WHERE po.product_id = %s
            ORDER BY po.position, pov.sort_order
        """, (product_id,))

        if not options_raw:
            raise ValueError(
                f"El producto {product_id} no tiene opciones con valores definidos."
            )

        # Agrupar por opción
        options_map: dict[int, list[dict]] = {}
        for row in options_raw:
            options_map.setdefault(row["option_id"], []).append(row)

        combinations = list(cartesian_product(*options_map.values()))
        created: list[Variant] = []

        for combo in combinations:
            parts = [sku_prefix] + [v["value"][:4].upper().replace(" ", "") for v in combo]
            base_sku = "-".join(filter(None, parts))

            # SKU único — agrega sufijo si ya existe
            sku, suffix = base_sku, 1
            while self.get_by_sku(sku):
                sku = f"{base_sku}-{suffix}"
                suffix += 1

            variant_id = self.create(
                product_id=product_id,
                sku=sku,
                price_cents=base_price_cents,
            )

            with self.conn.cursor() as cur:
                for option_value in combo:
                    cur.execute("""
                        INSERT INTO variant_option_values (variant_id, option_value_id)
                        VALUES (%s, %s)
                    """, (variant_id, option_value["value_id"]))
            self.conn.commit()

            created.append(self.get(variant_id))

        return created

    def find_by_options(self, product_id: int, option_value_ids: list[int]) -> Optional[Variant]:
        """
        Encuentra la variante que corresponde exactamente a una combinación
        de option_value_ids.

        Útil para el selector de variante en la página de producto:
        el usuario elige Color=Negro y Talla=42, esto retorna la Variant correcta.
        """
        if not option_value_ids:
            return None

        placeholders = ",".join(["%s"] * len(option_value_ids))
        row = self._fetchone(f"""
            SELECT v.*
            FROM variants v
            WHERE v.product_id = %s
              AND (
                  SELECT COUNT(*)
                  FROM variant_option_values vov
                  WHERE vov.variant_id = v.id
                    AND vov.option_value_id IN ({placeholders})
              ) = %s
        """, (product_id, *option_value_ids, len(option_value_ids)))

        return Variant(**row) if row else None


# ──────────────────────────────────────────────
# VariantOptionValueRepo
# ──────────────────────────────────────────────

class VariantOptionValueRepo(BaseRepo):

    def list(self, variant_id: int) -> list[dict]:
        """
        Retorna las opciones que definen una variante, con nombres legibles.
        Ejemplo de retorno:
            [
                {"option_name": "Color", "value": "Negro", "option_value_id": 1},
                {"option_name": "Talla", "value": "42",    "option_value_id": 3},
            ]
        """
        return self._fetchall("""
            SELECT po.name AS option_name, pov.value, pov.id AS option_value_id
            FROM variant_option_values vov
            JOIN product_option_values pov ON pov.id = vov.option_value_id
            JOIN product_options po         ON po.id  = pov.option_id
            WHERE vov.variant_id = %s
            ORDER BY po.position
        """, (variant_id,))


# ──────────────────────────────────────────────
# AttributeRepo
# ──────────────────────────────────────────────

class AttributeRepo(BaseRepo):

    def create(self, key: str, name: str, data_type: str) -> int:
        return self._execute("""
            INSERT INTO attributes (key, name, data_type)
            VALUES (%s, %s, %s) RETURNING id
        """, (key, name, data_type))

    def get(self, id: int) -> Optional[Attribute]:
        row = self._fetchone("SELECT * FROM attributes WHERE id = %s", (id,))
        return Attribute(**row) if row else None

    def get_by_key(self, key: str) -> Optional[Attribute]:
        row = self._fetchone("SELECT * FROM attributes WHERE key = %s", (key,))
        return Attribute(**row) if row else None

    def list(self, data_type: Optional[str] = None) -> list[Attribute]:
        if data_type:
            rows = self._fetchall(
                "SELECT * FROM attributes WHERE data_type = %s ORDER BY key",
                (data_type,)
            )
        else:
            rows = self._fetchall("SELECT * FROM attributes ORDER BY key")
        return [Attribute(**r) for r in rows]

    def update(self, id: int, name: str) -> None:
        # key y data_type no se actualizan — si hay valores guardados
        # cambiar el tipo rompe la integridad de los jsonb existentes
        self._execute("UPDATE attributes SET name = %s WHERE id = %s", (name, id))

    def delete(self, id: int) -> None:
        self._execute("DELETE FROM attributes WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# AttributeEnumValueRepo
# ──────────────────────────────────────────────

class AttributeEnumValueRepo(BaseRepo):

    def create(self, attribute_id: int, value: str, sort_order: int = 0) -> int:
        return self._execute("""
            INSERT INTO attribute_enum_values (attribute_id, value, sort_order)
            VALUES (%s, %s, %s) RETURNING id
        """, (attribute_id, value, sort_order))

    def get(self, id: int) -> Optional[AttributeEnumValue]:
        row = self._fetchone("SELECT * FROM attribute_enum_values WHERE id = %s", (id,))
        return AttributeEnumValue(**row) if row else None

    def list(self, attribute_id: int) -> list[AttributeEnumValue]:
        rows = self._fetchall(
            "SELECT * FROM attribute_enum_values WHERE attribute_id = %s ORDER BY sort_order",
            (attribute_id,)
        )
        return [AttributeEnumValue(**r) for r in rows]

    def update(self, id: int, value: Optional[str] = None, sort_order: Optional[int] = None) -> None:
        if value is not None:
            self._execute(
                "UPDATE attribute_enum_values SET value = %s WHERE id = %s", (value, id)
            )
        if sort_order is not None:
            self._execute(
                "UPDATE attribute_enum_values SET sort_order = %s WHERE id = %s", (sort_order, id)
            )

    def delete(self, id: int) -> None:
        """
        Valida que el valor no esté en uso antes de eliminar.
        El trigger de Postgres también lo protege, pero validamos
        en Python para dar un error más claro.
        """
        in_use = self._fetchone("""
            SELECT 1 FROM product_attribute_values
            WHERE (value->>'enum_id')::int = %s
            LIMIT 1
        """, (id,))
        if in_use:
            raise ValueError(
                f"El AttributeEnumValue id={id} está en uso en product_attribute_values "
                f"y no puede eliminarse."
            )
        self._execute("DELETE FROM attribute_enum_values WHERE id = %s", (id,))


# ──────────────────────────────────────────────
# CategoryAttributeRepo
# ──────────────────────────────────────────────

class CategoryAttributeRepo(BaseRepo):

    def set(
        self,
        category_id: int,
        attribute_id: int,
        is_filterable: bool = False,
        is_required: bool = False,
        filter_type: Optional[str] = None,
        ui_control: Optional[str] = None,
    ) -> None:
        """
        Crea o actualiza la configuración de un atributo en una categoría (upsert).
        """
        self._execute("""
            INSERT INTO category_attributes
                (category_id, attribute_id, is_filterable, is_required, filter_type, ui_control)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (category_id, attribute_id) DO UPDATE SET
                is_filterable = EXCLUDED.is_filterable,
                is_required   = EXCLUDED.is_required,
                filter_type   = EXCLUDED.filter_type,
                ui_control    = EXCLUDED.ui_control
        """, (category_id, attribute_id, is_filterable, is_required, filter_type, ui_control))

    def get(self, category_id: int, attribute_id: int) -> Optional[CategoryAttribute]:
        row = self._fetchone("""
            SELECT * FROM category_attributes
            WHERE category_id = %s AND attribute_id = %s
        """, (category_id, attribute_id))
        return CategoryAttribute(**row) if row else None

    def list(self, category_id: int) -> list[CategoryAttribute]:
        """Retorna todos los atributos configurados para una categoría."""
        rows = self._fetchall("""
            SELECT ca.*
            FROM category_attributes ca
            JOIN attributes a ON a.id = ca.attribute_id
            WHERE ca.category_id = %s
            ORDER BY a.key
        """, (category_id,))
        return [CategoryAttribute(**r) for r in rows]

    def list_filterable(self, category_id: int) -> list[dict]:
        """
        Retorna solo los atributos filtrables de una categoría,
        con toda la info del atributo incluida.
        Usado por el servicio de filtros del catálogo.
        """
        return self._fetchall("""
            SELECT ca.*, a.key, a.name, a.data_type
            FROM category_attributes ca
            JOIN attributes a ON a.id = ca.attribute_id
            WHERE ca.category_id = %s AND ca.is_filterable = TRUE
            ORDER BY a.key
        """, (category_id,))

    def delete(self, category_id: int, attribute_id: int) -> None:
        self._execute("""
            DELETE FROM category_attributes
            WHERE category_id = %s AND attribute_id = %s
        """, (category_id, attribute_id))


# ──────────────────────────────────────────────
# ProductAttributeValueRepo
# ──────────────────────────────────────────────

class ProductAttributeValueRepo(BaseRepo):

    def set(self, pav: ProductAttributeValue) -> None:
        """
        Recibe un ProductAttributeValue del modelo y lo persiste (upsert).

        El modelo sabe convertirse a jsonb con .to_jsonb().
        Si el atributo es enum, pav.enum_value_id debe estar seteado
        — el trigger de Postgres validará que exista.

        Ejemplo:
            pav = ProductAttributeValue(
                product_id=1, attribute_id=3, value=False
            )
            db.product_attributes.set(pav)
        """
        self._execute("""
            INSERT INTO product_attribute_values (product_id, attribute_id, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (product_id, attribute_id) DO UPDATE SET value = EXCLUDED.value
        """, (pav.product_id, pav.attribute_id, json.dumps(pav.to_jsonb())))

    def get(self, product_id: int, attribute_id: int) -> Optional[ProductAttributeValue]:
        row = self._fetchone("""
            SELECT * FROM product_attribute_values
            WHERE product_id = %s AND attribute_id = %s
        """, (product_id, attribute_id))
        if not row:
            return None
        return ProductAttributeValue.from_jsonb(product_id, attribute_id, row["value"])

    def list(self, product_id: int) -> list[ProductAttributeValue]:
        """Retorna todos los atributos de un producto como objetos del modelo."""
        rows = self._fetchall("""
            SELECT * FROM product_attribute_values
            WHERE product_id = %s
        """, (product_id,))
        return [
            ProductAttributeValue.from_jsonb(r["product_id"], r["attribute_id"], r["value"])
            for r in rows
        ]

    def delete(self, product_id: int, attribute_id: int) -> None:
        self._execute("""
            DELETE FROM product_attribute_values
            WHERE product_id = %s AND attribute_id = %s
        """, (product_id, attribute_id))

    def filter_products(
        self,
        category_id: int,
        filters: dict[str, Any],
    ) -> list[Product]:
        """
        Filtra productos de una categoría por sus atributos descriptivos.

        filters: dict donde la key es el attribute.key y el valor es:
            - Para text/enum:   un string exacto  → {"material": "Cuero"}
            - Para boolean:     un bool            → {"waterproof": True}
            - Para number:      un dict con min/max → {"peso_g": {"min": 200, "max": 400}}

        Ejemplo:
            productos = db.product_attributes.filter_products(
                category_id=1,
                filters={
                    "waterproof": True,
                    "peso_g": {"max": 400},
                }
            )
        """
        conditions: list[str] = ["p.category_id = %s"]
        params: list[Any]     = [category_id]

        for key, val in filters.items():
            attr = self._fetchone(
                "SELECT id, data_type FROM attributes WHERE key = %s", (key,)
            )
            if not attr:
                continue

            attr_id   = attr["id"]
            data_type = attr["data_type"]

            if data_type == "number" and isinstance(val, dict):
                if "min" in val:
                    conditions.append("""
                        EXISTS (
                            SELECT 1 FROM product_attribute_values pav2
                            WHERE pav2.product_id = p.id AND pav2.attribute_id = %s
                              AND (pav2.value->>'number')::float >= %s
                        )
                    """)
                    params += [attr_id, val["min"]]
                if "max" in val:
                    conditions.append("""
                        EXISTS (
                            SELECT 1 FROM product_attribute_values pav2
                            WHERE pav2.product_id = p.id AND pav2.attribute_id = %s
                              AND (pav2.value->>'number')::float <= %s
                        )
                    """)
                    params += [attr_id, val["max"]]

            elif data_type == "boolean":
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM product_attribute_values pav2
                        WHERE pav2.product_id = p.id AND pav2.attribute_id = %s
                          AND (pav2.value->>'bool')::boolean = %s
                    )
                """)
                params += [attr_id, val]

            elif data_type == "enum":
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM product_attribute_values pav2
                        WHERE pav2.product_id = p.id AND pav2.attribute_id = %s
                          AND pav2.value->>'enum_value' = %s
                    )
                """)
                params += [attr_id, str(val)]

            else:  # text
                conditions.append("""
                    EXISTS (
                        SELECT 1 FROM product_attribute_values pav2
                        WHERE pav2.product_id = p.id AND pav2.attribute_id = %s
                          AND pav2.value->>'text' = %s
                    )
                """)
                params += [attr_id, str(val)]

        where = " AND ".join(conditions)
        rows  = self._fetchall(
            f"SELECT DISTINCT p.* FROM products p WHERE {where} ORDER BY p.title",
            params
        )
        return [Product(**r) for r in rows]
