/**
 * AttributeImplementationDTO.js
 *
 * Valor concreto de un atributo sobre un producto o variante.
 *
 * Shape de la API:
 *   { id, attribute: AttributeDTO, value: string }
 *
 * El value siempre llega como string desde la API.
 * La conversión al tipo real (number, boolean) se hace con castValue().
 */
import { AttributeDTO } from "./AttributeDTO.js";

export class AttributeImplementationDTO {
  /**
   * @param {object}       raw
   * @param {number}       [raw.id]
   * @param {object}       raw.attribute   Raw AttributeDTO o instancia
   * @param {string}       raw.value
   */
  constructor({ id = null, attribute, value }) {
    this.id        = id;
    this.attribute = attribute instanceof AttributeDTO
      ? attribute
      : AttributeDTO.fromJSON(attribute);
    this.value     = value;
  }

  static fromJSON(raw) {
    if (!raw) return null;
    return new AttributeImplementationDTO(raw);
  }

  toJSON() {
    return {
      id:        this.id,
      attribute: this.attribute?.toJSON() ?? null,
      value:     this.value,
    };
  }

  /**
   * Retorna el valor casteado al tipo real según data_type del atributo.
   * number  → parseFloat
   * boolean → true/false
   * resto   → string
   */
  castValue() {
    const dt = this.attribute?.data_type;
    if (dt === "number")  return parseFloat(this.value);
    if (dt === "boolean") return this.value === "true" || this.value === true;
    return this.value;
  }
}
