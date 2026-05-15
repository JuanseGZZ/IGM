# showShop — Documentation Index

## Index
- [Project Overview](#project-overview)
- [File Structure](#file-structure)
- [Documentation Files](#documentation-files)
- [Quick Concepts](#quick-concepts)

---

## Project Overview

Read-only customer-facing product gallery. Fetches the catalog from the same FastAPI backend used by the admin (`short_products_manager`). Visitors can browse products, select attribute combinations, and see the matching variant price.

No write operations — the shop never modifies backend data.

---

## File Structure

```
showShop/
├── index.html        — shell, Bootstrap CDN, loads all scripts
├── models.js         — domain classes (Brand, Attribute, Stock, Variant, Product)
├── service.js        — LocalCache: caches last fetch in localStorage for instant load
├── api.js            — API.bring() — read-only, no save
├── render.js         — pure functions that return HTML strings
├── events.js         — Shop state, delegated click handler, action router
└── documentation/
    ├── index.md      — this file
    ├── models.md     — classes and their fields
    ├── data-flow.md  — cache strategy, bring cycle
    ├── ui-system.md  — action system, modal, render pattern
    └── api-service.md — API layer, LocalCache, backend connection
```

---

## Documentation Files

| File | What it covers |
|---|---|
| [models.md](models.md) | All domain classes, fields, fromJson |
| [data-flow.md](data-flow.md) | Cache-first load strategy, data flow from backend to DOM |
| [ui-system.md](ui-system.md) | Action system, modal, render functions, variant picker |
| [api-service.md](api-service.md) | API layer, LocalCache, backend dependency |

---

## Quick Concepts

**Read-only.**
The shop has no Save button, no CRUD forms. All it does is fetch and display. `api.js` only exposes `API.bring()`.

**Cache-first load.**
On startup, `LocalCache.load()` restores the last fetched state from `localStorage` instantly, so the grid appears before the API responds. The API response then refreshes the view and updates the cache.

**Variant picker.**
Each product modal lets the visitor select one value per attribute (pill buttons). When all attributes have a selection, the matching variant's price is shown. The selection lives only in `Shop.state.selection` — it is never persisted.

**Shared backend.**
Both the admin (`short_products_manager`) and the shop connect to `http://localhost:8000/api/state`. The backend must be running for fresh data. Without it, the shop falls back to the local cache.

**Models are kept in sync manually.**
`models.js` is a copy of the admin's `models.js`. If the admin's domain classes change (new fields, new classes), this file must be updated to match.
