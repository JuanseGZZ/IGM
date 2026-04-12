/**
 * CategoryDTO.js
 *
 * Categoría del catálogo. Puede tener atributos y productos propios.
 *
 * Shape de la API:
 *   { id, name, attributes: AttributeDTO[], products: ProductDTO[] }
 *
 * Regla de negocio: una categoría no puede tener subcategorías
 * y productos al mismo tiempo (solo las hojas del árbol tienen productos).
 * El árbol padre-hijo NO se persiste en DB — solo existe en memoria.
 */
import { AttributeDTO } from "./AttributeDTO.js";

export class CategoryDTO {
  /**
   * @param {object}   raw
   * @param {number}   [raw.id]
   * @param {string}   raw.name
   * @param {object[]} [raw.attributes]
   * @param {object[]} [raw.products]    Se pasan como raw; mapear con ProductDTO externamente
   */
  constructor({ id = null, name, father = null, attributes = [], products = [] }) {
    this.id         = id;
    this.name       = name;
    /** { id, name } del padre, o null si es raíz */
    this.father     = father ?? null;
    this.attributes = (attributes ?? []).map((a) =>
      a instanceof AttributeDTO ? a : AttributeDTO.fromJSON(a)
    );
    // products se guarda raw para evitar circular import con ProductDTO
    this.products   = products ?? [];
  }

  static fromJSON(raw) {
    if (!raw) return null;
    return new CategoryDTO(raw);
  }

  toJSON() {
    return {
      id:         this.id,
      name:       this.name,
      father:     this.father,
      attributes: this.attributes.map((a) => a.toJSON()),
      products:   this.products.map((p) =>
        typeof p.toJSON === "function" ? p.toJSON() : p
      ),
    };
  }

  /** Atributos dinámicos de la categoría (is_static=false) */
  getDynamicAttributes() {
    return this.attributes.filter((a) => a.isDynamic());
  }

  /** Atributos estáticos de la categoría (is_static=true) */
  getStaticAttributes() {
    return this.attributes.filter((a) => a.isStatic());
  }
}
