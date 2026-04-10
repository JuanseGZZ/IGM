/**
 * attributeApi.js — Llamadas HTTP crudas para /attributes
 *
 * Esta capa solo hace fetch. No transforma DTOs ni maneja errores de negocio.
 * Toda la lógica vive en attributeService.js.
 */
import { request } from "./_request.js";

export const AttributeApi = {

  /** GET /attributes → { status, data: raw[] } */
  getAll() {
    return request("GET", "/attributes");
  },

  /** GET /attributes/{id} → { status, data: raw | null } */
  getById(id) {
    return request("GET", `/attributes/${id}`);
  },

  /**
   * POST /attributes
   * @param {{ key, name, data_type, is_static, enum_values? }} body
   */
  create(body) {
    return request("POST", "/attributes", body);
  },

  /**
   * PATCH /attributes/{id}
   * @param {{ name?, enum_values? }} body  — solo los campos a actualizar
   *   enum_values reemplaza la lista completa (no es un append).
   *   Para agregar un valor individual usar addEnumValue.
   */
  update(id, body) {
    return request("PATCH", `/attributes/${id}`, body);
  },

  /** DELETE /attributes/{id} */
  delete(id) {
    return request("DELETE", `/attributes/${id}`);
  },

  /**
   * POST /attributes/{id}/enum-values
   * Agrega un valor posible a un atributo enum (sin tocar los existentes).
   * @param {string} value
   */
  addEnumValue(id, value) {
    return request("POST", `/attributes/${id}/enum-values`, { value });
  },
};
