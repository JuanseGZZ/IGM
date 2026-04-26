-- SQLite — esquema corregido y alineado con models.py
-- Diferencias respecto al schema PostgreSQL anterior:
--   - Eliminada tabla products_atributes (no existe en el modelo, se deriva del arbol)
--   - Eliminada columna variant.code (no existe en Variant)
--   - atr_implementation es 1-1 con product_implementation / variant_implementation (no compartida)
--   - Tipos SQLite: INTEGER, TEXT, REAL en lugar de SERIAL, VARCHAR, NUMERIC, BOOLEAN

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS attribute (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    key       TEXT    NOT NULL UNIQUE,
    name      TEXT    NOT NULL,
    data_type TEXT    NOT NULL,
    is_static INTEGER NOT NULL DEFAULT 0   -- 0=dinamico, 1=estatico
);

CREATE TABLE IF NOT EXISTS enum_value (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    attribute_id INTEGER NOT NULL REFERENCES attribute(id) ON DELETE CASCADE,
    value        TEXT    NOT NULL,
    UNIQUE(attribute_id, value)
);

CREATE TABLE IF NOT EXISTS category (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    NOT NULL,
    father_id INTEGER REFERENCES category(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS category_attribute (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id  INTEGER NOT NULL REFERENCES category(id)  ON DELETE CASCADE,
    attribute_id INTEGER NOT NULL REFERENCES attribute(id) ON DELETE CASCADE,
    UNIQUE(category_id, attribute_id)
);

CREATE TABLE IF NOT EXISTS product (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT    NOT NULL UNIQUE,
    title       TEXT    NOT NULL,
    price       REAL    NOT NULL,
    description TEXT,
    brand       TEXT,
    category_id INTEGER NOT NULL REFERENCES category(id) ON DELETE RESTRICT
);

-- Implementacion de un atributo estatico en un producto.
-- Una fila por cada (producto, atributo) que el producto implementa.
CREATE TABLE IF NOT EXISTS product_implementation (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL REFERENCES product(id)   ON DELETE CASCADE,
    attribute_id INTEGER NOT NULL REFERENCES attribute(id) ON DELETE RESTRICT,
    value        TEXT    NOT NULL,
    UNIQUE(product_id, attribute_id)
);

CREATE TABLE IF NOT EXISTS variant (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id) ON DELETE CASCADE
);

-- Implementacion de un atributo dinamico en una variante.
-- Una fila por cada (variante, atributo) que la variante implementa.
CREATE TABLE IF NOT EXISTS variant_implementation (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id   INTEGER NOT NULL REFERENCES variant(id)   ON DELETE CASCADE,
    attribute_id INTEGER NOT NULL REFERENCES attribute(id) ON DELETE RESTRICT,
    value        TEXT    NOT NULL,
    UNIQUE(variant_id, attribute_id)
);
