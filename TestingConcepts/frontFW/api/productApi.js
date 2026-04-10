/**
 * productApi.js — Llamadas HTTP crudas para /products
 */
import { request } from "./_request.js";

export const ProductApi = {

  /** GET /products */
  getAll() {
    return request("GET", "/products");
  },

  /** GET /products/{id} */
  getById(id) {
    return request("GET", `/products/${id}`);
  },

  /**
   * GET /products/by-code/{code}
   * NOTA: este endpoint debe registrarse antes de /{id} en FastAPI
   * para evitar que "by-code" se trate como entero.
   */
  getByCode(code) {
    return request("GET", `/products/by-code/${encodeURIComponent(code)}`);
  },

  /**
   * POST /products
   * @param {{ code, title, price, description, brand, category_id }} body
   */
  create(body) {
    return request("POST", "/products", body);
  },

  /**
   * PATCH /products/{id}
   * @param {{ title?, price?, description?, brand?, category_id? }} body
   * Solo se actualizan los campos presentes.
   */
  update(id, body) {
    return request("PATCH", `/products/${id}`, body);
  },

  /** DELETE /products/{id} — cascadea variantes e implementaciones */
  delete(id) {
    return request("DELETE", `/products/${id}`);
  },

  /**
   * POST /products/{id}/dynamic-attribute
   *
   * Primera llamada  → { attribute_id }
   * Segunda llamada  → { attribute_id, variant_options: [{variant_id, value}] }
   *
   * Respuesta A: { needs_implementations: true,  impact: [{variant_id}] }
   * Respuesta B: { needs_implementations: false, product: {...} }
   */
  addDynamicAttribute(prodId, body) {
    return request("POST", `/products/${prodId}/dynamic-attribute`, body);
  },

  /**
   * POST /products/{id}/implementations
   * Agrega implementación de atributo estático.
   * El atributo debe estar en la categoría del producto o en sus atributos propios.
   *
   * @param {number} attrId
   * @param {*}      value
   */
  addImplementation(prodId, attrId, value) {
    return request("POST", `/products/${prodId}/implementations`, {
      attribute_id: attrId,
      value,
    });
  },

  /**
   * DELETE /products/{id}/attributes/{attr_key}?del_opt=0|1
   *
   * del_opt=0 → reporta impacto (implementaciones o variantes afectadas)
   * del_opt=1 → elimina implementaciones huérfanas
   *
   * Respuesta: { needs_decision: bool, impact?: [...], product?: {...} }
   */
  removeOwnAttribute(prodId, attrKey, delOpt = 0) {
    return request("DELETE", `/products/${prodId}/attributes/${encodeURIComponent(attrKey)}?del_opt=${delOpt}`);
  },

  /**
   * POST /products/{id}/variants
   * @param {Array<{attribute_id, value}>} implementations
   *   Debe cubrir EXACTAMENTE todos los atributos dinámicos del producto.
   *
   * Respuesta éxito: producto completo (con la nueva variante)
   * Respuesta error: { error: "implementations_invalid", needed_attributes: [...] }
   */
  createVariant(prodId, implementations) {
    return request("POST", `/products/${prodId}/variants`, { implementations });
  },

  /** DELETE /products/{id}/variants/{variant_id} → producto actualizado */
  deleteVariant(prodId, variantId) {
    return request("DELETE", `/products/${prodId}/variants/${variantId}`);
  },
};
