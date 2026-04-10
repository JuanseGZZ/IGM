/**
 * categoryApi.js — Llamadas HTTP crudas para /categories
 */
import { request } from "./_request.js";

export const CategoryApi = {

  /** GET /categories */
  getAll() {
    return request("GET", "/categories");
  },

  /** GET /categories/{id} */
  getById(id) {
    return request("GET", `/categories/${id}`);
  },

  /**
   * POST /categories
   * @param {string} name
   */
  create(name) {
    return request("POST", "/categories", { name });
  },

  /**
   * PATCH /categories/{id}
   * @param {string} name
   */
  updateName(id, name) {
    return request("PATCH", `/categories/${id}`, { name });
  },

  /** DELETE /categories/{id} */
  delete(id) {
    return request("DELETE", `/categories/${id}`);
  },

  /**
   * POST /categories/{id}/dynamic-attribute
   *
   * Primera llamada  → { attribute_id }
   * Segunda llamada  → { attribute_id, implementations: [{product_id, variants:[{variant_id, value}]}] }
   *
   * Respuesta posible A (necesita completar):
   *   { needs_implementations: true, impact: [{product_id, product_code, variants:[{variant_id}]}] }
   * Respuesta posible B (completado):
   *   { needs_implementations: false, category: {...} }
   */
  addDynamicAttribute(catId, body) {
    return request("POST", `/categories/${catId}/dynamic-attribute`, body);
  },

  /**
   * POST /categories/{id}/static-attribute
   *
   * Primera llamada  → { attribute_id }
   * Segunda llamada  → { attribute_id, implementations: [{product_id, value}] }
   *
   * Respuesta posible A: { needs_implementations: true, impact: [{product_id, product_code}] }
   * Respuesta posible B: { needs_implementations: false, category: {...} }
   */
  addStaticAttribute(catId, body) {
    return request("POST", `/categories/${catId}/static-attribute`, body);
  },

  /**
   * DELETE /categories/{id}/attributes/{attr_id}?del_opt=0|1|2
   *
   * del_opt=0 → reporta impacto, no modifica nada
   *   Respuesta: { needs_decision: true,  impact: [{product_id, product_code}] }
   *            | { needs_decision: false, category: {...} }
   * del_opt=1 → elimina implementaciones huérfanas
   * del_opt=2 → migra el atributo directamente a los productos afectados
   */
  removeAttribute(catId, attrId, delOpt = 0) {
    return request("DELETE", `/categories/${catId}/attributes/${attrId}?del_opt=${delOpt}`);
  },

  /**
   * POST /categories/{cat_id}/products/{product_id}
   * Reasigna un producto a esta categoría.
   */
  addProduct(catId, productId) {
    return request("POST", `/categories/${catId}/products/${productId}`);
  },
};
