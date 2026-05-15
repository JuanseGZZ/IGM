# API & Service Layer

## Index
- [Overview](#overview)
- [API (api.js)](#api-apijs)
- [FastAPI Backend](#fastapi-backend)
- [SQLite Schema](#sqlite-schema)
- [Error Handling](#error-handling)

---

## Overview

```
event.js  →  API (api.js)  →  FastAPI backend (localhost:8000)  →  SQLite (products.db)
```

The UI only ever calls `API.bring()` and `API.save(state)`. The backend exposes two endpoints that map directly to those two operations.

---

## API (api.js)

```js
const BASE = "http://localhost:8000/api";

const API = {
  bring: async () => { ... },   // GET  /api/state
  save:  async (state) => { ... } // PUT  /api/state
};
```

### `API.bring()`

```js
API.bring()
// → Promise<{ products: Product[], brands: Brand[] }>
```

Fetches `GET /api/state`, deserializes the response with `fromJson` on every nested object, and resolves with typed arrays.

### `API.save(state)`

```js
API.save(state)
// → Promise<void>
```

Sends `PUT /api/state` with the full state serialized via `toJson()`. Throws on non-2xx response so the caller can surface the error.

---

## FastAPI Backend

Start with:
```powershell
cd short_products_manager\back
python -m uvicorn app.main:app --reload
```

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/state` | Returns full state: products (with attributes, variants, stocks), brands |
| `PUT` | `/api/state` | Full replace — deletes everything then re-inserts from request body |

### Layer breakdown

| File | Role |
|---|---|
| `main.py` | FastAPI app, CORS (`allow_origins=["*"]`), mounts `/api` router |
| `api.py` | Route handlers — thin, delegates to `ProductService` |
| `dto.py` | Pydantic models for request/response validation |
| `service.py` | Orchestrates repositories; maps DB rows ↔ DTOs |
| `repository.py` | `BaseRepository` + domain-specific repos (Brand, Product, Attribute, Variant, Stock) |
| `db.py` | `_conn()` context manager, `BaseRepository` base class with generic CRUD |

### DTOs (`dto.py`)

```
StateDTO
├── products: list[ProductDTO]
└── brands:   list[BrandDTO]

ProductDTO
├── id, name, description: str
├── photo:             Optional[str]   — base64 data URL or null
├── brand:             Optional[BrandDTO]
├── attributes:        list[AttributeDTO]
└── variants:          list[VariantDTO]

VariantDTO
├── id, price
├── implementations:   list[AttributeImplementationDTO]
└── historical_stocks: list[StockDTO]

StockDTO
├── id:              str
├── quantity:        float
├── date:            str
└── cost_unit_price: float
```

---

## SQLite Schema

Database file: `short_products_manager/back/products.db`

```sql
CREATE TABLE brands (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE products (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    brand_id    TEXT,
    photo       TEXT          -- base64 data URL, nullable
);

CREATE TABLE attributes (
    id          TEXT PRIMARY KEY,
    product_id  TEXT NOT NULL,
    key         TEXT NOT NULL,
    attr_values TEXT NOT NULL DEFAULT '[]'  -- JSON array of strings
);

CREATE TABLE variants (
    id              TEXT PRIMARY KEY,
    product_id      TEXT NOT NULL,
    price           REAL NOT NULL DEFAULT 0,
    implementations TEXT NOT NULL DEFAULT '[]'  -- JSON array of {attributeId, value}
);

CREATE TABLE stocks (
    id              TEXT PRIMARY KEY,
    variant_id      TEXT NOT NULL,
    quantity        REAL NOT NULL DEFAULT 0,
    date            TEXT NOT NULL,
    cost_unit_price REAL NOT NULL DEFAULT 0
);
```

`attr_values` and `implementations` are stored as JSON strings (not normalized). `photo` is a TEXT column holding a full base64 data URL — it can be large for high-resolution images.

The `photo` column is added automatically via `ALTER TABLE` when `ProductRepository` initializes, so existing databases without it are migrated on the next backend start.

---

## Error Handling

**Backend unreachable:** `API.bring()` rejects → `App.init()` shows an alert with instructions to start the server. The UI renders an empty state without crashing.

**Save failure:** `API.save()` throws if the response is not 2xx. The error propagates as an unhandled promise rejection (visible in the browser console). The save button does not show "Saved!" on failure.

**Database migration:** The `photo` column is added via `ALTER TABLE products ADD COLUMN photo TEXT` inside `ProductRepository.__init__`. SQLite raises an error if the column already exists; that error is swallowed silently, so the migration is idempotent.
