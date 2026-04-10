/**
 * ProductDTO.js
 *
 * Producto del catálogo con atributos, implementaciones y variantes.
 *
 * Shape de la API (GET /products/{id}):
 * {
 *   id, code, title, price, description, brand,
 *   category:                  CategoryDTO,
 *   attributes:                AttributeDTO[],          ← atributos PROPIOS del producto
 *   attributes_implementations: AttributeImplementationDTO[],  ← impl estáticas
 *   variants:                  VariantDTO[]
 * }
 *
 * NOTA: la API retorna "category" (objeto completo), NO "category_id".
 * Para leer el id de la categoría: product.category.id
 */
import { AttributeDTO }               from "./AttributeDTO.js";
import { AttributeImplementationDTO } from "./AttributeImplementationDTO.js";
import { VariantDTO }                 from "./VariantDTO.js";
import { CategoryDTO }                from "./CategoryDTO.js";

export class ProductDTO {
  /**
   * @param {object}   raw
   * @param {number}   [raw.id]
   * @param {string}   raw.code
   * @param {string}   raw.title
   * @param {number}   raw.price
   * @param {string}   raw.description
   * @param {string}   raw.brand
   * @param {object}   [raw.category]
   * @param {object[]} [raw.attributes]
   * @param {object[]} [raw.attributes_implementations]
   * @param {object[]} [raw.variants]
   */
  constructor({
    id = null,
    code,
    title,
    price,
    description,
    brand,
    category = null,
    attributes = [],
    attributes_implementations = [],
    variants = [],
  }) {
    this.id                       = id;
    this.code                     = code;
    this.title                    = title;
    this.price                    = price;
    this.description              = description;
    this.brand                    = brand;
    this.category                 = category instanceof CategoryDTO
      ? category
      : CategoryDTO.fromJSON(category);
    this.attributes               = (attributes ?? []).map((a) =>
      a instanceof AttributeDTO ? a : AttributeDTO.fromJSON(a)
    );
    this.attributes_implementations = (attributes_implementations ?? []).map((i) =>
      i instanceof AttributeImplementationDTO ? i : AttributeImplementationDTO.fromJSON(i)
    );
    this.variants                 = (variants ?? []).map((v) =>
      v instanceof VariantDTO ? v : VariantDTO.fromJSON(v)
    );
  }

  static fromJSON(raw) {
    if (!raw) return null;
    return new ProductDTO(raw);
  }

  toJSON() {
    return {
      id:                        this.id,
      code:                      this.code,
      title:                     this.title,
      price:                     this.price,
      description:               this.description,
      brand:                     this.brand,
      category:                  this.category?.toJSON() ?? null,
      attributes:                this.attributes.map((a) => a.toJSON()),
      attributes_implementations: this.attributes_implementations.map((i) => i.toJSON()),
      variants:                  this.variants.map((v) => v.toJSON()),
    };
  }

  /**
   * Todos los atributos dinámicos que aplican al producto:
   * los heredados de la categoría + los propios del producto.
   * @returns {AttributeDTO[]}
   */
  getAllDynamicAttributes() {
    const catDyn  = (this.category?.attributes ?? []).filter((a) => a.isDynamic());
    const ownDyn  = this.attributes.filter((a) => a.isDynamic());
    return _dedup([...catDyn, ...ownDyn]);
  }

  /**
   * Todos los atributos estáticos que aplican al producto.
   * @returns {AttributeDTO[]}
   */
  getAllStaticAttributes() {
    const catStat = (this.category?.attributes ?? []).filter((a) => a.isStatic());
    const ownStat = this.attributes.filter((a) => a.isStatic());
    return _dedup([...catStat, ...ownStat]);
  }

  /**
   * Retorna la implementación estática de un atributo por key.
   * @param {string} attrKey
   * @returns {AttributeImplementationDTO|null}
   */
  getImplementation(attrKey) {
    return this.attributes_implementations.find(
      (i) => i.attribute?.key === attrKey
    ) ?? null;
  }
}

function _dedup(attrs) {
  const seen = new Set();
  return attrs.filter((a) => {
    if (seen.has(a.id)) return false;
    seen.add(a.id);
    return true;
  });
}
