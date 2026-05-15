# Data Flow

## Index
- [Overview](#overview)
- [Cache-First Load Strategy](#cache-first-load-strategy)
- [In-Memory State](#in-memory-state)
- [LocalCache Schema](#localcache-schema)

---

## Overview

```
SQLite (products.db)
    │  via FastAPI backend at localhost:8000
    │
    │  API.bring()  (GET /api/state)
    ▼
Shop.state  (in-memory)
    │                         ┌──────────────────────┐
    │  renderGrid()           │  localStorage         │
    ▼                         │  key: spm_shop_cache  │
DOM                           │                       │
                              │  LocalCache.save()  ◀─┤  after every successful bring
                              │  LocalCache.load()  ──┼▶ on startup (instant display)
                              └──────────────────────┘
```

The shop is **read-only** — it never writes to the backend.

---

## Cache-First Load Strategy

On `Shop.init()`:

1. **Instant load from cache** — `LocalCache.load()` restores the last fetched state from `localStorage`. If data exists, `renderGrid()` is called immediately so the visitor sees products with zero network delay.
2. **Background fetch** — `API.bring()` runs concurrently. When it resolves, `Shop.state` is replaced with fresh data, `LocalCache.save()` updates the cache, and `renderGrid()` re-renders.
3. **Error fallback** — if `API.bring()` rejects and the cache was empty (first visit with backend down), an error message is shown. If the cache had data, the visitor sees stale-but-useful content with no error shown.

```js
// events.js — init sequence
const cached = LocalCache.load();
if (cached.products.length) {
    this.state.products = cached.products;
    this.renderGrid();          // instant
}

API.bring().then(data => {
    this.state.products = data.products;
    LocalCache.save(this.state); // update cache
    this.renderGrid();           // refresh with fresh data
}).catch(() => {
    if (!this.state.products.length) showError();
    // else: stale cache is shown, no error
});
```

---

## In-Memory State

Defined in `events.js` as `Shop.state`:

```js
{
  products:  Product[],
  brands:    Brand[],
  activeId:  string | null,  // product id currently open in modal
  selection: object          // { [attrId]: value } — visitor's current attribute picks
}
```

`selection` is reset to `{}` every time a new modal is opened. It is never persisted.

---

## LocalCache Schema

Single `localStorage` key: `spm_shop_cache`

```json
{
  "products": [ ...same shape as backend /api/state response... ],
  "brands":   [ ... ]
}
```

The cache is written only after a successful `API.bring()`. A failed or missing cache returns `{ products: [], brands: [] }` safely.
