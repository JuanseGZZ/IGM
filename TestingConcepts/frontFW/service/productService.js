/**
 * productService.js — Lógica de negocio para Productos
 *
 * Las operaciones complejas (addDynamicAttribute, removeOwnAttribute, createVariant)
 * aceptan un `container` HTMLElement donde se renderiza el formulario de
 * implementación si el server lo requiere.
 *
 * Patrón general:
 *   1. Primera llamada → si hay impacto, renderiza form en container.
 *   2. El usuario completa el form → segunda llamada.
 *   3. Retorna el ProductDTO final.
 */
import { ProductApi }   from "../api/productApi.js";
import { AttributeApi } from "../api/attributeApi.js";
import { ProductDTO }   from "../interfaceModels/ProductDTO.js";
import { AttributeDTO } from "../interfaceModels/AttributeDTO.js";
import {
  buildDynamicImplForm,
  buildVariantForm,
  buildDecisionForm,
} from "./formBuilder.js";

export const ProductService = {

  /**
   * Lista todos los productos.
   * @returns {Promise<ProductDTO[]>}
   */
  async getAll() {
    const { status, data } = await ProductApi.getAll();
    if (status !== 200) throw new Error(data?.detail ?? "Error al listar productos");
    return data.map(ProductDTO.fromJSON);
  },

  /**
   * Obtiene un producto por id.
   * @param   {number} id
   * @returns {Promise<ProductDTO|null>}
   */
  async getById(id) {
    const { status, data } = await ProductApi.getById(id);
    if (status === 404) return null;
    if (status !== 200) throw new Error(data?.detail ?? "Error al obtener producto");
    return ProductDTO.fromJSON(data);
  },

  /**
   * Obtiene un producto por código único.
   * @param   {string} code
   * @returns {Promise<ProductDTO|null>}
   */
  async getByCode(code) {
    const { status, data } = await ProductApi.getByCode(code);
    if (status === 404) return null;
    if (status !== 200) throw new Error(data?.detail ?? "Error al obtener producto por código");
    return ProductDTO.fromJSON(data);
  },

  /**
   * Crea un producto.
   *
   * @param {object}  params
   * @param {string}  params.code          Código único (ej: "REMERA-001")
   * @param {string}  params.title         Título
   * @param {number}  params.price         Precio (≥ 0)
   * @param {string}  params.description   Descripción
   * @param {string}  params.brand         Marca
   * @param {number}  params.category_id   ID de la categoría (debe existir)
   * @returns {Promise<ProductDTO>}
   */
  async create({ code, title, price, description, brand, category_id }) {
    const { status, data } = await ProductApi.create({
      code, title, price, description, brand, category_id,
    });
    if (status === 400) throw new Error(data?.detail ?? "Error de validación al crear producto");
    if (status !== 201) throw new Error(data?.detail ?? "Error al crear producto");
    return ProductDTO.fromJSON(data);
  },

  /**
   * Actualiza campos base del producto.
   * Solo se envían al server los campos que se pasan (parcial).
   *
   * @param {number}  id
   * @param {object}  fields
   * @param {string}  [fields.title]
   * @param {number}  [fields.price]
   * @param {string}  [fields.description]
   * @param {string}  [fields.brand]
   * @param {number}  [fields.category_id]
   * @returns {Promise<ProductDTO|null>}
   */
  async update(id, fields = {}) {
    const ALLOWED = ["title", "price", "description", "brand", "category_id"];
    const body = Object.fromEntries(
      Object.entries(fields).filter(([k, v]) => ALLOWED.includes(k) && v != null)
    );
    const { status, data } = await ProductApi.update(id, body);
    if (status === 404) return null;
    if (status === 400) throw new Error(data?.detail ?? "Error de validación al actualizar");
    return ProductDTO.fromJSON(data);
  },

  /**
   * Elimina un producto (cascadea variantes e implementaciones).
   * @param   {number} id
   * @returns {Promise<boolean>}
   */
  async delete(id) {
    const { status, data } = await ProductApi.delete(id);
    if (status === 400) throw new Error(data?.detail ?? "No se puede eliminar el producto");
    if (status === 404) return false;
    return true;
  },

  /**
   * Agrega una implementación de atributo ESTÁTICO directamente al producto.
   *
   * El atributo debe estar en la categoría del producto o en sus atributos propios.
   *
   * @param {number}  prodId
   * @param {number}  attrId
   * @param {*}       value
   * @returns {Promise<ProductDTO>}
   * @throws si el atributo no está suscripto o la impl ya existe (400)
   */
  async addImplementation(prodId, attrId, value) {
    const { status, data } = await ProductApi.addImplementation(prodId, attrId, value);
    if (status === 400) throw new Error(
      data?.detail ?? "Atributo no suscripto, tipo inválido o implementación duplicada"
    );
    if (status === 404) throw new Error(data?.detail ?? "Producto o atributo no encontrado");
    return ProductDTO.fromJSON(data);
  },

  /**
   * Agrega un atributo DINÁMICO al producto.
   *
   * Flujo automático de dos llamadas:
   *   1. Si el producto no tiene variantes → se agrega directamente.
   *   2. Si tiene variantes y no se proveen valores → renderiza buildDynamicImplForm
   *      en container con las variantes que necesitan valor.
   *   3. El usuario completa → segunda llamada con variant_options.
   *
   * @param {number}      prodId
   * @param {number}      attrId
   * @param {HTMLElement} container   Div para el formulario si hay impacto
   * @returns {Promise<ProductDTO>}
   */
  async addDynamicAttribute(prodId, attrId, container) {
    const { status, data } = await ProductApi.addDynamicAttribute(prodId, {
      attribute_id: attrId,
    });
    if (status === 400) throw new Error(data?.detail ?? "Error al agregar atributo dinámico");

    // Sin impacto → operación completa
    if (!data.needs_implementations) {
      return ProductDTO.fromJSON(data.product);
    }

    // Impacto: [{variant_id}]
    // Adaptamos al formato que espera buildDynamicImplForm (que espera productos con variantes)
    const attrData = await AttributeApi.getById(attrId).then((r) => r.data);
    const attribute = AttributeDTO.fromJSON(attrData);

    // Para el form, envolvemos las variantes bajo un "producto fake" con el prodId
    const prod = await ProductService.getById(prodId);
    const wrappedImpact = [{
      product_id:   prodId,
      product_code: prod?.code ?? String(prodId),
      variants:     data.impact, // [{variant_id}]
    }];

    return new Promise((resolve, reject) => {
      buildDynamicImplForm(
        container,
        { attribute, impact: wrappedImpact },
        async (implementations) => {
          try {
            // El endpoint de producto espera variant_options plano [{variant_id, value}]
            const variant_options = implementations.flatMap((p) => p.variants);

            const { status: s2, data: d2 } = await ProductApi.addDynamicAttribute(prodId, {
              attribute_id: attrId,
              variant_options,
            });
            if (s2 === 400) throw new Error(d2?.detail ?? "Implementaciones inválidas");
            resolve(ProductDTO.fromJSON(d2.product));
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  },

  /**
   * Elimina un atributo propio del producto.
   *
   * Flujo automático:
   *   1. Primera llamada con del_opt=0 → detectar si hay implementaciones huérfanas.
   *   2. Si needs_decision=true → renderiza buildDecisionForm en container
   *      con del_opt=1 (eliminar impls) — del_opt=2 no aplica en productos.
   *   3. Segunda llamada con del_opt=1.
   *
   * @param {number}      prodId
   * @param {string}      attrKey   key del atributo (ej: "color")
   * @param {HTMLElement} container
   * @returns {Promise<ProductDTO>}
   * @throws si el atributo no es propio del producto (400)
   */
  async removeOwnAttribute(prodId, attrKey, container) {
    const { status, data } = await ProductApi.removeOwnAttribute(prodId, attrKey, 0);
    if (status === 400) throw new Error(
      data?.detail ?? `El atributo '${attrKey}' no es propio del producto`
    );
    if (status === 404) throw new Error(data?.detail ?? "No encontrado");

    if (!data.needs_decision) {
      return ProductDTO.fromJSON(data.product);
    }

    return new Promise((resolve, reject) => {
      // En productos solo existe del_opt=1 (no del_opt=2)
      buildDecisionForm(
        container,
        { impact: data.impact, hasOptTwo: false },
        async (_chosenOpt) => {
          try {
            const { status: s2, data: d2 } = await ProductApi.removeOwnAttribute(prodId, attrKey, 1);
            if (s2 === 400) throw new Error(d2?.detail ?? "Error al eliminar implementaciones");
            resolve(ProductDTO.fromJSON(d2.product));
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  },

  /**
   * Crea una variante del producto.
   *
   * Flujo automático:
   *   1. Envía las implementations.
   *   2. Si el server responde "implementations_invalid" → renderiza buildVariantForm
   *      en container con los atributos necesarios.
   *   3. El usuario completa → reintenta recursivamente.
   *
   * @param {number}      prodId
   * @param {Array}       implementations   [{attribute_id, value}]
   *                      Puede ser [] en la primera llamada para disparar el form.
   * @param {HTMLElement} container
   * @returns {Promise<ProductDTO>}
   */
  async createVariant(prodId, implementations = [], container) {
    const { status, data } = await ProductApi.createVariant(prodId, implementations);
    if (status === 400) throw new Error(data?.detail ?? "Error al crear variante");

    // Éxito: data es el ProductDTO completo
    if (!data.error) {
      return ProductDTO.fromJSON(data);
    }

    // implementations_invalid → construir formulario con los atributos necesarios
    const neededAttrs = (data.needed_attributes ?? []).map(AttributeDTO.fromJSON);

    return new Promise((resolve, reject) => {
      buildVariantForm(container, neededAttrs, async (filledImpls) => {
        try {
          const prod = await ProductService.createVariant(prodId, filledImpls, container);
          resolve(prod);
        } catch (err) {
          reject(err);
        }
      });
    });
  },

  /**
   * Elimina una variante del producto.
   *
   * NOTA: después de eliminar, los IDs de las variantes restantes pueden
   * haber cambiado si el producto se re-persistió. Siempre refrescar con getById.
   *
   * @param {number} prodId
   * @param {number} variantId
   * @returns {Promise<ProductDTO>}
   */
  async deleteVariant(prodId, variantId) {
    const { status, data } = await ProductApi.deleteVariant(prodId, variantId);
    if (status === 400) throw new Error(
      data?.detail ?? `Variante ${variantId} no encontrada en el producto`
    );
    if (status === 404) throw new Error(data?.detail ?? "Producto no encontrado");
    return ProductDTO.fromJSON(data);
  },
};
