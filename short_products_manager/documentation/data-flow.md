# Data Flow

## Index
- [Overview](#overview)
- [In-Memory State](#in-memory-state)
- [Bring — Load from Storage](#bring--load-from-storage)
- [Save — Persist to Storage](#save--persist-to-storage)
- [CRUD Operations](#crud-operations)
- [localStorage Schema](#localstorage-schema)
- [Auto-Bring on Startup](#auto-bring-on-startup)
- [Backend Migration Path](#backend-migration-path)

---

## Overview

```
SQLite (products.db)
    │  via FastAPI backend at localhost:8000
    │
    │  Bring (GET /api/state)     Save (PUT /api/state)
    │ ──────────────────────▶     ◀──────────────────────
    │
App.state  (in-memory)
    │
    │  render()
    ▼
DOM
```

All CRUD operations (create, edit, delete products / attributes / brands / variants / stock entries, change photo) **only modify `App.state`**. Nothing touches the backend until the user explicitly presses **Save**.

---

## In-Memory State

Defined in `event.js` as `App.state`:

```js
{
  tab:               string,      // active tab: 'products' | 'brands'
  products:          Product[],
  brands:            Brand[],
  modal:             object|null, // { type, data } — see ui-system.md
  attrPendingValues: string[],    // staging area while editing attr values
  attrPendingKey:    string       // staging area while editing attr key
}
```

`attrPendingValues` and `attrPendingKey` are only meaningful when a modal of type `'attr'` is open. They hold the in-progress edits before the form is submitted, because the attribute value list re-renders the modal body on each add/remove.

---

## Bring — Load from Storage

```js
API.bring()  →  Promise<{ products: Product[], brands: Brand[] }>
```

Sends `GET /api/state` to the FastAPI backend. The backend reads from SQLite, assembles a full `StateDTO` (products with attributes, variants with stock entries, brands), and returns JSON. `API.bring` deserializes every nested object using `fromJson` and resolves with plain arrays. The caller replaces `App.state.products` and `App.state.brands` in full, then calls `render()`.

**Bring replaces state entirely** — any unsaved in-memory changes are lost.

---

## Save — Persist to Storage

```js
API.save(state)  →  Promise<void>
```

Sends `PUT /api/state` with the full serialized state. The backend does a **full replace**: deletes all stocks → variants → attributes → products → brands, then re-inserts everything from the request body. This keeps persistence simple at the cost of not supporting concurrent edits.

The Save button shows "Saved!" for 1.2 s after success.

---

## CRUD Operations

Each operation mutates `App.state` in place. Most call `render()` afterwards; stock operations re-render only `#modal-body` to stay inside the stock modal.

| Operation | State change |
|---|---|
| Create product | `state.products.push(new Product(...))` |
| Edit product | `state.products[i] = new Product(...)` — preserves existing attributes, variants, and photo |
| Delete product | `state.products = state.products.filter(...)` |
| Change photo | `FileReader` reads the file → hidden input → picked up by `handleProductSubmit` |
| Create/edit attribute | `product.attributes[i] = new Attribute(...)` |
| Delete attribute | `product.attributes = product.attributes.filter(...)` |
| Copy attribute | `product.attributes.push(new Attribute(genId(), ...))` — new ID, no link to source |
| Create/edit variant | `product.variants[i] = new Variant(...)` |
| Delete variant | `product.variants = product.variants.filter(...)` |
| Add stock entry | `variant.historical_stocks.push(new Stock(genId(), ...))` |
| Edit stock entry | `variant.historical_stocks[i] = new Stock(existingId, ...)` |
| Delete stock entry | `variant.historical_stocks = variant.historical_stocks.filter(...)` |
| Create/edit brand | `state.brands[i] = new Brand(...)` |
| Delete brand | `state.brands = state.brands.filter(...)` |

None of these write to the backend.

---

## JSON Schema (Bring / Save payload)

```json
{
  "products": [
    {
      "id": "abc123",
      "name": "Remera Lisa",
      "description": "",
      "photo": "data:image/jpeg;base64,...",
      "brand": { "id": "b1", "name": "Nike" },
      "attributes": [
        { "id": "a1", "key": "Talle", "values": ["S", "M", "L"] },
        { "id": "a2", "key": "Color", "values": ["Negro", "Blanco"] }
      ],
      "variants": [
        {
          "id": "v1",
          "price": 25.00,
          "implementations": [
            { "attributeId": "a1", "value": "M" },
            { "attributeId": "a2", "value": "Negro" }
          ],
          "historical_stocks": [
            { "id": "s1", "quantity": 20, "date": "2026-05-01", "cost_unit_price": 14.50 },
            { "id": "s2", "quantity": 10, "date": "2026-05-14", "cost_unit_price": 15.00 }
          ]
        }
      ]
    }
  ],
  "brands": [
    { "id": "b1", "name": "Nike" }
  ]
}
```

`photo` is `null` when no photo has been set. `historical_stocks` defaults to `[]`.

---

## Auto-Bring on Startup

`App.init()` calls `API.bring()` once on page load. This pre-populates state from the backend so the user sees their last saved data immediately. If the backend is unreachable, an alert explains how to start the server — the UI renders empty state without crashing.
