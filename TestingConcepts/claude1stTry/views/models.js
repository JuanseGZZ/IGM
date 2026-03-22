class Attribute {
  constructor({ id, key, name, data_type, is_static, enum_values = [] }) {
    this.id = id;
    this.key = key;
    this.name = name;
    this.data_type = data_type;
    this.is_static = is_static;
    this.enum_values = enum_values;
  }
}

class Category {
  constructor({ id, name, attributes = [] }) {
    this.id = id;
    this.name = name;
    this.attributes = attributes.map(a => new Attribute(a));
  }
}

class Implementation {
  constructor({ id, attribute, value }) {
    this.id = id;
    this.attribute = new Attribute(attribute);
    this.value = value;
  }
}

class Variant {
  constructor({ id, attribute_implementations = [] }) {
    this.id = id;
    this.attribute_implementations = attribute_implementations.map(i => new Implementation(i));
  }
}

class Product {
  constructor({ id, code, title, price, description, brand, category, attributes = [], attributes_implementations = [], variants = [] }) {
    this.id = id;
    this.code = code;
    this.title = title;
    this.price = price;
    this.description = description;
    this.brand = brand;
    this.category = new Category(category);
    this.attributes = attributes.map(a => new Attribute(a));
    this.attributes_implementations = attributes_implementations.map(i => new Implementation(i));
    this.variants = variants.map(v => new Variant(v));
  }
}

class ProductSummary {
  constructor({ id, code, title, price, brand, category_id, category_name, variant_count }) {
    this.id = id;
    this.code = code;
    this.title = title;
    this.price = price;
    this.brand = brand;
    this.category_id = category_id;
    this.category_name = category_name;
    this.variant_count = variant_count;
  }
}