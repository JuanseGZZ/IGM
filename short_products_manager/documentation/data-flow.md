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
localStorage
    │
    │  Bring (API.bring)          Save (API.save)
    │ ─────────────────▶          ◀─────────────────
    │
App.state  (in-memory)
    │
    │  render()
    ▼
DOM
```

All CRUD operations (create, edit, delete products / attributes / brands / variants) **only modify `App.state`**. Nothing touches storage until the user explicitly presses **Save**.

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

Reads the single JSON blob from `localStorage`, deserializes every nested object using `fromJson`, and resolves with plain arrays. The caller (`App.handleAction('db-bring')` or the startup auto-bring) replaces `App.state.products` and `App.state.brands` in full, then calls `render()`.

**Bring replaces state entirely** — any unsaved in-memory changes are lost.

---

## Save — Persist to Storage

```js
API.save(state)  →  Promise<void>
```

Calls `LocalDB.save(state)`, which serializes `state.products` and `state.brands` via `toJson()` and writes a single key to `localStorage`:

```js
localStorage.setItem('spm_state', JSON.stringify({ products: [...], brands: [...] }))
```

Attributes are serialized as part of their owning product — there is no top-level `attributes` key.

The Save button shows "Saved!" for 1.2 s after success.

---

## CRUD Operations

Each operation mutates `App.state` in place and then calls `render()`:

| Operation | State change |
|---|---|
| Create product | `state.products.push(new Product(...))` |
| Edit product | `state.products[i] = new Product(...)` — preserves existing attributes and variants |
| Delete product | `state.products = state.products.filter(...)` |
| Create/edit attribute | `product.attributes[i] = new Attribute(...)` |
| Delete attribute | `product.attributes = product.attributes.filter(...)` |
| Copy attribute | `product.attributes.push(new Attribute(genId(), ...))` — new ID, no link to source |
| Create/edit variant | `product.variants[i] = new Variant(...)` |
| Delete variant | `product.variants = product.variants.filter(...)` |
| Create/edit brand | `state.brands[i] = new Brand(...)` |
| Delete brand | `state.brands = state.brands.filter(...)` |

None of these write to `localStorage`.

---

## localStorage Schema

Single key: `spm_state`

```json
{
  "products": [
    {
      "id": "abc123",
      "name": "Remera Lisa",
      "description": "",
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

---

## Auto-Bring on Startup

`App.init()` calls `API.bring()` once on page load. This pre-populates state from whatever is in localStorage so the user sees their last saved data immediately, without needing to press Bring manually.

---

## Backend Migration Path

The entire persistence layer is isolated in two files:

1. **`service.js`** — `LocalDB.load()` and `LocalDB.save(state)`. Replace these with `fetch` calls.
2. **`api.js`** — `API.bring()` and `API.save(state)`. Already returns Promises, so callers need no changes.

`event.js`, `render.js`, and `models.js` are backend-agnostic and require zero changes.

```js
// api.js after migration
const API = {
  bring: () =>
    fetch('/api/state').then(r => r.json()).then(raw => ({
      products: raw.products.map(Product.fromJson),
      brands:   raw.brands.map(Brand.fromJson)
    })),
  save: (state) =>
    fetch('/api/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        products: state.products.map(p => p.toJson()),
        brands:   state.brands.map(b => b.toJson())
      })
    })
};
```
