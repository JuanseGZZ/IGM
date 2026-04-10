/**
 * AttributeDTO.js
 *
 * Representa un atributo del catálogo de productos.
 *
 * Shapes de la API:
 *   { id, key, name, data_type, is_static, enum_values[] }
 *
 * data_type : "text" | "number" | "boolean" | "enum"
 * is_static : true  → atributo de producto  (implementado en el producto)
 *             false → atributo de variante  (implementado en cada variante)
 */
export class AttributeDTO {
  /**
   * @param {object}   raw
   * @param {number}   [raw.id]
   * @param {string}   raw.key
   * @param {string}   raw.name
   * @param {string}   raw.data_type   "text"|"number"|"boolean"|"enum"
   * @param {boolean}  raw.is_static
   * @param {string[]} [raw.enum_values]
   */
  constructor({ id = null, key, name, data_type, is_static, enum_values = [] }) {
    this.id          = id;
    this.key         = key;
    this.name        = name;
    this.data_type   = data_type;
    this.is_static   = is_static;
    this.enum_values = enum_values ?? [];
  }

  static fromJSON(raw) {
    if (!raw) return null;
    return new AttributeDTO(raw);
  }

  toJSON() {
    return {
      id:          this.id,
      key:         this.key,
      name:        this.name,
      data_type:   this.data_type,
      is_static:   this.is_static,
      enum_values: this.enum_values,
    };
  }

  isEnum()    { return this.data_type === "enum"; }
  isStatic()  { return this.is_static === true; }
  isDynamic() { return this.is_static === false; }
}
