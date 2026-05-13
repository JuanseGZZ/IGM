# Short Products Manager — Documentation Index

## Index
- [Project Overview](#project-overview)
- [File Structure](#file-structure)
- [Documentation Files](#documentation-files)
- [Quick Concepts](#quick-concepts)

---

## Project Overview

Local-first product manager. All data lives in memory while you work; **Bring** loads from storage, **Save** persists to storage. No backend required — when one is ready, only `api.js` needs to change.

Core domain: a **Product** has a **Brand**, owns a set of **Attributes** (each with a list of possible values), and generates **Variants** (one value per attribute, unique combinations, with a price).

---

## File Structure

```
short_products_manager/
├── index.html          — shell, Bootstrap CDN, loads all scripts
├── models.js           — domain classes (Brand, Attribute, Variant, Product …)
├── service.js          — LocalDB: reads/writes a single JSON blob to localStorage
├── api.js              — two-method API layer (bring / save)
├── render.js           — pure functions that return HTML strings
├── event.js            — App state, delegated click handler, action router
└── documentation/
    ├── index.md        — this file
    ├── models.md       — classes, fields, toJson / fromJson
    ├── data-flow.md    — in-memory state, Bring/Save cycle, migration path
    ├── ui-system.md    — action system, modal system, render pattern
    └── api-service.md  — LocalDB, API object, backend migration
```

---

## Documentation Files

| File | What it covers |
|---|---|
| [models.md](models.md) | All domain classes, their fields, serialization contract |
| [data-flow.md](data-flow.md) | How data moves from storage → memory → UI and back |
| [ui-system.md](ui-system.md) | `data-action` pattern, modal lifecycle, render functions |
| [api-service.md](api-service.md) | LocalDB, API layer, how to swap in a real backend |

---

## Quick Concepts

**Attributes belong to products, not the system.**
There is no global attribute library. Each product owns its attributes. Use "Copy from…" to duplicate an attribute from another product as an independent copy.

**Variants are combinations.**
A variant picks exactly one value from each of the product's attributes. No partial variants, no duplicates.

**Two-button persistence.**
`Bring` = load everything from storage into memory. `Save` = flush memory to storage. All CRUD operations only touch in-memory state until you press Save.

**One action system.**
Every interactive element uses `data-action="..."`. A single delegated listener on `document` routes all clicks through `App.handleAction`. Adding a new feature = add a case to that switch.
