/**
 * VariantDTO.js
 *
 * Combinación concreta de atributos dinámicos de un producto.
 * Ej: color=rojo + talle=M
 *
 * Shape de la API:
 *   { id, attribute_implementations: AttributeImplementationDTO[] }
 *
 * IMPORTANTE: los IDs de variante NO son estables entre operaciones de
 * escritura sobre el producto (se re-insertan en DB con nuevos IDs).
 * Siempre refrescar el producto antes de usar variant.id.
 */
import { AttributeImplementationDTO } from "./AttributeImplementationDTO.js";

export class VariantDTO {
  /**
   * @param {object}   raw
   * @param {number}   [raw.id]
   * @param {object[]} [raw.attribute_implementations]
   */
  constructor({ id = null, attribute_implementations = [] }) {
    this.id = id;
    this.attribute_implementations = (attribute_implementations ?? []).map((i) =>
      i instanceof AttributeImplementationDTO ? i : AttributeImplementationDTO.fromJSON(i)
    );
  }

  static fromJSON(raw) {
    if (!raw) return null;
    return new VariantDTO(raw);
  }

  toJSON() {
    return {
      id:                       this.id,
      attribute_implementations: this.attribute_implementations.map((i) => i.toJSON()),
    };
  }

  /**
   * Retorna el valor de una implementación por key del atributo.
   * @param {string} attrKey
   * @returns {string|null}
   */
  getValue(attrKey) {
    const impl = this.attribute_implementations.find(
      (i) => i.attribute?.key === attrKey
    );
    return impl ? impl.castValue() : null;
  }
}
