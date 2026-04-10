/**
 * categoryService.js — Lógica de negocio para Categorías
 *
 * Las operaciones que pueden requerir datos adicionales (addDynamicAttribute,
 * addStaticAttribute, removeAttribute) aceptan un `container` HTMLElement.
 * Si el server devuelve needs_implementations/needs_decision, se construye
 * automáticamente el formulario en ese container y se espera al usuario.
 *
 * El container se pasa como último parámetro. Si la operación no tiene impacto,
 * el container no se toca.
 */
import { CategoryApi }  from "../api/categoryApi.js";
import { AttributeApi } from "../api/attributeApi.js";
import { CategoryDTO }  from "../interfaceModels/CategoryDTO.js";
import { AttributeDTO } from "../interfaceModels/AttributeDTO.js";
import {
  buildDynamicImplForm,
  buildStaticImplForm,
  buildDecisionForm,
} from "./formBuilder.js";

export const CategoryService = {

  /**
   * Lista todas las categorías (con atributos y productos).
   * @returns {Promise<CategoryDTO[]>}
   */
  async getAll() {
    const { status, data } = await CategoryApi.getAll();
    if (status !== 200) throw new Error(data?.detail ?? "Error al listar categorías");
    return data.map(CategoryDTO.fromJSON);
  },

  /**
   * Obtiene una categoría por id.
   * @param   {number} id
   * @returns {Promise<CategoryDTO|null>}
   */
  async getById(id) {
    const { status, data } = await CategoryApi.getById(id);
    if (status === 404) return null;
    if (status !== 200) throw new Error(data?.detail ?? "Error al obtener categoría");
    return CategoryDTO.fromJSON(data);
  },

  /**
   * Crea una categoría vacía.
   * @param   {string} name
   * @returns {Promise<CategoryDTO>}
   */
  async create(name) {
    const { status, data } = await CategoryApi.create(name);
    if (status !== 201) throw new Error(data?.detail ?? "Error al crear categoría");
    return CategoryDTO.fromJSON(data);
  },

  /**
   * Actualiza el nombre de una categoría.
   * @param   {number} id
   * @param   {string} name
   * @returns {Promise<CategoryDTO|null>}
   */
  async updateName(id, name) {
    const { status, data } = await CategoryApi.updateName(id, name);
    if (status === 404) return null;
    if (status === 400) throw new Error(data?.detail ?? "Error al actualizar nombre");
    return CategoryDTO.fromJSON(data);
  },

  /**
   * Elimina una categoría.
   * Falla (400) si tiene productos asociados (FK RESTRICT).
   *
   * @param   {number} id
   * @returns {Promise<boolean>}  false si no existía
   */
  async delete(id) {
    const { status, data } = await CategoryApi.delete(id);
    if (status === 400) throw new Error(
      data?.detail ?? "No se puede eliminar: la categoría tiene productos asociados"
    );
    if (status === 404) return false;
    return true;
  },

  /**
   * Agrega un atributo DINÁMICO a la categoría.
   *
   * Flujo automático de dos llamadas:
   *   1. Llama al server sin implementations.
   *   2. Si needs_implementations=true → renderiza buildDynamicImplForm en container
   *      y espera a que el usuario complete los valores.
   *   3. Segunda llamada con los valores completados.
   *
   * @param {number}      catId
   * @param {number}      attrId
   * @param {HTMLElement} container   Div donde se renderiza el formulario si hay impacto
   * @returns {Promise<CategoryDTO>}
   */
  async addDynamicAttribute(catId, attrId, container) {
    const { status, data } = await CategoryApi.addDynamicAttribute(catId, {
      attribute_id: attrId,
    });
    if (status === 400) throw new Error(data?.detail ?? "Error al agregar atributo");
    if (status === 404) throw new Error(data?.detail ?? "Categoría o atributo no encontrado");

    // Sin impacto → operación completa
    if (!data.needs_implementations) {
      return CategoryDTO.fromJSON(data.category);
    }

    // Necesita completar valores para las variantes afectadas
    const attrData = await AttributeApi.getById(attrId).then((r) => r.data);
    const attribute = AttributeDTO.fromJSON(attrData);

    return new Promise((resolve, reject) => {
      buildDynamicImplForm(
        container,
        { attribute, impact: data.impact },
        async (implementations) => {
          try {
            const { status: s2, data: d2 } = await CategoryApi.addDynamicAttribute(catId, {
              attribute_id: attrId,
              implementations,
            });
            if (s2 === 400) throw new Error(d2?.detail ?? "Implementaciones inválidas");
            resolve(CategoryDTO.fromJSON(d2.category));
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  },

  /**
   * Agrega un atributo ESTÁTICO a la categoría.
   *
   * Flujo automático de dos llamadas:
   *   1. Llama al server sin implementations.
   *   2. Si needs_implementations=true → renderiza buildStaticImplForm en container.
   *   3. Segunda llamada con los valores completados.
   *
   * @param {number}      catId
   * @param {number}      attrId
   * @param {HTMLElement} container
   * @returns {Promise<CategoryDTO>}
   */
  async addStaticAttribute(catId, attrId, container) {
    const { status, data } = await CategoryApi.addStaticAttribute(catId, {
      attribute_id: attrId,
    });
    if (status === 400) throw new Error(data?.detail ?? "Error al agregar atributo");
    if (status === 404) throw new Error(data?.detail ?? "Categoría o atributo no encontrado");

    if (!data.needs_implementations) {
      return CategoryDTO.fromJSON(data.category);
    }

    const attrData = await AttributeApi.getById(attrId).then((r) => r.data);
    const attribute = AttributeDTO.fromJSON(attrData);

    return new Promise((resolve, reject) => {
      buildStaticImplForm(
        container,
        { attribute, impact: data.impact },
        async (implementations) => {
          try {
            const { status: s2, data: d2 } = await CategoryApi.addStaticAttribute(catId, {
              attribute_id: attrId,
              implementations,
            });
            if (s2 === 400) throw new Error(d2?.detail ?? "Implementaciones inválidas");
            resolve(CategoryDTO.fromJSON(d2.category));
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  },

  /**
   * Elimina un atributo de la categoría.
   *
   * Flujo automático:
   *   1. Primera llamada con del_opt=0 (detectar impacto).
   *   2. Si needs_decision=true → renderiza buildDecisionForm en container.
   *      El usuario elige del_opt=1 (eliminar impls) o del_opt=2 (migrar al producto).
   *   3. Segunda llamada con el del_opt elegido.
   *
   * @param {number}      catId
   * @param {number}      attrId
   * @param {HTMLElement} container
   * @returns {Promise<CategoryDTO>}
   */
  async removeAttribute(catId, attrId, container) {
    const { status, data } = await CategoryApi.removeAttribute(catId, attrId, 0);
    if (status === 400) throw new Error(data?.detail ?? "Error al eliminar atributo");
    if (status === 404) throw new Error(data?.detail ?? "No encontrado");

    // Sin impacto → ya se eliminó
    if (!data.needs_decision) {
      return CategoryDTO.fromJSON(data.category);
    }

    // El usuario debe decidir qué hacer con los productos afectados
    return new Promise((resolve, reject) => {
      buildDecisionForm(
        container,
        { impact: data.impact, hasOptTwo: true },
        async (chosenOpt) => {
          try {
            const { status: s2, data: d2 } = await CategoryApi.removeAttribute(catId, attrId, chosenOpt);
            if (s2 === 400) throw new Error(d2?.detail ?? "Error al aplicar decisión");
            resolve(CategoryDTO.fromJSON(d2.category));
          } catch (err) {
            reject(err);
          }
        }
      );
    });
  },

  /**
   * Reasigna un producto a esta categoría.
   * Falla (400) si la categoría tiene subcategorías.
   *
   * @param {number} catId
   * @param {number} productId
   * @returns {Promise<object>}  ProductDTO raw
   */
  async addProduct(catId, productId) {
    const { status, data } = await CategoryApi.addProduct(catId, productId);
    if (status === 400) throw new Error(
      data?.detail ?? "La categoría tiene subcategorías y no puede tener productos directos"
    );
    if (status === 404) throw new Error(data?.detail ?? "No encontrado");
    return data; // ProductDTO raw — importar ProductDTO en el caller si se quiere mapear
  },
};
