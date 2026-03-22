const Dtos = {
  attributeCreate({ key, name, data_type, is_static = false, enum_values = [] }) {
    return { key, name, data_type, is_static, enum_values };
  },

  attributeUpdate({ name, is_static = false, enum_values = [] }) {
    return { name, is_static, enum_values };
  },

  categoryCreate({ name, attribute_ids = [] }) {
    return { name, attribute_ids: attribute_ids.map(Number) };
  },

  categoryUpdate({ name, attribute_ids = [] }) {
    return { name, attribute_ids: attribute_ids.map(Number) };
  },

  productCreate({ code, title, price, description, brand, category_id, attribute_ids = [], static_implementations = [] }) {
    return {
      code, title, description, brand,
      price: parseFloat(price),
      category_id: parseInt(category_id),
      attribute_ids: attribute_ids.map(Number),
      static_implementations,
    };
  },

  productUpdate({ title, price, description, brand, category_id, attribute_ids = [], static_implementations = [] }) {
    return {
      title, description, brand,
      price: parseFloat(price),
      category_id: parseInt(category_id),
      attribute_ids: attribute_ids.map(Number),
      static_implementations,
    };
  },

  implementationIn(attribute_id, value) {
    return { attribute_id: parseInt(attribute_id), value: String(value) };
  },

  variantIn(implementations) {
    return { implementations };
  },
};