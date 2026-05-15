# UI System

## Index
- [Action System](#action-system)
- [Action Reference](#action-reference)
- [Modal System](#modal-system)
- [Variant Picker](#variant-picker)
- [Render Pattern](#render-pattern)

---

## Action System

Same pattern as the admin: every interactive element uses `data-action`. A single delegated listener on `document` handles all clicks.

```js
document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    // dispatch by action name
});
```

No form submissions, no `type="submit"` buttons — everything flows through this handler.

---

## Action Reference

| Action | Extra data attrs | Effect |
|---|---|---|
| `open-product` | `data-id` | Opens the product modal, resets selection |
| `close-modal` | — | Closes the active modal |
| `select-attr` | `data-attr-id`, `data-value` | Records the visitor's pick, re-renders modal to update price |

---

## Modal System

One overlay in `index.html`:

```html
<div id="modal-overlay">
    <div id="modal-box">
        <div id="modal-body"></div>
    </div>
</div>
```

Visibility is toggled with `.open` on `#modal-overlay`. Clicking the backdrop closes the modal.

`_refreshModal()` re-renders `#modal-body` in place without toggling the overlay — used every time the visitor selects an attribute value so the price updates without reopening.

---

## Variant Picker

The product modal renders one group of pill buttons per attribute:

```html
<button class="attr-pill [selected]"
        data-action="select-attr"
        data-attr-id="a1"
        data-value="Rojo">Rojo</button>
```

When `select-attr` fires:
1. `Shop.state.selection[attrId] = value` is updated.
2. `_refreshModal()` re-renders the modal with the new selection.
3. `Render.productModal` checks if all attributes have a pick. If yes, it finds the matching variant and renders its price.

**Matching logic:**

```js
const matched = product.variants.find(v =>
    v.implementations.every(i => selection[i.attributeId] === i.value)
);
```

If no variant matches (all attributes selected but no combination exists in the catalog), the price block shows nothing — this situation shouldn't occur with valid data.

---

## Render Pattern

`render.js` contains only pure functions returning HTML strings:

```js
const Render = {
    grid(products)                      // → HTML for the full product grid
    productCard(product)                // → HTML for one grid card
    productModal(product, selection)    // → HTML for the detail modal
};
```

`Shop.renderGrid()` writes to `#grid`. `Shop._refreshModal()` writes to `#modal-body`. No other DOM writes happen outside those two methods.

`esc(str)` in `render.js` escapes all user-provided strings before injecting into templates.
