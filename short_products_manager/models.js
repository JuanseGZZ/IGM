function genId() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

class Brand {
    constructor(id, name) {
        this.id = id;
        this.name = name;
    }
    toJson() {
        return { id: this.id, name: this.name };
    }
    static fromJson(d) {
        return new Brand(d.id, d.name);
    }
}

class Attribute {
    // key: string label, values: string[] (possible options for variants)
    constructor(id, key, values) {
        this.id = id;
        this.key = key;
        this.values = values;
    }
    toJson() {
        return { id: this.id, key: this.key, values: [...this.values] };
    }
    static fromJson(d) {
        return new Attribute(d.id, d.key, [...(d.values || [])]);
    }
}

class AttributeImplementation {
    // A specific attribute + chosen value, used inside a Variant
    constructor(attributeId, value) {
        this.attributeId = attributeId;
        this.value = value;
    }
    toJson() {
        return { attributeId: this.attributeId, value: this.value };
    }
    static fromJson(d) {
        return new AttributeImplementation(d.attributeId, d.value);
    }
}

class Stock {
    constructor(id, quantity, date, cost_unit_price) {
        this.id             = id;
        this.quantity       = quantity;
        this.date           = date;
        this.cost_unit_price = cost_unit_price;
    }
    toJson() {
        return {
            id:              this.id,
            quantity:        this.quantity,
            date:            this.date,
            cost_unit_price: this.cost_unit_price
        };
    }
    static fromJson(d) {
        return new Stock(d.id, d.quantity, d.date, d.cost_unit_price ?? 0);
    }
}

class Variant {
    constructor(id, price, implementations, historical_stocks = [], oferta = null) {
        this.id               = id;
        this.price            = price;
        this.implementations  = implementations;   // AttributeImplementation[]
        this.historical_stocks = historical_stocks; // Stock[]
        this.oferta           = oferta;             // number 0–1 (discount fraction) | null
    }
    toJson() {
        return {
            id:               this.id,
            price:            this.price,
            implementations:  this.implementations.map(i => i.toJson()),
            historical_stocks: this.historical_stocks.map(s => s.toJson()),
            oferta:           this.oferta
        };
    }
    static fromJson(d) {
        return new Variant(
            d.id,
            d.price,
            (d.implementations   || []).map(AttributeImplementation.fromJson),
            (d.historical_stocks || []).map(Stock.fromJson),
            d.oferta ?? null
        );
    }
}

class Product {
    constructor(id, name, description, attributes, brand, variants, photo = null) {
        this.id          = id;
        this.name        = name;
        this.description = description;
        this.attributes  = attributes; // Attribute[]
        this.brand       = brand;      // Brand | null
        this.variants    = variants;   // Variant[]
        this.photo       = photo;      // base64 data URL | null
    }
    toJson() {
        return {
            id:          this.id,
            name:        this.name,
            description: this.description,
            attributes:  this.attributes.map(a => a.toJson()),
            brand:       this.brand ? this.brand.toJson() : null,
            variants:    this.variants.map(v => v.toJson()),
            photo:       this.photo
        };
    }
    static fromJson(d) {
        return new Product(
            d.id,
            d.name,
            d.description,
            (d.attributes || []).map(Attribute.fromJson),
            d.brand ? Brand.fromJson(d.brand) : null,
            (d.variants  || []).map(Variant.fromJson),
            d.photo ?? null
        );
    }
}
