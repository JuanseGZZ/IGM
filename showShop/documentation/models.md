# Models

The shop uses the same domain classes as the admin. All classes are defined in `models.js` and are a direct copy of `short_products_manager/models.js`. Only `fromJson` is used at runtime — the shop never mutates or creates entities.

---

## Brand

```
Brand
├── id:   string
└── name: string
```

---

## Attribute

```
Attribute
├── id:     string
├── key:    string     — label shown to the visitor, e.g. "Color", "Talle"
└── values: string[]   — possible options for this attribute
```

---

## AttributeImplementation

A specific (attribute, value) pair selected for a variant.

```
AttributeImplementation
├── attributeId: string   — matches Attribute.id on the same product
└── value:       string   — one of Attribute.values
```

---

## Stock

A stock entry. The shop uses `historical_stocks` only to compute total stock (sum of quantities). Cost information is not displayed to visitors.

```
Stock
├── id:              string
├── quantity:        number
├── date:            string
└── cost_unit_price: number
```

---

## Variant

```
Variant
├── id:                string
├── price:             number                     — unit sale price shown to visitor
├── implementations:   AttributeImplementation[]  — the combination that defines this variant
├── historical_stocks: Stock[]                    — used to compute total available stock
└── oferta:            number | null              — discount fraction 0–1 (e.g. 0.15 = 15% off), null = no offer
```

The discounted price = `price * (1 - oferta)`. `oferta` is set by the admin; the shop reads it and can display the discount badge.

The visitor-facing stock level = `variant.historical_stocks.reduce((s, e) => s + e.quantity, 0)`. Currently the shop does not display stock level, but the data is available.

---

## Product

```
Product
├── id:          string
├── name:        string
├── description: string
├── photo:       string | null   — base64 data URL; shown as card image and modal hero
├── brand:       Brand | null
├── attributes:  Attribute[]
└── variants:    Variant[]
```

Price range displayed on the card is derived from `variants.map(v => v.price)`.
