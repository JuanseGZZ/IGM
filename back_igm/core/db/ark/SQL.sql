-- Postgres DDL

-- =========================
-- CORE ENTITIES
-- =========================

CREATE TABLE customers (
  id              BIGINT PRIMARY KEY,
  name            TEXT NOT NULL,
  surname         TEXT NOT NULL,
  email           TEXT NOT NULL UNIQUE,
  mp_associated   INTEGER NOT NULL
);

CREATE TABLE shops (
  id    TEXT PRIMARY KEY,
  name  TEXT NOT NULL
);

CREATE TABLE plans (
  id                TEXT PRIMARY KEY,
  name              TEXT NOT NULL,
  up_to             INTEGER NOT NULL,
  down_to           INTEGER NOT NULL,
  cost_per_products INTEGER NOT NULL
);

-- =========================
-- SUBSCRIPTIONS
-- customer 1-* subscription *-1 plan
-- subscription 1-1 shop
-- =========================

CREATE TABLE subscriptions (
  id             TEXT PRIMARY KEY,
  customer_id    BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  plan_id        TEXT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
  shop_id        TEXT NOT NULL UNIQUE REFERENCES shops(id) ON DELETE CASCADE, -- 1-1 subscription<->shop
  cant_products  INTEGER NOT NULL,
  state          TEXT NOT NULL CHECK (state IN ('waiting','paid','expired')),
  until_date     TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX idx_subscriptions_plan_id ON subscriptions(plan_id);

-- =========================
-- SHOP -> PRODUCTS (1-*)
-- =========================

CREATE TABLE products (
  id          TEXT PRIMARY KEY,
  shop_id     TEXT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  title       TEXT NOT NULL,
  price       NUMERIC(12,2) NOT NULL CHECK (price >= 0),
  description TEXT NOT NULL,
  image_url   TEXT NOT NULL
);

CREATE INDEX idx_products_shop_id ON products(shop_id);

-- =========================
-- SHOP -> CLIENTS (1-*)
-- =========================

CREATE TABLE clients (
  id       BIGSERIAL PRIMARY KEY,
  shop_id  TEXT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  name     TEXT NOT NULL,
  email    TEXT NOT NULL UNIQUE
);

CREATE INDEX idx_clients_shop_id ON clients(shop_id);

-- =========================
-- CLIENT -> ORDERS (1-*)
-- ORDER -> LINES (1-*)
-- LINE *-1 PRODUCT
-- =========================

CREATE TABLE orders (
  id         TEXT PRIMARY KEY,
  client_id  BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  status     TEXT NOT NULL CHECK (status IN ('pending','paid','canceled','expired')),
  currency   TEXT NOT NULL CHECK (currency IN ('ARS','USD'))
);

CREATE INDEX idx_orders_client_id ON orders(client_id);

CREATE TABLE order_lines (
  id         BIGSERIAL PRIMARY KEY,
  order_id   TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id TEXT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
  quantity   INTEGER NOT NULL CHECK (quantity > 0)
);

CREATE INDEX idx_order_lines_order_id ON order_lines(order_id);
CREATE INDEX idx_order_lines_product_id ON order_lines(product_id);

-- Opcional util: evitar el mismo producto duplicado dentro de la misma orden
-- (si tu logica es "si existe, sumo quantity" como en tu codigo)
ALTER TABLE order_lines
  ADD CONSTRAINT uq_order_lines_order_product UNIQUE (order_id, product_id);

-- =========================
-- JWT 1-1 customer AND 1-1 client
-- =========================

CREATE TABLE jwts (
  id            BIGSERIAL PRIMARY KEY,

  -- 1-1 con customer y 1-1 con client (un registro jwt pertenece a uno u otro)
  customer_id   BIGINT UNIQUE REFERENCES customers(id) ON DELETE CASCADE,
  client_id     BIGINT UNIQUE REFERENCES clients(id) ON DELETE CASCADE,

  -- persistimos lo que tu objeto expone en JSON
  access_token  TEXT NOT NULL,
  refresh_token TEXT NOT NULL,

  -- metadata util (sale del payload: sub/rango/kid). Si no queres, lo sacas.
  subject_user  TEXT,
  rango         TEXT,
  kid           TEXT,

  CHECK (
    (customer_id IS NOT NULL AND client_id IS NULL) OR
    (customer_id IS NULL AND client_id IS NOT NULL)
  )
);

CREATE INDEX idx_jwts_customer_id ON jwts(customer_id);
CREATE INDEX idx_jwts_client_id ON jwts(client_id);