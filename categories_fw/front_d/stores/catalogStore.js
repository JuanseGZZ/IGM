// Almacén del árbol de catálogo — persiste en localStorage bajo "igm-catalog".
// Wrappea la serialización del Handler para que events.js no toque localStorage directamente.

export const catalogStore = {
  KEY: "igm-catalog",

  save(handler) {
    localStorage.setItem(this.KEY, handler.toJson());
  },

  load(handler) {
    const raw = localStorage.getItem(this.KEY);
    if (!raw) return false;
    try {
      handler.fromJson(raw);
      return true;
    } catch (e) {
      console.warn("Error al cargar catálogo:", e);
      return false;
    }
  },
};
