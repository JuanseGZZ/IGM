# UI System

## Index
- [Action System](#action-system)
- [Full Action Reference](#full-action-reference)
- [Modal System](#modal-system)
- [Modal Types](#modal-types)
- [Render Pattern](#render-pattern)
- [Tab System](#tab-system)
- [Attribute Value Staging](#attribute-value-staging)
- [Adding a New Feature](#adding-a-new-feature)

---

## Action System

Every interactive element (button, link) that triggers logic uses a `data-action` attribute:

```html
<button type="button" data-action="new-product">+ New Product</button>
<button type="button" data-action="delete-attr" data-product-id="abc" data-id="xyz">×</button>
```

A **single delegated listener** on `document` catches all clicks:

```js
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (btn) {
    e.preventDefault();
    App.handleAction(btn.dataset.action, btn);
    return;
  }
  // tab clicks handled separately via data-tab
});
```

`handleAction(action, target)` is a long if-chain that dispatches by action name. `target` is the element, so `target.dataset.id`, `target.dataset.productId`, etc. carry the context.

**All save buttons are `type="button"`** (not `type="submit"`) so they flow through this same click handler. `form.reportValidity()` is called manually before saving.

---

## Full Action Reference

### Global
| Action | Triggered by | Effect |
|---|---|---|
| `db-bring` | Bring button | Loads state from storage |
| `db-save` | Save button | Persists state to storage |
| `close-modal` | Cancel / Close buttons | Closes the active modal |

### Products
| Action | Extra data attrs | Effect |
|---|---|---|
| `new-product` | — | Opens product form (create) |
| `edit-product` | `data-id` | Opens product form (edit) |
| `delete-product` | `data-id` | Confirms + removes product |
| `save-product` | — | Validates + submits product form |
| `manage-variants` | `data-product-id` | Opens variants modal |

### Attributes (owned by product)
| Action | Extra data attrs | Effect |
|---|---|---|
| `new-attr` | `data-product-id` | Opens attr form (create on product) |
| `edit-attr` | `data-product-id`, `data-id` | Opens attr form (edit) |
| `delete-attr` | `data-product-id`, `data-id` | Confirms + removes attribute |
| `save-attr` | — | Validates + submits attr form |
| `copy-attr` | `data-product-id` | Opens copy picker modal |
| `confirm-copy-attr` | `data-source-product-id`, `data-attr-id`, `data-target-product-id` | Copies attribute to target product |
| `add-value` | — | Appends pending value to attr staging |
| `remove-value` | `data-index` | Removes value at index from staging |

### Variants
| Action | Extra data attrs | Effect |
|---|---|---|
| `save-variant` | — | Add or update variant (checks uniqueness) |
| `edit-variant` | `data-product-id`, `data-id` | Pre-fills form with variant data |
| `cancel-edit-variant` | `data-product-id` | Resets form to "Add" mode |
| `delete-variant` | `data-product-id`, `data-id` | Removes variant |

### Stock
| Action | Extra data attrs | Effect |
|---|---|---|
| `manage-stock` | `data-product-id`, `data-id` (variant) | Opens stock modal for that variant |
| `save-stock` | — | Add new entry if `stock-id` hidden input is empty; update existing if set |
| `edit-stock` | `data-product-id`, `data-variant-id`, `data-id` | Pre-fills form with entry data |
| `cancel-edit-stock` | `data-product-id`, `data-variant-id` | Resets form to "Add" mode |
| `delete-stock` | `data-product-id`, `data-variant-id`, `data-id` | Confirms + removes entry |
| `back-to-variants` | `data-product-id` | Closes stock modal, reopens variants modal |

### Brands
| Action | Extra data attrs | Effect |
|---|---|---|
| `new-brand` | — | Opens brand form (create) |
| `edit-brand` | `data-id` | Opens brand form (edit) |
| `delete-brand` | `data-id` | Confirms + removes brand |
| `save-brand` | — | Validates + submits brand form |

---

## Modal System

One modal overlay lives in `index.html`:

```html
<div id="modal-overlay">        <!-- full-screen backdrop -->
  <div id="modal-box">          <!-- centered white card -->
    <div id="modal-body"></div> <!-- dynamic content injected here -->
  </div>
</div>
```

Visibility is toggled with the `.open` CSS class on `#modal-overlay`:

```js
overlay.classList.add('open');     // show
overlay.classList.remove('open');  // hide
```

`App.state.modal` holds the current modal state:
```js
{ type: 'product' | 'attr' | 'attr-copy' | 'variants' | 'brand', data: any }
```

`null` means no modal is open.

**Clicking the backdrop** (the overlay itself, not the box) closes the modal.

**Partial re-renders** — some actions re-render only `#modal-body` without closing and reopening the modal. This is used when:
- Adding/removing attribute values (stays in attr form)
- Adding/editing/deleting variants (stays in variants modal)

```js
document.getElementById('modal-body').innerHTML = Render.variantsModal(product);
```

---

## Modal Types

| Type | `modal.data` shape | Render function |
|---|---|---|
| `'product'` | `Product \| null` | `Render.productForm(data, brands)` |
| `'attr'` | `{ product, attr: Attribute \| null }` | `Render.attrForm(data.attr, pendingValues, pendingKey)` |
| `'attr-copy'` | `{ targetProductId }` | `Render.attrCopyPicker(products, targetProductId)` |
| `'variants'` | `{ product }` | `Render.variantsModal(product, editingVariant?)` |
| `'brand'` | `Brand \| null` | `Render.brandForm(data)` |
| `'stock'` | `{ product, variant }` | `Render.stockModal(product, variant, editingStock?)` |

---

## Render Pattern

`render.js` contains only **pure functions** that return HTML strings. No DOM reads or writes happen there.

```js
const Render = {
  productCard(product)  { return `<div class="card">...</div>`; },
  productsTab(products) { return products.map(p => this.productCard(p)).join(''); },
  productForm(product, allBrands) { return `<form id="product-form">...</form>`; },
  // ...
};
```

`App.render()` in `event.js` is the single place that writes to the DOM:

```js
render() {
  document.getElementById('tabs').innerHTML    = Render.tabs(tab);
  document.getElementById('content').innerHTML = Render.productsTab(products); // or brandsTab
  document.getElementById('modal-body').innerHTML = Render.productForm(...);   // when modal open
}
```

Because the whole subtree is replaced on each render, **no stale event listeners accumulate** — all events are delegated to `document`.

`esc(str)` in `render.js` escapes HTML special characters for every user-provided string injected into templates, preventing XSS.

---

## Tab System

Tabs use `data-tab` (not `data-action`) so they are handled by a separate branch in the click listener:

```html
<button type="button" class="nav-link" data-tab="products">Products</button>
```

```js
const tab = e.target.closest('[data-tab]');
if (tab) { App.state.tab = tab.dataset.tab; App.render(); }
```

Current tabs: `'products'`, `'brands'`.

---

## Attribute Value Staging

Editing attribute values requires a live preview that updates before the form is saved. This uses two staging fields in `App.state`:

```js
attrPendingValues: string[]   // values being built
attrPendingKey:    string     // key field preserved across re-renders
```

When `add-value` fires:
1. Read current key from `#attr-form [name="key"]` → store in `attrPendingKey`
2. Push new value to `attrPendingValues`
3. Re-render only `#modal-body` (keeps modal open, updates preview)

When `save-attr` fires:
- `attrPendingValues` is used as the final `values` array for the new Attribute
- The key comes from `FormData` (current input value)

On `openModal('attr', ...)` the staging is initialized from the existing attribute (edit) or empty (create).

---

## Photo File Input

The photo field in the product form uses a `change` event instead of the click-based action system, because file inputs fire `change` not `click`. A dedicated listener in `App.init()` handles it:

```js
document.addEventListener('change', (e) => {
    if (e.target.id !== 'photo-input') return;
    const reader = new FileReader();
    reader.onload = (evt) => {
        document.getElementById('photo-data').value = evt.target.result;  // hidden input
        document.getElementById('photo-preview').src = evt.target.result; // img preview
    };
    reader.readAsDataURL(e.target.files[0]);
});
```

When `save-product` fires, `FormData` picks up `photo-data` (the hidden input) and `handleProductSubmit` passes it to `new Product(...)`.

---

## Adding a New Feature

1. **Add HTML** in `render.js` — a new method or an addition to an existing card/form. Use `data-action="your-action"` on the trigger element.
2. **Handle the action** in `event.js → handleAction` — add an `if (action === 'your-action')` block. Mutate `App.state`, then call `this.render()` (or re-render only `#modal-body` if inside a modal).
3. **Persist shape** — if the action introduces new data, update the model in `models.js` (`toJson`/`fromJson`), the DTO in `back/app/dto.py`, and the repository + service in the backend.
