# API & Service Layer

## Index
- [Overview](#overview)
- [API (api.js)](#api-apijs)
- [LocalCache (service.js)](#localcache-servicejs)
- [Backend Dependency](#backend-dependency)
- [Error Handling](#error-handling)

---

## Overview

```
events.js
    │
    ├── API.bring()      →  GET http://localhost:8000/api/state  →  SQLite
    │
    └── LocalCache       →  localStorage key: spm_shop_cache
```

The shop is read-only. `API` exposes only `bring` — there is no `save`.

---

## API (api.js)

```js
const BASE = "http://localhost:8000/api";

const API = {
    bring: async () => {
        const res = await fetch(`${BASE}/state`);
        if (!res.ok) throw new Error(`Bring failed: ${res.status}`);
        const raw = await res.json();
        return {
            products: raw.products.map(Product.fromJson),
            brands:   raw.brands.map(Brand.fromJson)
        };
    }
};
```

Fetches the full catalog from the backend and deserializes it into typed model instances. Throws on non-2xx so the caller can handle network errors.

---

## LocalCache (service.js)

Stores the last successful fetch result in `localStorage` under `spm_shop_cache`. Enables instant display on repeat visits even before the backend responds.

```js
LocalCache.save(state)   // serializes products + brands → localStorage
LocalCache.load()        // → { products: Product[], brands: Brand[] }
LocalCache.clear()       // removes the cache key
```

`save` silently swallows `QuotaExceededError` — if localStorage is full, the cache is simply not updated and the shop fetches fresh data on the next visit.

`load` returns `{ products: [], brands: [] }` on any parse error or missing key, never throws.

---

## Backend Dependency

Both the admin and the shop connect to the same backend:

```
http://localhost:8000/api/state
```

The backend must be running for fresh data. To start it:

```powershell
cd short_products_manager\back
python -m uvicorn app.main:app --reload
```

The shop does **not** need the backend to render if the `LocalCache` has data from a previous session.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Backend down, cache empty | Error message shown in the grid |
| Backend down, cache has data | Stale cache rendered silently (no error) |
| Backend responds, data changed | Cache updated, grid re-rendered with fresh data |
| `localStorage` full on save | Cache write skipped silently, data not lost |
| Non-2xx response from backend | `API.bring()` throws → caught in `events.js` |
