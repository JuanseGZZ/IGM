# Models

## Index
- [genId](#genid)
- [Brand](#brand)
- [Attribute](#attribute)
- [AttributeImplementation](#attributeimplementation)
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

## Variant

A unique combination of one value per attribute, with a price.

```
Variant
├── id:              string                     — unique identifier
├── price:           number                     — unit price
└── implementations: AttributeImplementation[]  — one entry per product attribute
```

```js
new Variant(id, price, implementations)
variant.toJson()          // → { id, price, implementations: [...] }
Variant.fromJson(data)    // → Variant
```

**Uniqueness rule:** Two variants are equal if every `AttributeImplementation` pair matches (same `attributeId` and same `value`). The UI enforces this on add and on edit (excluding self).

**Completeness rule:** A valid variant has exactly one `AttributeImplementation` per product attribute. The form enforces this with required selects.

---

## Product

The root aggregate. Owns all attributes, variants, and a brand reference.

```
Product
├── id:          string        — unique identifier
├── name:        string
├── description: string
├── attributes:  Attribute[]   — defines the shape of variants
├── brand:       Brand | null
└── variants:    Variant[]
```

```js
new Product(id, name, description, attributes, brand, variants)
product.toJson()          // → { id, name, description, attributes, brand, variants }
Product.fromJson(data)    // → Product  (recursively restores nested objects)
```

**Editing name/brand/description** preserves `attributes` and `variants` unchanged.  
**Deleting an attribute** does not automatically clean up variants that reference it — variants will show `?` for the missing attribute in the UI.

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
    ├── brand            (copy — editing brand entity won't update product cards)
    ├── attributes[]     (owned — not shared across products)
    │   └── values[]
    └── variants[]
        └── implementations[]
            ├── attributeId  (references Attribute.id on the same product)
            └── value
```

Brands are stored by copy inside each product. If a brand is renamed in the Brands tab, existing product cards still show the old name until the product is re-saved.
