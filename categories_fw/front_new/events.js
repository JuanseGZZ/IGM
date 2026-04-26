const Events = {

  async init() {
    Animations.init();
    await this.refresh();
    Render.placeholder();
  },

  async refresh() {
    await Service.loadAll();
    Render.tree();
  },

  // ── Selección ─────────────────────────────────────────────────────────────

  selectCategory(catId) {
    document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`.tree-item[data-id="${catId}"]`)?.classList.add('active');
    const cat = State.catById[catId];
    if (cat) Render.categoryDetail(cat);
  },

  async selectProduct(prodId) {
    try {
      const prod = await API.product(prodId);
      Render.productDetail(prod);
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  async loadCategoryChildren(cat) {
    const products = cat._children?.length ? [] : await API.products(cat.id).catch(() => []);
    Render.categoryChildren(cat, products);
  },

  // ── Categoria — cambio de padre ───────────────────────────────────────────

  openChangeFather(catId) {
    const cat = State.catById[catId];
    const options = State.categories
      .filter(c => c.id !== catId && c.father_id !== catId)
      .map(c => `<option value="${c.id}" ${c.id === cat.father_id ? 'selected' : ''}>${c.name}</option>`)
      .join('');

    Render.formModal('Cambiar padre', `
      <div class="mb-3">
        <label class="form-label">Nueva categoría padre</label>
        <select class="form-select" id="new-father-sel">
          <option value="">— Sin padre (raíz) —</option>
          ${options}
        </select>
      </div>`, () => {
        const val = document.getElementById('new-father-sel').value;
        const newFatherId = val ? parseInt(val) : null;
        Events._doChangeFather(catId, newFatherId);
        return true;
    });
  },

  async _doChangeFather(catId, newFatherId) {
    try {
      const res = await Service.changeFather(catId, newFatherId);
      if (res) { Animations.toast('Padre actualizado.', 'success'); await this.refresh(); this.selectCategory(catId); }
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  async removeFather(catId) {
    try {
      const res = await Service.removeFather(catId);
      if (res) { Animations.toast('Padre eliminado.', 'success'); await this.refresh(); this.selectCategory(catId); }
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  // ── Categoria — atributos ─────────────────────────────────────────────────

  async addAttribute(catId, attrId) {
    try {
      const res = await Service.addAttributeToCategory(catId, attrId);
      if (res) { Animations.toast('Atributo agregado.', 'success'); await this.refresh(); this.selectCategory(catId); }
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  async removeAttribute(catId, attrId) {
    try {
      const res = await Service.removeAttributeFromCategory(catId, attrId);
      if (res) { Animations.toast('Atributo quitado.', 'success'); await this.refresh(); this.selectCategory(catId); }
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  // ── Producto — cambio de categoria ────────────────────────────────────────

  openChangeCategory(prodId) {
    const leafCats = State.categories.filter(c => !c._children?.length);
    const options  = leafCats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    Render.formModal('Cambiar categoría del producto', `
      <div class="mb-3">
        <label class="form-label">Nueva categoría</label>
        <select class="form-select" id="new-cat-sel">${options}</select>
      </div>`, () => {
        const newCatId = parseInt(document.getElementById('new-cat-sel').value);
        Events._doChangeProductCategory(prodId, newCatId);
        return true;
    });
  },

  async _doChangeProductCategory(prodId, newCatId) {
    try {
      const res = await Service.changeProductCategory(prodId, newCatId);
      if (res) { Animations.toast('Categoría actualizada.', 'success'); await this.selectProduct(prodId); }
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  // ── Variantes ─────────────────────────────────────────────────────────────

  async openAddVariant(prodId) {
    const prod = await API.product(prodId).catch(() => null);
    if (!prod) return;
    // Los attrs dinamicos requeridos los saca el backend; en el front usamos los de la cat
    const catAttrs = (State.catById[prod.category_id]?.attributes || []).filter(a => !a.is_static);
    if (!catAttrs.length) { Animations.toast('Esta categoría no tiene atributos dinámicos.', 'info'); return; }

    const inputs = catAttrs.map(a => `
      <div class="mb-2">
        <label class="form-label small mb-1">${a.name} <span class="text-muted">[${a.key}]</span></label>
        ${a.data_type === 'enum'
          ? `<select class="form-select form-select-sm" id="var-${a.id}">
              ${(a.enum_values || []).map(v => `<option>${v}</option>`).join('')}
             </select>`
          : `<input type="${a.data_type === 'number' ? 'number' : 'text'}"
                    class="form-control form-control-sm" id="var-${a.id}" placeholder="${a.name}">`}
      </div>`).join('');

    Render.formModal('Agregar variante', inputs, () => {
      const impls = catAttrs.map(a => ({
        attr_id: a.id,
        value:   document.getElementById(`var-${a.id}`)?.value || '',
      }));
      Events._doAddVariant(prodId, impls);
      return true;
    });
  },

  async _doAddVariant(prodId, impls) {
    try {
      await Service.addVariant(prodId, impls);
      Animations.toast('Variante agregada.', 'success');
      await this.selectProduct(prodId);
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  async removeVariant(prodId, varId) {
    try {
      await Service.removeVariant(prodId, varId);
      Animations.toast('Variante eliminada.', 'success');
      await this.selectProduct(prodId);
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  // ── CRUD — crear entidades ────────────────────────────────────────────────

  openCreateCategory() {
    const catOptions = State.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    const attrOptions = State.attributes.map(a =>
      `<option value="${a.id}">${a.name} [${a.key}] (${a.is_static ? 'estático' : 'dinámico'})</option>`
    ).join('');

    Render.formModal('Nueva categoría', `
      <div class="mb-3">
        <label class="form-label">Nombre <span class="text-danger">*</span></label>
        <input class="form-control" id="cc-name" placeholder="Nombre de la categoría">
      </div>
      <div class="mb-3">
        <label class="form-label">Padre (opcional)</label>
        <select class="form-select" id="cc-father">
          <option value="">— Sin padre (raíz) —</option>
          ${catOptions}
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Atributos iniciales</label>
        <select multiple class="form-select" id="cc-attrs" size="4">${attrOptions}</select>
        <small class="text-muted">Ctrl+click para seleccionar varios</small>
      </div>`, () => {
        const name = document.getElementById('cc-name').value.trim();
        if (!name) { Animations.toast('El nombre es requerido.', 'warning'); return false; }
        const fatherVal = document.getElementById('cc-father').value;
        const attrSel   = [...document.getElementById('cc-attrs').selectedOptions].map(o => parseInt(o.value));
        Events._doCreateCategory({ name, father_id: fatherVal ? parseInt(fatherVal) : null, attribute_ids: attrSel });
        return true;
    });
  },

  async _doCreateCategory(body) {
    try {
      await Service.createCategory(body);
      Animations.toast('Categoría creada.', 'success');
      await this.refresh();
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  openCreateAttribute() {
    Render.formModal('Nuevo atributo', `
      <div class="mb-3">
        <label class="form-label">Key (identificador único) <span class="text-danger">*</span></label>
        <input class="form-control" id="ca-key" placeholder="ej: color, talle">
      </div>
      <div class="mb-3">
        <label class="form-label">Nombre visible <span class="text-danger">*</span></label>
        <input class="form-control" id="ca-name" placeholder="ej: Color, Talle">
      </div>
      <div class="mb-3">
        <label class="form-label">Tipo de dato</label>
        <select class="form-select" id="ca-type" onchange="Events._onAttrTypeChange()">
          <option value="text">text</option>
          <option value="number">number</option>
          <option value="boolean">boolean</option>
          <option value="enum">enum</option>
        </select>
      </div>
      <div class="mb-3" id="ca-enum-section" style="display:none">
        <label class="form-label">Valores posibles (uno por línea)</label>
        <textarea class="form-control" id="ca-enum-vals" rows="3" placeholder="rojo&#10;azul&#10;verde"></textarea>
      </div>
      <div class="form-check mb-3">
        <input class="form-check-input" type="checkbox" id="ca-static">
        <label class="form-check-label" for="ca-static">Estático (info de producto)</label>
        <small class="d-block text-muted">Dinámico = opción de variante</small>
      </div>`, () => {
        const key  = document.getElementById('ca-key').value.trim();
        const name = document.getElementById('ca-name').value.trim();
        if (!key || !name) { Animations.toast('Key y nombre son requeridos.', 'warning'); return false; }
        const data_type  = document.getElementById('ca-type').value;
        const is_static  = document.getElementById('ca-static').checked;
        const enumRaw    = document.getElementById('ca-enum-vals')?.value || '';
        const enum_values = data_type === 'enum' ? enumRaw.split('\n').map(v => v.trim()).filter(Boolean) : [];
        Events._doCreateAttribute({ key, name, data_type, is_static, enum_values });
        return true;
    });
  },

  _onAttrTypeChange() {
    const t = document.getElementById('ca-type').value;
    document.getElementById('ca-enum-section').style.display = t === 'enum' ? '' : 'none';
  },

  async _doCreateAttribute(body) {
    try {
      await Service.createAttribute(body);
      Animations.toast('Atributo creado.', 'success');
      await this.refresh();
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  openCreateProduct(preCatId = null) {
    const leafCats = State.categories.filter(c => !c._children?.length);
    const options  = leafCats.map(c =>
      `<option value="${c.id}" ${c.id === preCatId ? 'selected' : ''}>${c.name}</option>`
    ).join('');

    Render.formModal('Nuevo producto', `
      <div class="row g-2 mb-3">
        <div class="col-md-6">
          <label class="form-label">Código <span class="text-danger">*</span></label>
          <input class="form-control" id="cp-code" placeholder="SKU001">
        </div>
        <div class="col-md-6">
          <label class="form-label">Precio <span class="text-danger">*</span></label>
          <input type="number" step="0.01" class="form-control" id="cp-price" placeholder="0.00">
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Título <span class="text-danger">*</span></label>
        <input class="form-control" id="cp-title" placeholder="Nombre del producto">
      </div>
      <div class="row g-2 mb-3">
        <div class="col-md-6">
          <label class="form-label">Marca</label>
          <input class="form-control" id="cp-brand" placeholder="Marca">
        </div>
        <div class="col-md-6">
          <label class="form-label">Categoría <span class="text-danger">*</span></label>
          <select class="form-select" id="cp-cat">${options}</select>
        </div>
      </div>
      <div class="mb-3">
        <label class="form-label">Descripción</label>
        <textarea class="form-control" id="cp-desc" rows="2"></textarea>
      </div>`, () => {
        const code  = document.getElementById('cp-code').value.trim();
        const title = document.getElementById('cp-title').value.trim();
        const price = parseFloat(document.getElementById('cp-price').value);
        if (!code || !title || isNaN(price)) { Animations.toast('Código, título y precio son requeridos.', 'warning'); return false; }
        Events._doCreateProduct({
          code, title, price,
          brand:       document.getElementById('cp-brand').value.trim(),
          description: document.getElementById('cp-desc').value.trim(),
          category_id: parseInt(document.getElementById('cp-cat').value),
        });
        return true;
    });
  },

  async _doCreateProduct(body) {
    try {
      const prod = await Service.createProduct(body);
      Animations.toast('Producto creado.', 'success');
      await this.refresh();
      Render.productDetail(prod);
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  // ── Eliminar ──────────────────────────────────────────────────────────────

  async deleteCategory(catId) {
    if (!confirm('¿Eliminar esta categoría? Se eliminan todas sus relaciones.')) return;
    try {
      await Service.deleteCategory(catId);
      Animations.toast('Categoría eliminada.', 'success');
      Render.placeholder();
      await this.refresh();
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },

  async deleteProduct(prodId) {
    if (!confirm('¿Eliminar este producto?')) return;
    try {
      await Service.deleteProduct(prodId);
      Animations.toast('Producto eliminado.', 'success');
      Render.placeholder();
      await this.refresh();
    } catch(e) { Animations.toast(e.message, 'danger'); }
  },
};

document.addEventListener('DOMContentLoaded', () => Events.init());
