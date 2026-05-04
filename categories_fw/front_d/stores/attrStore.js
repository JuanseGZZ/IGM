// Almacén global de atributos — persiste en localStorage bajo "igm-attrs".
// Los charts de categoría referencian copias de estos objetos planos.
// Estructura: { id, key, name, data_type, is_static, enum_values[] }

export const attrStore = {
  attrs:  [],
  lastId: 0,

  load() {
    try {
      const raw = localStorage.getItem("igm-attrs");
      if (!raw) return;
      const data  = JSON.parse(raw);
      this.attrs  = data.attrs  ?? [];
      this.lastId = data.lastId ?? 0;
    } catch (e) {
      console.warn("Error al cargar atributos globales:", e);
    }
  },

  _save() {
    localStorage.setItem("igm-attrs", JSON.stringify({ lastId: this.lastId, attrs: this.attrs }));
  },

  add({ key, name, data_type, is_static, enum_values = [] }) {
    this.lastId++;
    const attr = {
      id:          this.lastId,
      key,
      name,
      data_type,
      is_static:   !!is_static,
      enum_values: [...enum_values],
    };
    this.attrs.push(attr);
    this._save();
    return attr;
  },

  remove(id) {
    const idx = this.attrs.findIndex(a => a.id === id);
    if (idx === -1) return false;
    this.attrs.splice(idx, 1);
    this._save();
    return true;
  },

  update(id, { name, data_type, is_static, enum_values }) {
    const attr = this.attrs.find(a => a.id === id);
    if (!attr) return false;
    if (name        !== undefined) attr.name        = name;
    if (data_type   !== undefined) attr.data_type   = data_type;
    if (is_static   !== undefined) attr.is_static   = !!is_static;
    if (enum_values !== undefined) attr.enum_values = [...enum_values];
    this._save();
    return true;
  },
};
