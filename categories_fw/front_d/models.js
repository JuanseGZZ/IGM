// Buenas practicas locales:
// text y number son siempre de producto
// boolean es siempre de variante
// enum puede ser de producto o de variante: si es de producto se muestra como info, si es de variante se muestra como opcion para elegir.

const DataTypes = ["text", "number", "boolean", "enum"];

// ─── Attribute ────────────────────────────────────────────────────────────────

class Attribute {
  constructor({ key, name, data_type, id = null, is_static = false } = {}) {
    this.id = id;
    this.key = key;
    this.name = name;
    this.data_type = data_type;
    this.is_static = is_static;
    this.enum_values = [];
  }

  add_enum_value(value) {
    if (this.data_type !== "enum") {
      throw new Error("El atributo no es de tipo enum.");
    }
    if (this.enum_values.includes(value)) {
      throw new Error("El valor ya existe en la lista de valores posibles.");
    }
    this.enum_values.push(value);
  }

  check_value(value) {
    if (this.data_type === "text") return typeof value === "string";
    if (this.data_type === "number") return typeof value === "number";
    if (this.data_type === "boolean") return typeof value === "boolean";
    if (this.data_type === "enum") return this.enum_values.includes(value);
    throw new Error("Tipo de dato no reconocido.");
  }

  // Igualdad por id cuando está asignado, por identidad de objeto si no.
  equals(other) {
    if (!(other instanceof Attribute)) return false;
    if (this.id !== null && other.id !== null) return this.id === other.id;
    return this === other;
  }

  to_json() {
    return {
      id: this.id,
      key: this.key,
      name: this.name,
      data_type: this.data_type,
      is_static: this.is_static,
      enum_values: this.enum_values.map((ev) =>
        ev && typeof ev.to_json === "function" ? ev.to_json() : ev
      ),
    };
  }

  static from_json(data) {
    const attr = new Attribute({
      key: data.key,
      name: data.name,
      data_type: data.data_type,
      id: data.id ?? null,
      is_static: data.is_static ?? false,
    });
    for (const ev of data.enum_values ?? []) {
      attr.enum_values.push(ev);
    }
    return attr;
  }
}

// ─── AttributeFactory ─────────────────────────────────────────────────────────

class AttributeFactory {
  static _instances = {};

  static get(key, name, data_type, id = null, is_static = false) {
    if (!(key in this._instances)) {
      this._instances[key] = new Attribute({ key, name, data_type, id, is_static });
    }
    return this._instances[key];
  }

  static clear() {
    this._instances = {};
  }
}

// ─── AttributeImplementation ──────────────────────────────────────────────────

class AttributeImplementation {
  constructor({ attribute, value, id = null } = {}) {
    this.id = id;
    this.attribute = attribute;
    this.value = value;
  }

  to_json() {
    return {
      id: this.id,
      attribute: this.attribute ? this.attribute.to_json() : null,
      value: this.value,
    };
  }

  static from_json(data) {
    const attribute_data = data.attribute;
    const attribute =
      attribute_data && typeof attribute_data === "object"
        ? Attribute.from_json(attribute_data)
        : attribute_data;

    return new AttributeImplementation({
      attribute,
      value: data.value,
      id: data.id ?? null,
    });
  }
}

// ─── Category ─────────────────────────────────────────────────────────────────

class Category {
  constructor({
    name,
    id = null,
    attributes = [],
    subcategories = [],
    father_categorie = null,
    products = [],
  } = {}) {
    this.id = id;
    this.name = name;
    this.attributes = [...attributes];
    this._attribute_keys = new Set(this.attributes.map((a) => a.key));
    this.subcategories = [...subcategories];
    this.father_categorie = father_categorie ?? null;
    this.products = [...products];
    this._product_codes = new Set(this.products.map((p) => p.code));
  }

  _check_no_cycle(candidate_child) {
    let node = this;
    while (node !== null) {
      if (node === candidate_child) {
        throw new Error(
          `Ciclo detectado: '${candidate_child.name}' ya es ancestro de '${this.name}'.`
        );
      }
      node = node.father_categorie;
    }
  }

  _check_exclusive_children(adding) {
    if (adding === "subcategory" && this.products.length > 0) {
      throw new Error(`'${this.name}' ya tiene productos, no puede tener subcategorias.`);
    }
    if (adding === "product" && this.subcategories.length > 0) {
      throw new Error(`'${this.name}' ya tiene subcategorias, no puede tener productos.`);
    }
  }

  // Predicados de consulta (sin throw, sin mutación) — para que el Gestor
  // pueda preguntar antes de actuar sin necesidad de capturar excepciones.
  can_add_subcategory() {
    if (this.products.length > 0)
      return `"${this.name}" ya tiene productos, no puede tener subcategorías.`;
    return null;
  }

  can_add_product() {
    if (this.subcategories.length > 0)
      return `"${this.name}" ya tiene subcategorías, no puede tener productos.`;
    return null;
  }

  add_subcategory(cat) {
    this._check_exclusive_children("subcategory");
    this._check_no_cycle(cat);
    this.subcategories.push(cat);
    cat.father_categorie = this;
  }

  add_product(product) {
    this._check_exclusive_children("product");
    this.products.push(product);
    this._product_codes.add(product.code);
  }

  set_father(father) {
    if (father !== null) {
      father._check_no_cycle(this);
    }
    this.father_categorie = father;
  }

  get_ancestor_attrs() {
    const attrs = new AttributeSet();
    let current = this.father_categorie;
    while (current !== null) {
      for (const a of current.attributes) attrs.add(a);
      current = current.father_categorie;
    }
    return attrs;
  }

  get_effective_inherited_attrs() {
    const ancestor = this.get_ancestor_attrs();
    const own = new AttributeSet(this.attributes);
    return ancestor.difference(own);
  }

  get_full_attr_set() {
    const ancestor = this.get_ancestor_attrs();
    for (const a of this.attributes) ancestor.add(a);
    return ancestor;
  }

  impact_on_add_father(new_father) {
    new_father._check_no_cycle(this);
    const new_inherited = new_father.get_ancestor_attrs();
    for (const a of new_father.attributes) new_inherited.add(a);
    const own = new AttributeSet(this.attributes);
    return this.compute_impact(new_inherited.difference(own));
  }

  impact_on_remove_father() {
    return this.compute_impact(this.get_effective_inherited_attrs());
  }

  impact_on_change_father(new_father) {
    new_father._check_no_cycle(this);
    return [this.impact_on_remove_father(), this.impact_on_add_father(new_father)];
  }

  impact_on_add_attribute(attr) {
    return this.compute_impact(new AttributeSet([attr]));
  }

  impact_on_remove_attribute(attr) {
    return this.compute_impact(new AttributeSet([attr]));
  }

  compute_impact(attrs) {
    if (attrs.size === 0) return [];
    return this._descend_impact(attrs.clone());
  }

  _descend_impact(attrs) {
    if (this.products.length > 0) {
      return [[attrs, [...this.products]]];
    }
    const results = [];
    for (const sub of this.subcategories) {
      const sub_own = new AttributeSet(sub.attributes);
      const sub_remaining = attrs.difference(sub_own);
      if (sub_remaining.size > 0) {
        results.push(...sub._descend_impact(sub_remaining));
      }
    }
    return results;
  }
}

// ─── Variant ──────────────────────────────────────────────────────────────────

class Variant {
  constructor({ attribute_implementations = [], id = null } = {}) {
    this.id = id;
    this.attribute_implementations = [...attribute_implementations];
  }

  to_json() {
    return {
      id: this.id,
      attribute_implementations: this.attribute_implementations.map((ai) =>
        ai && typeof ai.to_json === "function" ? ai.to_json() : ai
      ),
    };
  }

  static from_json(data) {
    const attribute_implementations = (data.attribute_implementations ?? []).map((ai) =>
      typeof ai === "object" ? AttributeImplementation.from_json(ai) : ai
    );
    return new Variant({ attribute_implementations, id: data.id ?? null });
  }
}

// ─── Product ──────────────────────────────────────────────────────────────────

class Product {
  constructor({
    code,
    title,
    price,
    description,
    brand,
    id = null,
    category = null,
    attributes_implementations = [],
    variants = [],
  } = {}) {
    if (category === null) throw new Error("Product must have a category");

    this.id = id;
    this.code = code;
    this.title = title;
    this.price = price;
    this.description = description;
    this.brand = brand;
    this.category = category;
    this.attributes_implementations = [...attributes_implementations];
    this._impl_keys = new Set(this.attributes_implementations.map((i) => i.attribute.key));
    this.variants = [...variants];
  }

  _current_static_attrs() {
    return new AttributeSet(
      this.attributes_implementations
        .filter((impl) => impl.attribute.is_static)
        .map((impl) => impl.attribute)
    );
  }

  _current_dynamic_attrs() {
    return new AttributeSet(
      this.attributes_implementations
        .filter((impl) => !impl.attribute.is_static)
        .map((impl) => impl.attribute)
    );
  }

  impact_on_change_category(new_category) {
    const current_static = this._current_static_attrs();
    const new_required = new AttributeSet(
      [...new_category.get_full_attr_set().values()].filter((a) => a.is_static)
    );
    return [new_required.difference(current_static), current_static.difference(new_required)];
  }

  get_required_dynamic_attrs() {
    return new AttributeSet(
      [...this.category.get_full_attr_set().values()].filter((a) => !a.is_static)
    );
  }

  _variant_signature(variant) {
    return variant.attribute_implementations
      .map((impl) => `${impl.attribute.key}:${impl.value}`)
      .sort()
      .join("|");
  }

  _check_variant_completeness(variant) {
    const required = this.get_required_dynamic_attrs();
    const implemented = new AttributeSet(
      variant.attribute_implementations.map((impl) => impl.attribute)
    );
    const missing = required.difference(implemented);
    const extra = implemented.difference(required);
    const errors = [];
    if (missing.size > 0) {
      errors.push(`faltan: ${[...missing.values()].map((a) => a.key).sort()}`);
    }
    if (extra.size > 0) {
      errors.push(`de mas: ${[...extra.values()].map((a) => a.key).sort()}`);
    }
    if (errors.length > 0) {
      throw new Error(`Variante invalida — ${errors.join(", ")}`);
    }
  }

  _check_variant_uniqueness(variant) {
    const new_sig = this._variant_signature(variant);
    for (const existing of this.variants) {
      if (this._variant_signature(existing) === new_sig) {
        throw new Error("Ya existe una variante con la misma combinacion de valores.");
      }
    }
  }

  add_variant(variant) {
    this._check_variant_completeness(variant);
    this._check_variant_uniqueness(variant);
    this.variants.push(variant);
  }

  remove_variant(variant) {
    const idx = this.variants.indexOf(variant);
    if (idx === -1) throw new Error("La variante no pertenece a este producto.");
    this.variants.splice(idx, 1);
  }
}

// ─── AttributeSet ─────────────────────────────────────────────────────────────
// Set de Attribute con igualdad semantica (por id cuando existe, por referencia si no).

class AttributeSet {
  constructor(iterable = []) {
    this._map = new Map();
    for (const attr of iterable) this.add(attr);
  }

  _keyFor(attr) {
    if (attr.id !== null) return `id:${attr.id}`;
    return `key:${attr.key}`;
  }

  add(attr) {
    this._map.set(this._keyFor(attr), attr);
  }

  has(attr) {
    return this._map.has(this._keyFor(attr));
  }

  get size() { return this._map.size; }

  values() { return this._map.values(); }

  difference(other) {
    const result = new AttributeSet();
    for (const attr of this._map.values()) {
      if (!other.has(attr)) result.add(attr);
    }
    return result;
  }

  clone() {
    return new AttributeSet(this._map.values());
  }
}

export {
  DataTypes,
  Attribute,
  AttributeFactory,
  AttributeImplementation,
  AttributeSet,
  Category,
  Variant,
  Product,
};
