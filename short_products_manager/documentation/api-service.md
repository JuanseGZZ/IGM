# API & Service Layer

## Index
- [Overview](#overview)
- [LocalDB (service.js)](#localdb-servicejs)
- [API (api.js)](#api-apijs)
- [Why Two Layers](#why-two-layers)
- [Backend Migration](#backend-migration)
- [Error Handling](#error-handling)

---

## Overview

Two thin layers sit between the UI and storage:

```
event.js  →  API (api.js)  →  LocalDB (service.js)  →  localStorage
```

The UI only ever calls `API.bring()` and `API.save(state)`. It never touches `LocalDB` or `localStorage` directly.

---

## LocalDB (service.js)

Reads and writes a **single JSON blob** under the key `spm_state`.

```js
const LocalDB = {
  save(state) { ... },  // serializes and writes
  load()      { ... }   // reads and deserializes
};
```

### `LocalDB.save(state)`

```js
LocalDB.save(state)
// → void
```

Calls `toJson()` on every product and brand, then writes:
```js
localStorage.setItem('spm_state', JSON.stringify({
  products: state.products.map(p => p.toJson()),
  brands:   state.brands.map(b => b.toJson())
}));
```

Attributes and variants are nested inside products — no separate keys.

### `LocalDB.load()`

```js
LocalDB.load()
// → { products: Product[], brands: Brand[] }
```

Reads `spm_state`, parses JSON, calls `fromJson` on each item. Returns empty arrays on missing key or parse error (safe default).

```js
try {
  const raw = JSON.parse(localStorage.getItem('spm_state') || '{}');
  return {
    products: (raw.products || []).map(Product.fromJson),
    brands:   (raw.brands   || []).map(Brand.fromJson)
  };
} catch {
  return { products: [], brands: [] };
}
```

---

## API (api.js)

Wraps `LocalDB` with `Promise` wrappers so callers are already using the async pattern required by a real HTTP API.

```js
const API = {
  bring: ()      => Promise.resolve(LocalDB.load()),
  save:  (state) => { LocalDB.save(state); return Promise.resolve(); }
};
```

### `API.bring()`

```js
API.bring()
// → Promise<{ products: Product[], brands: Brand[] }>
```

Resolves with the full deserialized state. Callers use `await`:

```js
const data = await API.bring();
App.state.products = data.products;
App.state.brands   = data.brands;
```

### `API.save(state)`

```js
API.save(state)
// → Promise<void>
```

Persists the current in-memory state. Called only when the user presses **Save**.

---

## Why Two Layers

`LocalDB` knows about `localStorage` — it is the storage adapter.  
`API` knows about the shape of the domain — it deserializes to model classes.

When migrating to a backend:
- `LocalDB` goes away entirely.
- `API` grows `fetch` calls.
- Nothing else changes.

If in the future different parts of state need different endpoints (e.g., `/products` and `/brands` as separate routes), that split happens inside `API` — `event.js` still calls only `API.bring()` and `API.save()`.

---

## Backend Migration

Replace `api.js` only. Minimal example:

```js
const BASE = '/api';

const API = {
  bring: async () => {
    const res = await fetch(`${BASE}/state`);
    const raw = await res.json();
    return {
      products: raw.products.map(Product.fromJson),
      brands:   raw.brands.map(Brand.fromJson)
    };
  },

  save: (state) =>
    fetch(`${BASE}/state`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        products: state.products.map(p => p.toJson()),
        brands:   state.brands.map(b => b.toJson())
      })
    })
};
```

If the backend uses granular endpoints instead of a single state blob, split the logic inside `bring` and `save` while keeping the same external interface.

---

## Error Handling

Currently `API.bring()` never rejects — `LocalDB.load()` swallows parse errors and returns empty arrays. This means a corrupted `spm_state` key silently resets to empty instead of crashing the app.

`API.save()` does not handle localStorage quota errors. If the stored state grows too large, `localStorage.setItem` will throw a `QuotaExceededError`. This is only a concern for very large product catalogs.

When migrating to a backend, add `.catch()` handling in the callers inside `event.js` (the `db-bring` and `db-save` actions) to surface network errors to the user.
