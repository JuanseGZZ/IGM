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
  buildChangeParentDecisionForm,
  buildChangeParentImplForm,
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
   * Cambia el padre de una categoría.
   *
   * Flujo automático de hasta tres llamadas:
   *   1. Primera llamada con { parent_id }.
   *   2. Si needs_decision=true → renderiza buildChangeParentDecisionForm en container;
   *      el usuario elige del_opt=1 (inyectar en categoría) o del_opt=2 (eliminar impls huérfanas).
   *      Segunda llamada con { parent_id, del_opt }.
   *   3. Si needs_implementations=true (puede venir de la primera o segunda llamada) →
   *      obtiene data_type/enum_values de los atributos afectados, renderiza
   *      buildChangeParentImplForm, el usuario completa los valores.
   *      Llamada final con { parent_id, del_opt, implementations }.
   *
   * @param {number}      catId
   * @param {number}      parentId
   * @param {HTMLElement} container   Div donde se renderizan los formularios intermedios
   * @returns {Promise<CategoryDTO>}
   */
  async changeParent(catId, parentId, container) {
    const r1 = await CategoryApi.changeParent(catId, { parent_id: parentId, del_opt: 0 });
    if (r1.status === 400) throw new Error(r1.data?.detail ?? "Error al cambiar padre");
    if (r1.status === 404) throw new Error(r1.data?.detail ?? "Categoría no encontrada");

    let d = r1.data;
    let delOpt = 0;

    // success directo sin impacto — el servidor devuelve la categoría directamente
    if (!d.needs_decision && !d.needs_implementations) {
      return CategoryDTO.fromJSON(d);
    }

    // Step 1: atributos huérfanos del padre anterior → pedir decisión
    if (d.needs_decision) {
      delOpt = await new Promise((resolve) => {
        buildChangeParentDecisionForm(container, d.impact, resolve);
      });

      const r2 = await CategoryApi.changeParent(catId, { parent_id: parentId, del_opt: delOpt });
      if (r2.status === 400) throw new Error(r2.data?.detail ?? "Error al aplicar decisión");
      if (r2.status === 404) throw new Error(r2.data?.detail ?? "No encontrado");

      d = r2.data;
      if (!d.needs_decision && !d.needs_implementations) {
        return CategoryDTO.fromJSON(d);
      }
    }

    // Step 2: nuevo padre tiene atributos sin cobertura → pedir implementations
    if (d.needs_implementations) {
      // enriquecer el impact con data_type y enum_values via AttributeApi
      const { data: allAttrsRaw } = await AttributeApi.getAll();
      const attrsByKey = Object.fromEntries(
        (allAttrsRaw ?? []).map((a) => [a.key, a])
      );

      const impactWithAttrs = d.impact.map((attrInfo) => ({
        ...attrInfo,
        data_type:   attrsByKey[attrInfo.attribute_key]?.data_type   ?? "text",
        enum_values: attrsByKey[attrInfo.attribute_key]?.enum_values ?? [],
      }));

      const implementations = await new Promise((resolve) => {
        buildChangeParentImplForm(container, impactWithAttrs, resolve);
      });

      const r3 = await CategoryApi.changeParent(catId, {
        parent_id: parentId,
        del_opt: delOpt,
        implementations,
      });
      if (r3.status === 400) throw new Error(r3.data?.detail ?? "Error al aplicar implementaciones");
      if (r3.status === 404) throw new Error(r3.data?.detail ?? "No encontrado");

      return CategoryDTO.fromJSON(r3.data);
    }

    throw new Error("Respuesta inesperada del servidor");
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
