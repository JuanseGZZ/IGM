// models.js — mirror de app/models.py
// Misma lógica de negocio, mismas validaciones, mismo comportamiento.
// Los DTOs en interfaceModels/ son para comunicación con la API.
// Este archivo es el modelo vivo para validar en el front antes de mandar al back.

export const DataTypes = ["text", "number", "boolean", "enum"];

// ─── Attribute ────────────────────────────────────────────────────────────────

export class Attribute {
  constructor({ key, name, data_type, id = null, is_static = false }) {
    this.id          = id;
    this.key         = key;
    this.name        = name;
    this.data_type   = data_type;
    this.is_static   = is_static;
    this.enum_values = [];
  }

  addEnumValue(value) {
    if (this.data_type !== "enum") throw new Error("El atributo no es de tipo enum.");
    if (!this.enum_values.includes(value)) {
      this.enum_values.push(value);
    } else {
      throw new Error("El valor ya existe en la lista de valores posibles.");
    }
  }

  checkValue(value) {
    if (this.data_type === "text")    return typeof value === "string";
    if (this.data_type === "number")  return typeof value === "number";
    if (this.data_type === "boolean") return typeof value === "boolean";
    if (this.data_type === "enum")    return this.enum_values.includes(value);
    throw new Error("Tipo de dato no reconocido.");
  }

  toJSON() {
    return {
      id:          this.id,
      key:         this.key,
      name:        this.name,
      data_type:   this.data_type,
      is_static:   this.is_static,
      enum_values: this.enum_values.map(ev => ev?.toJSON ? ev.toJSON() : ev),
    };
  }

  static fromJSON(data) {
    if (!data) return null;
    const attr = new Attribute({
      key:       data.key,
      name:      data.name,
      data_type: data.data_type,
      id:        data.id        ?? null,
      is_static: data.is_static ?? false,
    });
    for (const ev of (data.enum_values ?? [])) attr.enum_values.push(ev);
    return attr;
  }
}

// ─── AttributeFactory ─────────────────────────────────────────────────────────

export class AttributeFactory {
  static _instances = {};

  static get(key, name, data_type, id = null, is_static = false) {
    if (!(key in this._instances)) {
      this._instances[key] = new Attribute({ key, name, data_type, id, is_static });
    }
    return this._instances[key];
  }

  static clear() { this._instances = {}; }
}

// ─── AttributeImplementation ──────────────────────────────────────────────────

export class AttributeImplementation {
  constructor({ attribute, value, id = null }) {
    this.id        = id;
    this.attribute = attribute;
    this.value     = value;
  }

  toJSON() {
    return {
      id:        this.id,
      attribute: this.attribute?.toJSON() ?? null,
      value:     this.value,
    };
  }

  static fromJSON(data) {
    if (!data) return null;
    const attrData  = data.attribute;
    const attribute = attrData && typeof attrData === "object"
      ? Attribute.fromJSON(attrData)
      : attrData;
    return new AttributeImplementation({ attribute, value: data.value, id: data.id ?? null });
  }
}

// ─── Category ─────────────────────────────────────────────────────────────────

export class Category {
  constructor({
    name,
    id             = null,
    attributes     = null,
    subcategories  = null,
    father_categorie = null,
    products       = null,
  }) {
    this.id               = id;
    this.name             = name;
    this.attributes       = attributes    ?? [];
    this._attribute_keys  = new Set(this.attributes.map(a => a.key));
    this.subcategories    = subcategories ?? [];
    this.father_categorie = father_categorie ?? null;
    this.products         = products      ?? [];
    this._product_codes   = new Set(this.products.map(p => p.code));
  }

  // ── getters recursivos ────────────────────────────────────────────────────

  getAttributes() {
    const attrs = [...this.attributes];
    if (this.father_categorie) attrs.push(...this.father_categorie.getAttributes());
    return attrs;
  }

  getAttributeKeys() {
    const keys = new Set(this.attributes.map(a => a.key));
    if (this.father_categorie) {
      for (const k of this.father_categorie.getAttributeKeys()) keys.add(k);
    }
    return keys;
  }

  // ── lookup helpers para add_attribute ─────────────────────────────────────

  _addAttributeLookUp(attribute) {
    if (this._attribute_keys.has(attribute.key)) return true;
    if (!this.father_categorie) return false;
    return this.father_categorie._addAttributeLookUp(attribute);
  }

  _addAttributeLookDown(attribute) {
    if (this._attribute_keys.has(attribute.key)) return [];
    if (this.subcategories.length > 0) {
      return this.subcategories.flatMap(c => c._addAttributeLookDown(attribute));
    }
    if (this.products.length > 0) return [...this.products];
    return [];
  }

  _addAttributeProductCheckFamilyImpact(attribute) {
    if (this._addAttributeLookUp(attribute)) return null;
    return this._addAttributeLookDown(attribute).filter(p => !p.isAttributeIn(attribute));
  }

  // ── add_dinamic_attribute ─────────────────────────────────────────────────

  // product_variant_implementations : [{ product_id, variants: [{ variant_id, value }] }]
  _addAttributeVariantImpactCheck(attribute, product_variant_implementations) {
    let impact = this._addAttributeProductCheckFamilyImpact(attribute);
    if (impact === null) return null;

    impact = impact.filter(p => p.variants.length > 0);

    if (impact.length === 0) {
      if (!this._attribute_keys.has(attribute.key)) {
        this.attributes.push(attribute);
        this._attribute_keys.add(attribute.key);
      }
      return {};
    }

    const impactProductIds = new Set(impact.map(p => p.id));
    const implProductIds   = new Set();
    for (const entry of product_variant_implementations) {
      if (implProductIds.has(entry.product_id)) return impact;
      implProductIds.add(entry.product_id);
    }
    if (!_setsEqual(impactProductIds, implProductIds)) return impact;

    const impactMap = Object.fromEntries(impact.map(p => [p.id, p]));
    const pending   = [];

    for (const entry of product_variant_implementations) {
      const product         = impactMap[entry.product_id];
      const productVarIds   = new Set(product.variants.map(v => v.id));
      const variantsMap     = Object.fromEntries(product.variants.map(v => [v.id, v]));

      const entryVarIds = new Set();
      for (const vEntry of entry.variants) {
        if (entryVarIds.has(vEntry.variant_id)) return impact;
        entryVarIds.add(vEntry.variant_id);
      }
      if (!_setsEqual(productVarIds, entryVarIds)) return impact;

      for (const vEntry of entry.variants) {
        try { if (!attribute.checkValue(vEntry.value)) return impact; } catch { return impact; }
        pending.push([variantsMap[vEntry.variant_id], new AttributeImplementation({ attribute, value: vEntry.value })]);
      }
    }
    return pending;
  }

  addDinamicAttribute(attribute, product_variant_implementations) {
    if (attribute.is_static) throw new Error("El attributo que se quiere incertar es estatico");

    const pending = this._addAttributeVariantImpactCheck(attribute, product_variant_implementations);
    if (pending === null || (!Array.isArray(pending) && typeof pending === "object")) return {};
    if (pending.length > 0 && pending[0] instanceof Product) return pending;

    for (const [variant, impl] of pending) variant.attribute_implementations.push(impl);
    this.attributes.push(attribute);
    this._attribute_keys.add(attribute.key);
    return {};
  }

  // ── add_static_attribute ──────────────────────────────────────────────────

  // implementations : [{ product_id, value }]
  _addStaticImpactCheck(attribute, implementations) {
    let impact = this._addAttributeProductCheckFamilyImpact(attribute);
    if (impact === null) return null;

    if (impact.length === 0) {
      if (!this._attribute_keys.has(attribute.key)) {
        this.attributes.push(attribute);
        this._attribute_keys.add(attribute.key);
      }
      return {};
    }

    const impactProductIds = new Set(impact.map(p => p.id));
    const implProductIds   = new Set();
    for (const entry of implementations) {
      if (implProductIds.has(entry.product_id)) return impact;
      implProductIds.add(entry.product_id);
    }
    if (!_setsEqual(impactProductIds, implProductIds)) return impact;

    const impactMap = Object.fromEntries(impact.map(p => [p.id, p]));
    const pending   = [];

    for (const entry of implementations) {
      try { if (!attribute.checkValue(entry.value)) return impact; } catch { return impact; }
      pending.push([impactMap[entry.product_id], new AttributeImplementation({ attribute, value: entry.value })]);
    }
    return pending;
  }

  addStaticAttribute(attribute, implementations) {
    if (!attribute.is_static) throw new Error("El atributo que se quiere insertar no es estatico");

    const pending = this._addStaticImpactCheck(attribute, implementations);
    if (pending === null || (!Array.isArray(pending) && typeof pending === "object")) return {};
    if (pending.length > 0 && pending[0] instanceof Product) return pending;

    for (const [product, impl] of pending) {
      product.attributes_implementations.push(impl);
      product._impl_keys.add(impl.attribute.key);
    }
    this.attributes.push(attribute);
    this._attribute_keys.add(attribute.key);
    return {};
  }

  // ── del_attribute ─────────────────────────────────────────────────────────

  static _delAttributeLookUp(category, attribute) {
    if (category._attribute_keys.has(attribute.key)) return true;
    if (!category.father_categorie) return false;
    return Category._delAttributeLookUp(category.father_categorie, attribute);
  }

  static _delAttributeLookDown(category, attribute) {
    if (category._attribute_keys.has(attribute.key)) return [];
    if (category.subcategories.length > 0) {
      return category.subcategories.flatMap(c => Category._delAttributeLookDown(c, attribute));
    }
    if (category.products.length > 0) {
      return category.products.filter(p => !p._attribute_keys.has(attribute.key));
    }
    return [];
  }

  delAttributeCheckFamilyImpact(attribute) {
    const products = [];
    if (this.father_categorie && Category._delAttributeLookUp(this.father_categorie, attribute)) return products;
    if (this.products.length > 0) {
      return this.products.filter(p => !p._attribute_keys.has(attribute.key));
    }
    for (const c of this.subcategories) products.push(...Category._delAttributeLookDown(c, attribute));
    return products;
  }

  // delete_opt: 0=solo avisa, 1=elimina implementaciones, 2=inyecta attr en productos
  delAttribute(attribute, delete_opt = 0) {
    const products = [...this.delAttributeCheckFamilyImpact(attribute)];

    if (products.length === 0) {
      this._attribute_keys.delete(attribute.key);
      this.attributes = this.attributes.filter(a => a.key !== attribute.key);
      return [];
    }

    if (delete_opt === 0) return products;

    if (delete_opt === 1) {
      for (const p of products) {
        if (attribute.is_static) {
          p.attributes_implementations = p.attributes_implementations.filter(i => i.attribute.key !== attribute.key);
          p._impl_keys.delete(attribute.key);
        } else {
          for (const v of p.variants) {
            v.attribute_implementations = v.attribute_implementations.filter(i => i.attribute.key !== attribute.key);
          }
        }
      }
      this._attribute_keys.delete(attribute.key);
      this.attributes = this.attributes.filter(a => a.key !== attribute.key);
      return [];
    }

    if (delete_opt === 2) {
      for (const p of products) {
        p.attributes.push(attribute);
        p._attribute_keys.add(attribute.key);
      }
      this._attribute_keys.delete(attribute.key);
      this.attributes = this.attributes.filter(a => a.key !== attribute.key);
      return [];
    }
  }

  // ── change_categorie_father ───────────────────────────────────────────────

  static changeLookupForAttributes(initCategorie) {
    const attrs = new Set(initCategorie.attributes);
    if (initCategorie.father_categorie) {
      for (const a of Category.changeLookupForAttributes(initCategorie.father_categorie)) attrs.add(a);
    }
    return attrs;
  }

  // del_option: 0=retorna huerfanos si hay impacto, 1=inyecta huerfanos en self, 2=elimina impls huerfanas
  // implementations: { attr_key: [[product_id, value], ...] } para estáticos
  //                  { attr_key: [[product_id, [{variant_id, value},...]], ...] } para dinámicos
  changeCategorieFather(father_categorie, implementations, del_option = 0) {
    let cursor = father_categorie;
    while (cursor !== null) {
      if (cursor === this) throw new Error("No se puede asignar un descendiente como padre: se formaría un ciclo.");
      cursor = cursor.father_categorie;
    }
    if (father_categorie.products.length > 0) throw new Error("No puede tener productos si quiere poner categorias");

    const fatherAttrs    = Category.changeLookupForAttributes(father_categorie);
    const fatherAttrKeys = new Set([...fatherAttrs].map(a => a.key));

    let oldOrphanAttrs = [];
    if (this.father_categorie) {
      const oldAttrs = Category.changeLookupForAttributes(this.father_categorie);
      oldOrphanAttrs = [...oldAttrs].filter(a => !fatherAttrKeys.has(a.key) && !this._attribute_keys.has(a.key));
    }

    const orphanImpact = {};
    for (const attr of oldOrphanAttrs) {
      const affected = this._addAttributeLookDown(attr).filter(p => p._impl_keys.has(attr.key));
      if (affected.length > 0) orphanImpact[attr.key] = { attr, affected };
    }

    if (del_option === 0 && Object.keys(orphanImpact).length > 0) return orphanImpact;

    const staticImpactMap  = {};
    const dynamicImpactMap = {};
    for (const attr of fatherAttrs) {
      const impacted = this._addAttributeLookDown(attr).filter(p => !p.isAttributeIn(attr));
      if (!impacted.length) continue;
      if (attr.is_static) {
        staticImpactMap[attr.key] = { attr, impacted };
      } else {
        dynamicImpactMap[attr.key] = {
          attr,
          entries: impacted.map(product => ({
            product,
            variant_slots: product.variants.map(v => ({ variant_id: v.id, value: null })),
          })),
        };
      }
    }

    const impactMap = { ...staticImpactMap, ...dynamicImpactMap };
    const hasImpact = Object.keys(staticImpactMap).length > 0 || Object.keys(dynamicImpactMap).length > 0;

    if (hasImpact) {
      // validar estáticos
      for (const [attrKey, { attr, impacted }] of Object.entries(staticImpactMap)) {
        const implEntries = implementations[attrKey];
        if (!implEntries) return impactMap;
        const implMap = Object.fromEntries(implEntries.map(([pid, v]) => [pid, v]));
        for (const product of impacted) {
          const val = implMap[product.id];
          if (val === undefined || val === null) return impactMap;
          try { if (!attr.checkValue(val)) return impactMap; } catch { return impactMap; }
        }
      }
      // validar dinámicos
      for (const [attrKey, { attr, entries }] of Object.entries(dynamicImpactMap)) {
        const implEntries = implementations[attrKey];
        if (!implEntries) return impactMap;
        const implProdMap = Object.fromEntries(implEntries.map(([pid, variants]) => [pid, variants]));
        for (const { product, variant_slots } of entries) {
          const implVariants = implProdMap[product.id];
          if (!implVariants) return impactMap;
          const implVarMap = Object.fromEntries(implVariants.map(v => [v.variant_id, v.value]));
          for (const slot of variant_slots) {
            const val = implVarMap[slot.variant_id];
            if (val === undefined || val === null) return impactMap;
            try { if (!attr.checkValue(val)) return impactMap; } catch { return impactMap; }
          }
        }
      }

      // aplicar estáticos
      for (const [attrKey, { attr, impacted }] of Object.entries(staticImpactMap)) {
        const implMap = Object.fromEntries(implementations[attrKey].map(([pid, v]) => [pid, v]));
        for (const product of impacted) {
          const impl = new AttributeImplementation({ attribute: attr, value: implMap[product.id] });
          product.attributes_implementations.push(impl);
          product._impl_keys.add(attr.key);
        }
      }
      // aplicar dinámicos
      const pendingVars = [];
      for (const [attrKey, { attr, entries }] of Object.entries(dynamicImpactMap)) {
        const implProdMap  = Object.fromEntries(implementations[attrKey].map(([pid, variants]) => [pid, variants]));
        for (const { product, variant_slots } of entries) {
          const implVarMap  = Object.fromEntries(implProdMap[product.id].map(v => [v.variant_id, v.value]));
          const variantsMap = Object.fromEntries(product.variants.map(v => [v.id, v]));
          for (const slot of variant_slots) {
            pendingVars.push([variantsMap[slot.variant_id], new AttributeImplementation({ attribute: attr, value: implVarMap[slot.variant_id] })]);
          }
        }
      }
      for (const [variant, impl] of pendingVars) variant.attribute_implementations.push(impl);
    }

    // desvincular del padre anterior
    if (this.father_categorie) {
      this.father_categorie.subcategories = this.father_categorie.subcategories.filter(c => c !== this);
    }

    // manejar huérfanos
    if (del_option === 1) {
      for (const attr of oldOrphanAttrs) {
        if (!this._attribute_keys.has(attr.key)) {
          this.attributes.push(attr);
          this._attribute_keys.add(attr.key);
        }
      }
    } else if (del_option === 2) {
      for (const { attr, affected } of Object.values(orphanImpact)) {
        for (const product of affected) {
          if (attr.is_static) {
            product.attributes_implementations = product.attributes_implementations.filter(i => i.attribute.key !== attr.key);
            product._impl_keys.delete(attr.key);
          } else {
            for (const v of product.variants) {
              v.attribute_implementations = v.attribute_implementations.filter(i => i.attribute.key !== attr.key);
            }
          }
        }
      }
    }

    // vincular al nuevo padre
    this.father_categorie = father_categorie;
    father_categorie.subcategories.push(this);
    return {};
  }

  // ── del_categorie ─────────────────────────────────────────────────────────

  // del_option: 0=inyecta attrs sobrantes en productos, 1=elimina impls, 2=solo retorna impactados
  delCategorie(categorie, del_option) {
    if (!this.subcategories.includes(categorie)) return false;

    const parentAttrKeys = this.getAttributeKeys();
    const leftoverAttrs  = categorie.attributes.filter(a => !parentAttrKeys.has(a.key));

    if (leftoverAttrs.length === 0) {
      this.subcategories = this.subcategories.filter(c => c !== categorie);
      categorie.father_categorie = null;
      return [];
    }

    const impactMap = {};
    for (const attr of leftoverAttrs) {
      const impacted = [
        ...categorie.products.filter(p => !p._attribute_keys.has(attr.key) && p._impl_keys.has(attr.key)),
        ...categorie.subcategories.flatMap(c => Category._delAttributeLookDown(c, attr)),
      ];
      impactMap[attr.key] = { attr, impacted };
    }

    const allImpacted = {};
    for (const { impacted } of Object.values(impactMap)) {
      for (const p of impacted) allImpacted[p.code] = p;
    }

    if (Object.keys(allImpacted).length === 0) {
      this.subcategories = this.subcategories.filter(c => c !== categorie);
      categorie.father_categorie = null;
      return [];
    }

    if (del_option === 2) return Object.values(allImpacted);

    if (del_option === 1) {
      for (const { attr, impacted } of Object.values(impactMap)) {
        for (const p of impacted) {
          if (attr.is_static) {
            p.attributes_implementations = p.attributes_implementations.filter(i => i.attribute.key !== attr.key);
            p._impl_keys.delete(attr.key);
          } else {
            for (const v of p.variants) {
              v.attribute_implementations = v.attribute_implementations.filter(i => i.attribute.key !== attr.key);
            }
          }
        }
      }
    }

    if (del_option === 0) {
      for (const { attr, impacted } of Object.values(impactMap)) {
        for (const p of impacted) {
          if (!p._attribute_keys.has(attr.key)) {
            p.attributes.push(attr);
            p._attribute_keys.add(attr.key);
          }
        }
      }
    }

    this.subcategories = this.subcategories.filter(c => c !== categorie);
    categorie.father_categorie = null;
    return [];
  }

  // ── products ──────────────────────────────────────────────────────────────

  delProduct(product) {
    if (!this._product_codes.has(product.code)) return false;
    this.products = this.products.filter(p => p.code !== product.code);
    this._product_codes.delete(product.code);
    return true;
  }

  addProduct(product) {
    if (this.subcategories.length > 0) throw new Error("No puede tener categorias si quiere agregar productos");
    if (this._product_codes.has(product.code)) return false;
    this.products.push(product);
    this._product_codes.add(product.code);
    return true;
  }

  // ── serialización ─────────────────────────────────────────────────────────

  toJSON() {
    return {
      id:            this.id,
      name:          this.name,
      father:        this.father_categorie ? { id: this.father_categorie.id, name: this.father_categorie.name } : null,
      attributes:    this.attributes.map(a => a?.toJSON ? a.toJSON() : a),
      subcategories: this.subcategories.map(s => s.toJSON()),
    };
  }

  static fromJSON(data) {
    if (!data) return null;
    const attributes = (data.attributes ?? []).map(a => a && typeof a === "object" ? Attribute.fromJSON(a) : a);
    const category   = new Category({ name: data.name, id: data.id ?? null, attributes });
    for (const subData of (data.subcategories ?? [])) {
      const sub = subData && typeof subData === "object" ? Category.fromJSON(subData) : subData;
      sub.father_categorie = category;
      category.subcategories.push(sub);
    }
    return category;
  }
}

// ─── Variant ──────────────────────────────────────────────────────────────────

export class Variant {
  constructor({ attribute_implementations = null, id = null } = {}) {
    this.id                       = id;
    this.attribute_implementations = attribute_implementations ?? [];
  }

  toJSON() {
    return {
      id:                       this.id,
      attribute_implementations: this.attribute_implementations.map(ai => ai?.toJSON ? ai.toJSON() : ai),
    };
  }

  static fromJSON(data) {
    if (!data) return null;
    const impls = (data.attribute_implementations ?? []).map(ai =>
      ai && typeof ai === "object" ? AttributeImplementation.fromJSON(ai) : ai
    );
    return new Variant({ attribute_implementations: impls, id: data.id ?? null });
  }
}

// ─── Product ──────────────────────────────────────────────────────────────────

export class Product {
  constructor({
    code, title, price, description, brand,
    id                      = null,
    category                = null,
    attributes_implementations = null,
    attributes              = null,
    variants                = null,
  }) {
    if (category === null) throw new Error("Product must have a category");
    this.id                        = id;
    this.code                      = code;
    this.title                     = title;
    this.price                     = price;
    this.description               = description;
    this.brand                     = brand;
    this.category                  = category;
    this.attributes_implementations = attributes_implementations ?? [];
    this._impl_keys                = new Set(this.attributes_implementations.map(i => i.attribute.key));
    this.attributes                = attributes ?? [];
    this._attribute_keys           = new Set(this.attributes.map(a => a.key));
    this.variants                  = variants ?? [];
  }

  isAttributeIn(attribute) { return this._attribute_keys.has(attribute.key); }

  getAttributes() { return [...this.attributes, ...this.category.getAttributes()]; }

  getAttributeKeys() { return new Set([...this._attribute_keys, ...this.category.getAttributeKeys()]); }

  // ── add_dinamic_attribute ─────────────────────────────────────────────────

  // variant_options: [{ variant_id, value }]
  addDinamicAttribute(attribute, variant_options = null) {
    if (attribute.is_static) throw new Error("El attributo que se quiere incertar es estatico");

    const neededKeys = new Set([...this.getNeededAtributesImplementations()].map(a => a.key));
    if (neededKeys.has(attribute.key)) {
      this.attributes.push(attribute);
      this._attribute_keys.add(attribute.key);
      return true;
    }

    const variantOptionsId = new Set();
    const variantsId       = new Set(this.variants.map(v => v.id));
    for (const opt of variant_options) {
      if (variantOptionsId.has(opt.variant_id)) return false;
      variantOptionsId.add(opt.variant_id);
    }
    if (!_setsEqual(variantsId, variantOptionsId)) return false;

    try {
      for (const vo of variant_options) attribute.checkValue(vo.value);
    } catch (error) {
      console.log(error);
      return false;
    }

    const variantsMap = Object.fromEntries(this.variants.map(v => [v.id, v]));
    for (const opt of variant_options) {
      variantsMap[opt.variant_id].attribute_implementations.push(
        new AttributeImplementation({ attribute, value: opt.value })
      );
    }
    this.attributes.push(attribute);
    this._attribute_keys.add(attribute.key);
    return true;
  }

  // ── add_static_attribute ──────────────────────────────────────────────────

  addStaticAttribute(attribute, implementation) {
    if (!attribute.checkValue(implementation.value)) {
      throw new Error(`El valor '${implementation.value}' no es válido para el atributo '${attribute.name}'.`);
    }
    const neededKeys = new Set([...this.getNeededAtributesImplementations(true)].map(a => a.key));
    if (neededKeys.has(attribute.key)) {
      if (this._impl_keys.has(implementation.attribute.key)) throw new Error("La implementacion ya esta hecha");
      this.attributes_implementations.push(implementation);
      this._impl_keys.add(implementation.attribute.key);
      return true;
    }
    return false;
  }

  // ── del_attribute ─────────────────────────────────────────────────────────

  // delete_opt: 0=avisa impacto, 1=elimina sin importar impacto
  delAttribute(attribute, delete_opt = 0) {
    if (!this._attribute_keys.has(attribute.key)) return false;

    if (this.category.getAttributeKeys().has(attribute.key)) {
      this.attributes = this.attributes.filter(a => a.key !== attribute.key);
      this._attribute_keys.delete(attribute.key);
      return [];
    }

    const impacted = attribute.is_static
      ? this.attributes_implementations.filter(i => i.attribute.key === attribute.key)
      : this.variants.filter(v => v.attribute_implementations.some(i => i.attribute.key === attribute.key));

    if (impacted.length === 0) {
      this.attributes = this.attributes.filter(a => a.key !== attribute.key);
      this._attribute_keys.delete(attribute.key);
      return [];
    }

    if (delete_opt === 0) return impacted;

    if (attribute.is_static) {
      this.attributes_implementations = this.attributes_implementations.filter(i => i.attribute.key !== attribute.key);
      this._impl_keys.delete(attribute.key);
    } else {
      for (const v of this.variants) {
        v.attribute_implementations = v.attribute_implementations.filter(i => i.attribute.key !== attribute.key);
      }
    }
    this.attributes = this.attributes.filter(a => a.key !== attribute.key);
    this._attribute_keys.delete(attribute.key);
    return [];
  }

  // ── serialización ─────────────────────────────────────────────────────────

  toJSON() {
    return {
      id:                        this.id,
      code:                      this.code,
      title:                     this.title,
      price:                     this.price,
      description:               this.description,
      brand:                     this.brand,
      category:                  this.category?.toJSON() ?? null,
      attributes_implementations: this.attributes_implementations.map(ai => ai?.toJSON ? ai.toJSON() : ai),
      attributes:                this.attributes.map(a => a?.toJSON ? a.toJSON() : a),
      variants:                  this.variants.map(v => v?.toJSON ? v.toJSON() : v),
    };
  }

  static fromJSON(data) {
    if (!data) return null;
    const category = data.category && typeof data.category === "object"
      ? Category.fromJSON(data.category)
      : data.category;
    return new Product({
      code:                      data.code,
      title:                     data.title,
      price:                     data.price,
      description:               data.description,
      brand:                     data.brand,
      id:                        data.id ?? null,
      category,
      attributes_implementations: (data.attributes_implementations ?? []).map(ai => ai && typeof ai === "object" ? AttributeImplementation.fromJSON(ai) : ai),
      attributes:                (data.attributes ?? []).map(a => a && typeof a === "object" ? Attribute.fromJSON(a) : a),
      variants:                  (data.variants ?? []).map(v => v && typeof v === "object" ? Variant.fromJSON(v) : v),
    });
  }

  // ── variantes ─────────────────────────────────────────────────────────────

  _addVariant(variant) { this.variants.push(variant); }

  delVariant(variant_id) {
    const before = this.variants.length;
    this.variants = this.variants.filter(v => v.id !== variant_id);
    return this.variants.length < before;
  }

  addProductImplementation(attribute_implementation) {
    if (!attribute_implementation.attribute.is_static) {
      throw new Error("Estas intentando meter un atributo dinamico como implementacion estatica");
    }
    this._checkImplementation(attribute_implementation);
    if (this._impl_keys.has(attribute_implementation.attribute.key)) {
      throw new Error(`El atributo '${attribute_implementation.attribute.name}' ya está implementado para este producto`);
    }
    this.attributes_implementations.push(attribute_implementation);
    this._impl_keys.add(attribute_implementation.attribute.key);
  }

  _checkImplementation(attr_impl) {
    if (!attr_impl.attribute.checkValue(attr_impl.value)) {
      throw new Error(`El valor '${attr_impl.value}' no es válido para el atributo '${attr_impl.attribute.name}'.`);
    }
    const neededKeys = new Set([...this.getNeededAtributesImplementations(true)].map(a => a.key));
    if (!neededKeys.has(attr_impl.attribute.key)) {
      throw new Error("La implimentacion es de un attributo que no se encuentra subscripto.");
    }
    return true;
  }

  // is_static=false → atributos de variante; is_static=true → atributos de producto
  getNeededAtributesImplementations(is_static = false) {
    return new Set(this.getAttributes().filter(a => a.is_static === is_static));
  }

  createVariantByImplementations(implementations) {
    const neededAttributes = this.getNeededAtributesImplementations();
    const implAttributes   = new Set();
    for (const impl of implementations) {
      if (implAttributes.has(impl.attribute)) {
        console.log(`Error: atributo '${impl.attribute.name}' duplicado en las implementaciones.`);
        return null;
      }
      implAttributes.add(impl.attribute);
    }
    if (!_setsEqual(implAttributes, neededAttributes)) {
      console.log("Error: las implementaciones no coinciden con los atributos requeridos.");
      return null;
    }
    for (const i of implementations) {
      try {
        if (!i.attribute.checkValue(i.value)) {
          console.log(`Error en tipo: valor inválido para '${i.attribute.name}'.`);
          return null;
        }
      } catch (error) {
        console.log(`Error en tipo: ${error.message}`);
        return null;
      }
    }
    this._addVariant(new Variant({ attribute_implementations: implementations }));
  }

  getAddAttributeImpact(attribute) {
    if (this.isAttributeIn(attribute)) return null;
    return { [this.id]: this.variants.map(v => v.id) };
  }
}

// ─── util ─────────────────────────────────────────────────────────────────────

function _setsEqual(a, b) {
  if (a.size !== b.size) return false;
  for (const item of a) if (!b.has(item)) return false;
  return true;
}
