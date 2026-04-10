/**
 * config.js — Configuración global del framework IGM Frontend
 *
 * Modificar BASE_URL antes de inicializar el framework.
 * En el HTML: import { Config } from './frontFW/config/config.js';
 *             Config.BASE_URL = 'https://mi-server.com';
 */

export const Config = {
  /** URL base del server FastAPI */
  BASE_URL: "http://localhost:8001",

  /** Headers enviados en todas las peticiones */
  defaultHeaders: {
    "Content-Type": "application/json",
  },

  /** ms antes de abortar una petición (0 = sin timeout) */
  timeout: 0,
};
