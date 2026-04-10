/**
 * attributeService.js — Lógica de negocio para Atributos
 *
 * Recibe parámetros tipados, llama a AttributeApi, maneja errores de negocio
 * y retorna DTOs ya mapeados.
 *
 * No toca el DOM — no necesita container.
 */
import { AttributeApi } from "../api/attributeApi.js";
import { AttributeDTO } from "../interfaceModels/AttributeDTO.js";

export const AttributeService = {

  /**
   * Lista todos los atributos.
   * @returns {Promise<AttributeDTO[]>}
   */
  async getAll() {
    const { status, data } = await AttributeApi.getAll();
    if (status !== 200) throw new Error(data?.detail ?? "Error al listar atributos");
    return data.map(AttributeDTO.fromJSON);
  },

  /**
   * Obtiene un atributo por id.
   * @param   {number} id
   * @returns {Promise<AttributeDTO|null>}  null si no existe
   */
  async getById(id) {
    const { status, data } = await AttributeApi.getById(id);
    if (status === 404) return null;
    if (status !== 200) throw new Error(data?.detail ?? "Error al obtener atributo");
    return AttributeDTO.fromJSON(data);
  },

  /**
   * Crea un atributo.
   *
   * @param {object}   params
   * @param {string}   params.key         Identificador único (ej: "color")
   * @param {string}   params.name        Nombre legible (ej: "Color")
   * @param {string}   params.data_type   "text" | "number" | "boolean" | "enum"
   * @param {boolean}  params.is_static   true=producto, false=variante
   * @param {string[]} [params.enum_values]  Solo si data_type="enum"
   * @returns {Promise<AttributeDTO>}
   * @throws si el key ya existe o los datos son inválidos (400)
   */
  async create({ key, name, data_type, is_static, enum_values = [] }) {
    const { status, data } = await AttributeApi.create({
      key, name, data_type, is_static, enum_values,
    });
    if (status === 400) throw new Error(data?.detail ?? "Error de validación al crear atributo");
    if (status !== 201) throw new Error(data?.detail ?? "Error al crear atributo");
    return AttributeDTO.fromJSON(data);
  },

  /**
   * Actualiza nombre y/o enum_values de un atributo.
   *
   * @param {number}   id
   * @param {object}   fields
   * @param {string}   [fields.name]           Nuevo nombre
   * @param {string[]} [fields.enum_values]    Reemplaza la lista completa.
   *                                            [] borra todos.
   *                                            undefined no la modifica.
   * @returns {Promise<AttributeDTO|null>}  null si no existe
   */
  async update(id, { name = undefined, enum_values = undefined } = {}) {
    const body = {};
    if (name        !== undefined) body.name        = name;
    if (enum_values !== undefined) body.enum_values = enum_values;
    const { status, data } = await AttributeApi.update(id, body);
    if (status === 404) return null;
    if (status === 400) throw new Error(data?.detail ?? "Error de validación al actualizar");
    return AttributeDTO.fromJSON(data);
  },

  /**
   * Agrega un valor posible a un atributo de tipo enum.
   * (No afecta los valores existentes — usa el endpoint específico)
   *
   * @param {number} id
   * @param {string} value
   * @returns {Promise<AttributeDTO|null>}
   * @throws si el valor ya existe o el atributo no es enum (400)
   */
  async addEnumValue(id, value) {
    const { status, data } = await AttributeApi.addEnumValue(id, value);
    if (status === 404) return null;
    if (status === 400) throw new Error(data?.detail ?? "Valor duplicado o atributo no es enum");
    return AttributeDTO.fromJSON(data);
  },

  /**
   * Elimina un atributo.
   *
   * @param {number} id
   * @returns {Promise<boolean>}  false si no existía
   * @throws si hay implementaciones referenciándolo (FK RESTRICT → 400)
   */
  async delete(id) {
    const { status, data } = await AttributeApi.delete(id);
    if (status === 400) throw new Error(
      data?.detail ?? "No se puede eliminar: hay productos/variantes con este atributo implementado"
    );
    if (status === 404) return false;
    return true;
  },
};
