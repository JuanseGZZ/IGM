# Short Products Manager — Documentation Index

## Index
- [Project Overview](#project-overview)
- [File Structure](#file-structure)
- [Documentation Files](#documentation-files)
- [Quick Concepts](#quick-concepts)

---

## Project Overview

Product manager with a FastAPI + SQLite backend. All data lives in memory while you work; **Bring** loads from the backend, **Save** persists to the backend. The backend runs locally at `http://localhost:8000`.

Core domain: a **Product** has a **Brand**, a **photo**, owns a set of **Attributes** (each with a list of possible values), and generates **Variants** (one value per attribute, unique combinations, with a price). Each **Variant** tracks a history of **Stock** entries (quantity, date, unit cost).

---

## File Structure

```
short_products_manager/
├── index.html          — shell, Bootstrap CDN, loads all scripts
├── models.js           — domain classes (Brand, Attribute, Stock, Variant, Product)
├── service.js          — LocalDB: legacy localStorage adapter (not used in production)
├── api.js              — two-method API layer (bring / save) talking to FastAPI backend
├── render.js           — pure functions that return HTML strings
├── event.js            — App state, delegated click/change handlers, action router
├── documentation/
│   ├── index.md        — this file
│   ├── models.md       — classes, fields, toJson / fromJson
│   ├── data-flow.md    — in-memory state, Bring/Save cycle
│   ├── ui-system.md    — action system, modal system, render pattern
│   └── api-service.md  — API object, FastAPI backend summary
└── back/
    ├── requirements.txt
    └── app/
        ├── main.py     — FastAPI app, CORS middleware
        ├── api.py      — GET /api/state, PUT /api/state
        ├── dto.py      — Pydantic models (StateDTO, ProductDTO, VariantDTO, StockDTO …)
        ├── service.py  — orchestrates repositories, maps DB rows ↔ DTOs
        ├── repository.py — BaseRepository + Brand/Product/Attribute/Variant/Stock repos
        └── db.py       — SQLite connection helper, BaseRepository
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

**Stock is a history, not a counter.**
Each variant holds an append-style list of `Stock` entries (quantity, date, unit cost). The current stock level is always computed as the sum of all entries. Entries can be added, edited, or deleted; the total updates automatically.

**Photos are stored as base64.**
A product has at most one photo. It is stored as a base64 data URL (e.g. `data:image/jpeg;base64,...`) directly in the `photo` column of the SQLite `products` table. No separate file system or upload endpoint is needed.

**Two-button persistence.**
`Bring` = load everything from the backend into memory. `Save` = flush memory back to the backend. All CRUD operations (including stock and photo changes) only touch in-memory state until you press Save.

**One action system.**
Every interactive element uses `data-action="..."`. A single delegated listener on `document` routes all clicks through `App.handleAction`. A separate `change` listener handles the photo file input. Adding a new feature = add a case to the action router.
