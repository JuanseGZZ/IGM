/**
 * _request.js — Helper de fetch compartido por todas las APIs.
 *
 * Convenciones de retorno:
 *   { status, data }   en todos los casos (incluyendo 400, 404)
 *
 * Solo lanza ApiError en:
 *   - Error de red (fetch falla)
 *   - Status >= 500 (error del servidor)
 *
 * Los errores de negocio (400) y not-found (404) se retornan como
 * { status, data } para que la capa de servicio los maneje.
 */
import { Config } from "../config/config.js";

export class ApiError extends Error {
  /**
   * @param {number} status   HTTP status code (0 = error de red)
   * @param {string} detail   Mensaje del servidor o descripción del error
   */
  constructor(status, detail) {
    super(detail);
    this.name   = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Realiza una petición HTTP a la API.
 *
 * @param {"GET"|"POST"|"PATCH"|"DELETE"} method
 * @param {string}  path    Path relativo a Config.BASE_URL (ej: "/attributes")
 * @param {object}  [body]  Se serializa a JSON si se pasa
 * @returns {Promise<{status: number, data: any}>}
 * @throws  {ApiError}  Solo en error de red o status >= 500
 */
export async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { ...Config.defaultHeaders },
  };
  if (body !== null) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(`${Config.BASE_URL}${path}`, opts);
  } catch (err) {
    throw new ApiError(0, `Error de red: ${err.message}`);
  }

  const data = await res.json().catch(() => null);

  if (res.status >= 500) {
    throw new ApiError(res.status, data?.detail ?? "Error interno del servidor");
  }

  return { status: res.status, data };
}
