
-- ============================================================
-- DDL: Esquema completo de producto / variante / atributos
-- PostgreSQL
-- ============================================================

CREATE TABLE category (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE atribute (
    id        SERIAL       PRIMARY KEY,
    key       VARCHAR(100) NOT NULL,
    name      VARCHAR(255) NOT NULL,
    data_type VARCHAR(50)  NOT NULL,  -- ej: 'string', 'integer', 'float', 'boolean', 'enum'
    is_static BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE enum_values (
    id          SERIAL       PRIMARY KEY,
    atribute_id INT          NOT NULL REFERENCES atribute(id) ON DELETE CASCADE,
    value       VARCHAR(255) NOT NULL
);

CREATE TABLE category_atributes (
    id          SERIAL PRIMARY KEY,
    category_id INT    NOT NULL REFERENCES category(id)  ON DELETE CASCADE,
    atribute_id INT    NOT NULL REFERENCES atribute(id)  ON DELETE CASCADE
);

CREATE TABLE product (
    id          SERIAL          PRIMARY KEY,
    code        VARCHAR(100)    NOT NULL UNIQUE,
    title       VARCHAR(255)    NOT NULL,
    price       NUMERIC(12, 2)  NOT NULL,
    description TEXT,
    brand       VARCHAR(255),
    category_id INT             NOT NULL REFERENCES category(id) ON DELETE RESTRICT
);

CREATE TABLE products_atributes (
    id          SERIAL PRIMARY KEY,
    product_id  INT    NOT NULL REFERENCES product(id)   ON DELETE CASCADE,
    atribute_id INT    NOT NULL REFERENCES atribute(id)  ON DELETE CASCADE
);

CREATE TABLE atr_implementation (
    id          SERIAL       PRIMARY KEY,
    atribute_id INT          NOT NULL REFERENCES atribute(id) ON DELETE RESTRICT,
    value       VARCHAR(255) NOT NULL  -- se castea según atribute.data_type en la app
);

CREATE TABLE product_implementation (
    id         SERIAL PRIMARY KEY,
    product_id INT    NOT NULL REFERENCES product(id)            ON DELETE CASCADE,
    atr_imp_id INT    NOT NULL REFERENCES atr_implementation(id) ON DELETE CASCADE
);

CREATE TABLE variant (
    id         SERIAL       PRIMARY KEY,
    code       VARCHAR(100) NOT NULL UNIQUE,
    product_id INT          NOT NULL REFERENCES product(id) ON DELETE CASCADE
);

CREATE TABLE variant_implementation (
    id         SERIAL PRIMARY KEY,
    variant_id INT    NOT NULL REFERENCES variant(id)            ON DELETE CASCADE,
    atr_imp_id INT    NOT NULL REFERENCES atr_implementation(id) ON DELETE CASCADE
);