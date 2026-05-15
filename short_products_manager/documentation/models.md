# Models

## Index
- [genId](#genid)
- [Brand](#brand)
- [Attribute](#attribute)
- [AttributeImplementation](#attributeimplementation)
- [Stock](#stock)
- [Variant](#variant)
- [Product](#product)
- [Serialization Contract](#serialization-contract)
- [Ownership Rules](#ownership-rules)

---

## genId

```js
function genId()  // → string
```

Generates a short unique ID using `Date.now()` + random suffix (base-36). Used any time a new entity is created without an existing ID.

---

## Brand

Represents a brand that can be assigned to products.

```
Brand
├── id:   string   — unique identifier
└── name: string   — display name
```

```js
new Brand(id, name)
brand.toJson()         // → { id, name }
Brand.fromJson(data)   // → Brand
```

---

## Attribute

A characteristic of a product with a set of allowed values.

```
Attribute
├── id:     string     — unique identifier (scoped to its product)
├── key:    string     — label, e.g. "Color", "Size", "Material"
└── values: string[]   — possible options, e.g. ["Red", "Blue", "Green"]
```

```js
new Attribute(id, key, values)
attr.toJson()            // → { id, key, values }
Attribute.fromJson(data) // → Attribute
```

**Ownership:** Attributes belong to a single Product. There is no global attribute pool.  
**Copying:** Use "Copy from…" in the UI to clone an attribute from another product. The copy gets a new `genId()` and has no link to the original.

---

## AttributeImplementation

A single selection: one Attribute + one chosen value from that attribute's `values` list. Used inside Variants.

```
AttributeImplementation
├── attributeId: string   — matches Attribute.id on the same product
└── value:       string   — one of Attribute.values
```

```js
new AttributeImplementation(attributeId, value)
impl.toJson()                       // → { attributeId, value }
AttributeImplementation.fromJson(d) // → AttributeImplementation
```

---

## Stock

A single stock entry belonging to a variant. Stock is append-style: new deliveries are added as new entries. The current stock level = `sum(entry.quantity)` over all entries.

```
Stock
├── id:              string   — unique identifier
├── quantity:        number   — units in this entry (positive integer)
├── date:            string   — ISO date, e.g. "2026-05-14"
└── cost_unit_price: number   — purchase cost per unit (default 0)
```

```js
new Stock(id, quantity, date, cost_unit_price)
stock.toJson()          // → { id, quantity, date, cost_unit_price }
Stock.fromJson(data)    // → Stock
```

**Total cost of entry:** `quantity × cost_unit_price` (computed in the UI, not stored).

---

## Variant

A unique combination of one value per attribute, with a price, a stock history, and an optional discount.

```
Variant
├── id:               string                     — unique identifier
├── price:            number                     — unit sale price
├── implementations:  AttributeImplementation[]  — one entry per product attribute
├── historical_stocks: Stock[]                   — append-only list of stock entries (default [])
└── oferta:           number | null              — discount fraction 0–1 (e.g. 0.2 = 20% off), null = no offer
```

```js
new Variant(id, price, implementations, historical_stocks = [], oferta = null)
variant.toJson()          // → { id, price, implementations: [...], historical_stocks: [...], oferta }
Variant.fromJson(data)    // → Variant
```

**Offer display:** `Math.round(oferta * 100)` → percentage shown to the visitor. `null` means no active offer.  
**Bulk offer:** The product form exposes "Aplicar a todas" / "Quitar oferta" buttons that set or clear `oferta` on every variant of the product at once.

**Uniqueness rule:** Two variants are equal if every `AttributeImplementation` pair matches (same `attributeId` and same `value`). The UI enforces this on add and on edit (excluding self).

**Completeness rule:** A valid variant has exactly one `AttributeImplementation` per product attribute. The form enforces this with required selects.

**Stock level:** computed on the fly as `variant.historical_stocks.reduce((sum, s) => sum + s.quantity, 0)`. Never stored as a separate field.

---

## Product

The root aggregate. Owns all attributes, variants, a brand reference, and a photo.

```
Product
├── id:          string        — unique identifier
├── name:        string
├── description: string
├── attributes:  Attribute[]   — defines the shape of variants
├── brand:       Brand | null
├── variants:    Variant[]
└── photo:       string | null — base64 data URL, e.g. "data:image/jpeg;base64,..."
```

```js
new Product(id, name, description, attributes, brand, variants, photo = null)
product.toJson()          // → { id, name, description, attributes, brand, variants, photo }
Product.fromJson(data)    // → Product  (recursively restores nested objects)
```

**Editing name/brand/description/photo** preserves `attributes` and `variants` unchanged.  
**Deleting an attribute** does not automatically clean up variants that reference it — variants will show `?` for the missing attribute in the UI.  
**Photo** is stored as a base64 data URL. Selecting a file in the product form reads it with `FileReader.readAsDataURL` and stores it in a hidden input. It is passed through `toJson` and persisted in the `photo` column of the SQLite `products` table.

---

## Serialization Contract

Every class implements `toJson()` and `static fromJson(data)`.

- `toJson()` returns a plain JS object safe to `JSON.stringify`.
- `fromJson(data)` reconstructs the full class instance, recursively calling `fromJson` on nested classes.
- Container classes (Product) call their children's `fromJson` — callers never need to know the nesting depth.

```js
// Full round-trip example
const json = product.toJson();
const restored = Product.fromJson(json);
```

---

## Ownership Rules

```
App state
└── products[]
    ├── brand             (copy — editing brand entity won't update product cards)
    ├── photo             (base64 string | null — owned by product)
    ├── attributes[]      (owned — not shared across products)
    │   └── values[]
    └── variants[]
        ├── implementations[]
        │   ├── attributeId  (references Attribute.id on the same product)
        │   └── value
        └── historical_stocks[]
            ├── id
            ├── quantity
            ├── date
            └── cost_unit_price
        └── oferta  (number | null)
```

Brands are stored by copy inside each product. If a brand is renamed in the Brands tab, existing product cards still show the old name until the product is re-saved.
