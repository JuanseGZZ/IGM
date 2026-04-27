// ── Estado global ─────────────────────────────────────────────────────────────
const State = {
  categories: [],   // lista plana de CategoryOut
  attributes: [],   // lista de AttributeOut
  catById:    {},   // {id: CategoryOut} — el frontend arma el arbol desde aqui
  roots:      [],   // categorias sin padre
};

// ── Helpers internos ──────────────────────────────────────────────────────────
function _buildTree(cats) {
  const byId = {};
  cats.forEach(c => byId[c.id] = { ...c, _children: [], _products: [] });
  const roots = [];
  cats.forEach(c => {
    if (!c.father_id) roots.push(byId[c.id]);
    else if (byId[c.father_id]) byId[c.father_id]._children.push(byId[c.id]);
  });
  return { byId, roots };
}

async function _withImpact(phase1Call, phase2Call) {
  const data = await phase1Call();
  if (data.status !== 'impact_pending') return data;

  const resolution = await Render.impactModal(data.impact, data.message, data.context);
  if (!resolution) return null;

  const data2 = await phase2Call(resolution);
  if (data2.status === 'impact_pending') {
    Animations.toast('La resolución no cubre todos los productos impactados.', 'warning');
    return null;
  }
  return data2;
}

// ── Service ───────────────────────────────────────────────────────────────────
const Service = {

  async loadAll() {
    const [cats, attrs] = await Promise.all([API.categories(), API.attributes()]);
    State.categories = cats;
    State.attributes = attrs;
    const { byId, roots } = _buildTree(cats);
    State.catById = byId;
    State.roots = roots;
  },

  // ── Categoria — padre ─────────────────────────────────────────────────────

  async changeFather(catId, newFatherId) {
    const body = { new_father_id: newFatherId };
    return _withImpact(
      ()           => API.changeFather(catId, body),
      (resolution) => API.changeFather(catId, { ...body, resolution }),
    );
  },

  async removeFather(catId) {
    const body = { new_father_id: null };
    return _withImpact(
      ()           => API.changeFather(catId, body),
      (resolution) => API.changeFather(catId, { ...body, resolution }),
    );
  },

  // ── Categoria — atributos ─────────────────────────────────────────────────

  async addAttributeToCategory(catId, attrId) {
    return _withImpact(
      ()           => API.addCatAttribute(catId, attrId, {}),
      (resolution) => API.addCatAttribute(catId, attrId, { resolution }),
    );
  },

  async removeAttributeFromCategory(catId, attrId) {
    return _withImpact(
      ()           => API.removeCatAttribute(catId, attrId, {}),
      (resolution) => API.removeCatAttribute(catId, attrId, { resolution }),
    );
  },

  // ── Producto — categoria ──────────────────────────────────────────────────

  async changeProductCategory(prodId, newCatId) {
    const phase1 = await API.changeProductCat(prodId, newCatId, {});
    if (phase1.status !== 'impact_pending') return phase1;

    const resolution = await Render.e6Modal(phase1.to_add, phase1.to_remove, phase1.message);
    if (!resolution) return null;

    const phase2 = await API.changeProductCat(prodId, newCatId, { resolution });
    if (phase2.status === 'impact_pending') {
      Animations.toast('Faltan implementaciones requeridas.', 'warning');
      return null;
    }
    return phase2;
  },

  // ── CRUD ──────────────────────────────────────────────────────────────────

  async createCategory(body)  { return API.createCategory(body); },
  async createAttribute(body) { return API.createAttribute(body); },
  async createProduct(body)   { return API.createProduct(body); },

  async deleteCategory(id)  { return API.deleteCategory(id); },
  async deleteAttribute(id) { return API.deleteAttribute(id); },
  async deleteProduct(id)   { return API.deleteProduct(id); },

  async addVariant(prodId, impls)  { return API.addVariant(prodId, { attribute_implementations: impls }); },
  async removeVariant(prodId, varId) { return API.removeVariant(prodId, varId); },
};
