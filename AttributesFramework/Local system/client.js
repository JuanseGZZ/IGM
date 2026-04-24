import {
  Attribute, AttributeImplementation,
  Category, Variant, Product, DataTypes,
} from './models.js';

// ─── Registry ─────────────────────────────────────────────────────────────────
// Todas las instancias de modelos viven acá.
let _uid = 1;
const uid = () => _uid++;

const R = {
  attrs: new Map(),  // id → Attribute
  cats:  new Map(),  // id → Category
  prods: new Map(),  // id → Product
  vars:  new Map(),  // id → Variant
};
const varOwner = new Map(); // Variant → Product

// ─── Log ──────────────────────────────────────────────────────────────────────
function log(msg, type = 'info') {
  const colors = { info: '#212529', success: '#198754', warning: '#b45309', error: '#dc3545' };
  const icons  = { info: '→', success: '✓', warning: '⚠', error: '✗' };
  const div = document.createElement('div');
  div.className = 'log-entry';
  div.innerHTML = `<span style="color:${colors[type]};font-weight:700">${icons[type]}</span> <span style="color:${colors[type]}">${msg}</span>`;
  document.getElementById('log').prepend(div);
}

// ─── Tabs ─────────────────────────────────────────────────────────────────────
window.switchTab = (key, btn) => {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('on'));
  document.querySelectorAll('.tb').forEach(b => b.classList.remove('on'));
  document.getElementById('panel-' + key).classList.add('on');
  btn.classList.add('on');
};

// ─── Render ───────────────────────────────────────────────────────────────────
function renderAll() {
  renderAttrs(); renderCats(); renderProds(); renderVars();
  document.getElementById('node-count').textContent =
    `${R.attrs.size}a · ${R.cats.size}c · ${R.prods.size}p · ${R.vars.size}v`;
  refreshGraph();
}

function renderAttrs() {
  const el = document.getElementById('list-a');
  if (!R.attrs.size) { el.innerHTML = '<p class="text-muted" style="font-size:11px">Sin atributos.</p>'; return; }
  el.innerHTML = [...R.attrs.values()].map(a => `
    <div class="ec ec-a">
      <div class="ec-body">
        <b>${h(a.name)}
          <span class="badge bg-primary" style="font-size:9px">${a.data_type}</span>
          ${a.is_static ? '<span class="badge bg-secondary" style="font-size:9px">estático</span>' : ''}
        </b>
        <small>${h(a.key)}${a.enum_values.length ? ' · ' + a.enum_values.join(', ') : ''}</small>
      </div>
      <div class="ec-acts">
        <button style="color:#0d6efd;border-color:#0d6efd" onclick="openModal('attr',${a.id})">✏</button>
        <button style="color:#dc3545;border-color:#dc3545" onclick="delAttr(${a.id})">🗑</button>
      </div>
    </div>`).join('');
}

function renderCats() {
  const el = document.getElementById('list-c');
  if (!R.cats.size) { el.innerHTML = '<p class="text-muted" style="font-size:11px">Sin categorías.</p>'; return; }
  el.innerHTML = [...R.cats.values()].map(c => {
    const ownAttrs = c.attributes.map(a => `${a.name}(${a.is_static ? 'est' : 'din'})`).join(', ');
    return `
    <div class="ec ec-c">
      <div class="ec-body">
        <b>${h(c.name)}</b>
        <small>${c.father_categorie ? '↑ ' + h(c.father_categorie.name) : 'Raíz'} · ${c.subcategories.length} sub · ${c.products.length} prod</small>
        ${ownAttrs ? `<small style="color:#198754">${ownAttrs}</small>` : ''}
      </div>
      <div class="ec-acts">
        <button style="color:#198754;border-color:#198754" onclick="openModal('cat',${c.id})">✏</button>
        <button style="color:#dc3545;border-color:#dc3545" onclick="delCat(${c.id})">🗑</button>
      </div>
    </div>`;
  }).join('');
}

function renderProds() {
  const el = document.getElementById('list-p');
  if (!R.prods.size) { el.innerHTML = '<p class="text-muted" style="font-size:11px">Sin productos.</p>'; return; }
  el.innerHTML = [...R.prods.values()].map(p => `
    <div class="ec ec-p">
      <div class="ec-body">
        <b>${h(p.title)} <span class="badge bg-warning text-dark" style="font-size:9px">${h(p.code)}</span></b>
        <small>${p.category ? h(p.category.name) : '—'} · $${p.price} · ${p.variants.length} var.</small>
      </div>
      <div class="ec-acts">
        <button style="color:#fd7e14;border-color:#fd7e14" onclick="openModal('prod',${p.id})">✏</button>
        <button style="color:#dc3545;border-color:#dc3545" onclick="delProd(${p.id})">🗑</button>
      </div>
    </div>`).join('');
}

function renderVars() {
  const el = document.getElementById('list-v');
  if (!R.vars.size) { el.innerHTML = '<p class="text-muted" style="font-size:11px">Sin variantes.</p>'; return; }
  el.innerHTML = [...R.vars.values()].map(v => {
    const prod = varOwner.get(v);
    const impls = v.attribute_implementations.map(ai => `${ai.attribute.name}=${ai.value}`).join(', ');
    return `
    <div class="ec ec-v">
      <div class="ec-body">
        <b>Var #${v.id}</b>
        <small>${prod ? h(prod.title) : '—'}${impls ? ' · ' + impls : ''}</small>
      </div>
      <div class="ec-acts">
        <button style="color:#dc3545;border-color:#dc3545" onclick="delVar(${v.id})">🗑</button>
      </div>
    </div>`;
  }).join('');
}

// ─── Delete ───────────────────────────────────────────────────────────────────
window.delAttr = id => {
  const a = R.attrs.get(id);
  if (!confirm(`¿Eliminar atributo "${a.name}"?`)) return;
  const users = [...R.cats.values()].filter(c => c._attribute_keys.has(a.key)).map(c => c.name);
  if (users.length) { log(`"${a.name}" está en uso por: ${users.join(', ')}. Quítalo primero.`, 'error'); return; }
  R.attrs.delete(id);
  log(`Atributo "${a.name}" eliminado.`, 'success');
  renderAll();
};

window.delCat = id => {
  const c = R.cats.get(id);
  if (!confirm(`¿Eliminar categoría "${c.name}"?`)) return;
  if (c.products.length || c.subcategories.length) {
    log(`"${c.name}" tiene ${c.products.length} productos y ${c.subcategories.length} subcategorías. Vacíala primero.`, 'error');
    return;
  }
  if (c.father_categorie) {
    // Use model method to detach properly
    const result = c.father_categorie.delCategorie(c, 0);
    if (Array.isArray(result) && result.length > 0) {
      log(`Impacto al eliminar "${c.name}": ${result.length} productos afectados.`, 'warning');
    }
  }
  R.cats.delete(id);
  log(`Categoría "${c.name}" eliminada.`, 'success');
  renderAll();
};

window.delProd = id => {
  const p = R.prods.get(id);
  if (!confirm(`¿Eliminar producto "${p.title}"?`)) return;
  p.category.delProduct(p);
  p.variants.forEach(v => { R.vars.delete(v.id); varOwner.delete(v); });
  R.prods.delete(id);
  log(`Producto "${p.title}" eliminado.`, 'success');
  renderAll();
};

window.delVar = id => {
  const v = R.vars.get(id);
  const prod = varOwner.get(v);
  if (!confirm(`¿Eliminar variante #${id}?`)) return;
  if (prod) prod.delVariant(id);
  R.vars.delete(id);
  varOwner.delete(v);
  log(`Variante #${id} eliminada.`, 'success');
  renderAll();
};

// ─── Modal ────────────────────────────────────────────────────────────────────
let _ctx = {};
let _bsMain, _bsImpact;

window.openModal = (type, id = null) => {
  _ctx = { type, id };
  const titles = { attr: 'Atributo', cat: 'Categoría', prod: 'Producto', var: 'Variante' };
  document.getElementById('modal-title').textContent = (id ? 'Editar' : 'Nuevo') + ' ' + titles[type];
  document.getElementById('modal-body').innerHTML = buildForm(type, id);
  if (!_bsMain) _bsMain = new bootstrap.Modal(document.getElementById('mainModal'));
  _bsMain.show();
  if (type === 'attr') {
    syncEnumSection();
    document.getElementById('f-dt').addEventListener('change', syncEnumSection);
  }
};

function syncEnumSection() {
  const s = document.getElementById('f-enum-sec');
  if (s) s.style.display = document.getElementById('f-dt').value === 'enum' ? '' : 'none';
}

// ─── Form builders ────────────────────────────────────────────────────────────
function buildForm(type, id) {
  if (type === 'attr') {
    const a = id ? R.attrs.get(id) : null;
    const disabled = a ? 'disabled' : '';
    return `<div class="row g-2">
      <div class="col-6"><label class="form-label">Key *</label>
        <input id="f-key" class="form-control form-control-sm" value="${ea(a?.key??'')}" placeholder="color…" ${disabled}></div>
      <div class="col-6"><label class="form-label">Nombre *</label>
        <input id="f-name" class="form-control form-control-sm" value="${ea(a?.name??'')}" placeholder="Color…"></div>
      <div class="col-6"><label class="form-label">Tipo *</label>
        <select id="f-dt" class="form-select form-select-sm" ${disabled}>
          ${DataTypes.map(t=>`<option value="${t}"${a?.data_type===t?' selected':''}>${t}</option>`).join('')}
        </select></div>
      <div class="col-6 d-flex align-items-end pb-1">
        <div class="form-check">
          <input id="f-static" class="form-check-input" type="checkbox"${a?.is_static?' checked':''} ${disabled}>
          <label class="form-check-label" for="f-static" style="font-size:12px">Estático (valor por producto)</label>
        </div></div>
      <div class="col-12" id="f-enum-sec" style="display:none">
        <label class="form-label">Valores enum <small class="text-muted">(coma separados)</small></label>
        <input id="f-enum" class="form-control form-control-sm" value="${ea((a?.enum_values??[]).join(', '))}" placeholder="rojo, azul, verde">
      </div>
      ${a ? '<div class="col-12"><p class="text-muted mb-0" style="font-size:11px">⚠ Key, tipo y staticidad son inmutables una vez creado el atributo.</p></div>' : ''}
    </div>`;
  }

  if (type === 'cat') {
    const c = id ? R.cats.get(id) : null;
    // Exclude self and all descendants from parent options
    const desc = new Set();
    if (c) { const walk = x => { desc.add(x.id); x.subcategories.forEach(walk); }; walk(c); }
    const catOpts = [...R.cats.values()].filter(x => !desc.has(x.id))
      .map(x => `<option value="${x.id}"${c?.father_categorie===x?' selected':''}>${h(x.name)}</option>`).join('');
    const attrOpts = [...R.attrs.values()]
      .map(a => `<option value="${a.id}"${c?.attributes.includes(a)?' selected':''}>${h(a.name)} (${a.data_type}${a.is_static?' · est':''})</option>`).join('');
    return `<div class="row g-2">
      <div class="col-12"><label class="form-label">Nombre *</label>
        <input id="f-name" class="form-control form-control-sm" value="${ea(c?.name??'')}" placeholder="Indumentaria…"></div>
      <div class="col-12"><label class="form-label">Categoría padre</label>
        <select id="f-father" class="form-select form-select-sm">
          <option value="">Sin padre (raíz)</option>${catOpts}
        </select></div>
      <div class="col-12">
        <label class="form-label">Atributos <small class="text-muted">(Ctrl+click para varios)</small></label>
        <select id="f-attr-ids" class="form-select form-select-sm" multiple size="5">${attrOpts}</select>
        <p class="text-muted mb-0 mt-1" style="font-size:11px">
          Si hay productos en el árbol con variantes, se abrirá un segundo paso para pedir los valores de impacto.
        </p>
      </div>
    </div>`;
  }

  if (type === 'prod') {
    const p = id ? R.prods.get(id) : null;
    const leafCats = [...R.cats.values()].filter(c => c.subcategories.length === 0);
    const catOpts = leafCats.map(c => `<option value="${c.id}"${p?.category===c?' selected':''}>${h(c.name)}</option>`).join('');
    return `<div class="row g-2">
      <div class="col-4"><label class="form-label">Código *</label>
        <input id="f-code" class="form-control form-control-sm" value="${ea(p?.code??'')}" placeholder="SKU-001"></div>
      <div class="col-4"><label class="form-label">Precio</label>
        <input id="f-price" type="number" step="0.01" class="form-control form-control-sm" value="${p?.price??0}"></div>
      <div class="col-4"><label class="form-label">Marca</label>
        <input id="f-brand" class="form-control form-control-sm" value="${ea(p?.brand??'')}"></div>
      <div class="col-12"><label class="form-label">Título *</label>
        <input id="f-title" class="form-control form-control-sm" value="${ea(p?.title??'')}" placeholder="Nombre del producto"></div>
      <div class="col-12"><label class="form-label">Descripción</label>
        <textarea id="f-desc" class="form-control form-control-sm" rows="2">${h(p?.description??'')}</textarea></div>
      <div class="col-12"><label class="form-label">Categoría * <small class="text-muted">(solo hojas — sin subcategorías)</small></label>
        <select id="f-cat" class="form-select form-select-sm" ${p?'disabled':''}>
          <option value="">Seleccionar…</option>${catOpts}
        </select></div>
    </div>`;
  }

  if (type === 'var') {
    const prodOpts = [...R.prods.values()].map(p =>
      `<option value="${p.id}">${h(p.title)} (${h(p.code)})</option>`).join('');
    return `<div class="row g-2">
      <div class="col-12"><label class="form-label">Producto *</label>
        <select id="f-prod" class="form-select form-select-sm" onchange="loadVarFields(this.value)">
          <option value="">Seleccionar producto…</option>${prodOpts}
        </select></div>
      <div id="var-fields"></div>
    </div>`;
  }
  return '';
}

// Carga los campos de implementación para la variante según el producto seleccionado
window.loadVarFields = prodId => {
  const el = document.getElementById('var-fields');
  if (!prodId) { el.innerHTML = ''; return; }
  const p = R.prods.get(parseInt(prodId));
  const needed = p.getNeededAtributesImplementations(false); // dinámicos
  if (!needed.size) {
    el.innerHTML = '<p class="text-muted mt-2 mb-0" style="font-size:11px">Este producto no tiene atributos dinámicos. No se necesitan implementaciones.</p>';
    return;
  }
  el.innerHTML = `<div class="mt-2"><label class="form-label">Implementaciones requeridas</label><div class="row g-2">
    ${[...needed].map(a => implField(`fi-${a.id}`, a, null)).join('')}
  </div></div>`;
};

// ─── Impl field helper ────────────────────────────────────────────────────────
function implField(fieldId, attr, val) {
  if (attr.data_type === 'boolean') return `
    <div class="col-6"><label class="form-label">${h(attr.name)}</label>
      <select id="${fieldId}" class="form-select form-select-sm">
        <option value="">— elegir —</option>
        <option value="true"${val===true?' selected':''}>true</option>
        <option value="false"${val===false?' selected':''}>false</option>
      </select></div>`;
  if (attr.data_type === 'enum') return `
    <div class="col-6"><label class="form-label">${h(attr.name)}</label>
      <select id="${fieldId}" class="form-select form-select-sm">
        <option value="">— elegir —</option>
        ${attr.enum_values.map(v => `<option${val===v?' selected':''}>${h(v)}</option>`).join('')}
      </select></div>`;
  return `
    <div class="col-6"><label class="form-label">${h(attr.name)} (${attr.data_type})</label>
      <input id="${fieldId}" type="${attr.data_type==='number'?'number':'text'}" class="form-control form-control-sm" value="${ea(String(val??''))}"></div>`;
}

function readField(fieldId, attr) {
  const el = document.getElementById(fieldId);
  if (!el || el.value === '') return undefined;
  if (attr.data_type === 'number') return parseFloat(el.value);
  if (attr.data_type === 'boolean') return el.value === 'true';
  return el.value;
}

// ─── Save entity ──────────────────────────────────────────────────────────────
window.saveEntity = () => {
  try {
    const { type, id } = _ctx;
    if (type === 'attr') saveAttr(id);
    else if (type === 'cat') saveCat(id);
    else if (type === 'prod') saveProd(id);
    else if (type === 'var') saveVar();
    _bsMain.hide();
    renderAll();
  } catch(e) {
    log(e.message, 'error');
    alert('Error: ' + e.message);
  }
};

function saveAttr(id) {
  const name = document.getElementById('f-name').value.trim();
  if (!name) throw new Error('Nombre es obligatorio.');

  if (id) {
    const a = R.attrs.get(id);
    a.name = name;
    if (a.data_type === 'enum') {
      const newVals = (document.getElementById('f-enum')?.value ?? '').split(',').map(s => s.trim()).filter(Boolean);
      for (const v of newVals) {
        if (!a.enum_values.includes(v)) {
          try { a.addEnumValue(v); log(`Valor enum "${v}" agregado a "${a.name}".`, 'info'); }
          catch(e) { log(e.message, 'warning'); }
        }
      }
    }
    log(`Atributo "${name}" actualizado.`, 'success');
  } else {
    const key = document.getElementById('f-key').value.trim();
    const data_type = document.getElementById('f-dt').value;
    const is_static = document.getElementById('f-static').checked;
    if (!key) throw new Error('Key es obligatorio.');
    const eid = uid();
    const a = new Attribute({ id: eid, key, name, data_type, is_static });
    if (data_type === 'enum') {
      for (const v of (document.getElementById('f-enum')?.value ?? '').split(',').map(s => s.trim()).filter(Boolean))
        a.addEnumValue(v);
    }
    R.attrs.set(eid, a);
    log(`Atributo "${name}" [${data_type}${is_static?' estático':''}] creado (id=${eid}).`, 'success');
  }
}

function saveCat(id) {
  const name = document.getElementById('f-name').value.trim();
  if (!name) throw new Error('Nombre es obligatorio.');
  const fRaw = document.getElementById('f-father').value;
  const newFather = fRaw ? R.cats.get(parseInt(fRaw)) : null;
  const selIds = [...document.getElementById('f-attr-ids').selectedOptions].map(o => parseInt(o.value));
  const selAttrs = selIds.map(id => R.attrs.get(id));

  let cat;
  if (id) {
    cat = R.cats.get(id);
    cat.name = name;
    log(`Categoría "${name}" renombrada.`, 'info');

    // Cambio de padre
    if (newFather !== cat.father_categorie) {
      if (newFather) {
        try {
          const res = cat.changeCategorieFather(newFather, {}, 0);
          if (res && typeof res === 'object' && !Array.isArray(res) && Object.keys(res).length > 0) {
            log(`⚠ changeCategorieFather requiere implementaciones adicionales. Ver consola.`, 'warning');
            console.warn('Impacto changeCategorieFather:', res);
          } else {
            log(`"${name}" movida a padre "${newFather.name}".`, 'success');
          }
        } catch(e) { log(e.message, 'error'); }
      }
    }

    // Atributos: agregar los nuevos, quitar los deseleccionados
    const currentKeys = new Set(cat.attributes.map(a => a.key));
    const selectedKeys = new Set(selAttrs.map(a => a.key));

    // Quitar
    for (const a of [...cat.attributes]) {
      if (!selectedKeys.has(a.key)) {
        const impact = cat.delAttributeCheckFamilyImpact(a);
        if (impact.length > 0) {
          const opt = confirm(
            `Quitar "${a.name}" de "${cat.name}" afecta ${impact.length} producto(s).\n` +
            `OK = eliminar implementaciones   Cancelar = inyectar atributo en productos`
          ) ? 1 : 2;
          cat.delAttribute(a, opt);
          log(`Atributo "${a.name}" quitado (opción ${opt === 1 ? 'eliminar impls' : 'inyectar en productos'}).`, 'warning');
        } else {
          cat.delAttribute(a, 0);
          log(`Atributo "${a.name}" quitado de "${cat.name}".`, 'success');
        }
      }
    }

    // Agregar
    for (const a of selAttrs) {
      if (currentKeys.has(a.key)) continue;
      const result = a.is_static
        ? cat.addStaticAttribute(a, [])
        : cat.addDinamicAttribute(a, []);

      if (Array.isArray(result) && result.length > 0 && result[0]?.code !== undefined) {
        // Hay impacto — abrir modal de impacto y cortar el flujo
        _bsMain.hide();
        openImpactModal(a, cat, result);
        return; // El resto lo maneja saveImpact()
      }
      log(`Atributo "${a.name}" asignado a "${cat.name}".`, 'success');
    }

  } else {
    // Nueva categoría
    const eid = uid();
    cat = new Category({ id: eid, name });
    R.cats.set(eid, cat);
    log(`Categoría "${name}" creada (id=${eid}).`, 'success');

    if (newFather) {
      try {
        cat.changeCategorieFather(newFather, {}, 0);
        log(`  → Padre: "${newFather.name}".`, 'info');
      } catch(e) { log('Error al asignar padre: ' + e.message, 'error'); }
    }

    // Agregar atributos (sin productos todavía, no habrá impacto)
    for (const a of selAttrs) {
      try {
        a.is_static ? cat.addStaticAttribute(a, []) : cat.addDinamicAttribute(a, []);
        log(`  → Atributo "${a.name}" asignado.`, 'info');
      } catch(e) { log(`  → Error con "${a.name}": ${e.message}`, 'error'); }
    }
  }
}

function saveProd(id) {
  const code = document.getElementById('f-code').value.trim();
  const title = document.getElementById('f-title').value.trim();
  const price = parseFloat(document.getElementById('f-price').value) || 0;
  const description = document.getElementById('f-desc').value.trim();
  const brand = document.getElementById('f-brand').value.trim();
  if (!code || !title) throw new Error('Código y Título son obligatorios.');

  if (id) {
    const p = R.prods.get(id);
    p.code = code; p.title = title; p.price = price;
    p.description = description; p.brand = brand;
    log(`Producto "${title}" actualizado.`, 'success');
  } else {
    const catRaw = document.getElementById('f-cat').value;
    if (!catRaw) throw new Error('Categoría es obligatoria.');
    const cat = R.cats.get(parseInt(catRaw));
    const eid = uid();
    const p = new Product({ id: eid, code, title, price, description, brand, category: cat });
    cat.addProduct(p);
    R.prods.set(eid, p);
    log(`Producto "${title}" creado en "${cat.name}" (id=${eid}).`, 'success');
  }
}

function saveVar() {
  const prodRaw = document.getElementById('f-prod').value;
  if (!prodRaw) throw new Error('Producto es obligatorio.');
  const p = R.prods.get(parseInt(prodRaw));
  const needed = p.getNeededAtributesImplementations(false);

  const impls = [...needed].map(a => {
    const val = readField(`fi-${a.id}`, a);
    if (val === undefined) throw new Error(`Falta el valor para "${a.name}".`);
    return new AttributeImplementation({ attribute: a, value: val });
  });

  const prevLen = p.variants.length;
  p.createVariantByImplementations(impls);
  if (p.variants.length === prevLen) throw new Error('No se pudo crear la variante. Revisá los valores.');

  const v = p.variants[p.variants.length - 1];
  v.id = uid();
  R.vars.set(v.id, v);
  varOwner.set(v, p);
  log(`Variante #${v.id} creada para "${p.title}": ${impls.map(i=>`${i.attribute.name}=${i.value}`).join(', ')}.`, 'success');
}

// ─── Impact modal ─────────────────────────────────────────────────────────────
// Se abre cuando addStaticAttribute / addDinamicAttribute devuelven una lista de productos afectados.

function openImpactModal(attr, cat, impactedProds) {
  _ctx.impactAttr = attr;
  _ctx.impactCat  = cat;
  _ctx.impactProds = impactedProds;

  const isStatic = attr.is_static;
  let html = `<div class="alert alert-warning py-2 mb-3" style="font-size:12px">
    El atributo <strong>${h(attr.name)}</strong> afecta a <strong>${impactedProds.length}</strong> producto(s) existentes.
    Completá los valores para poder aplicar la operación.
  </div><div class="row g-2">`;

  for (const prod of impactedProds) {
    if (isStatic) {
      html += `<div class="col-12 mt-1">
        <label class="form-label"><b>${h(prod.title)}</b> (${h(prod.code)})</label>
        ${implField(`imp-p${prod.id}`, attr, null)}
      </div>`;
    } else {
      html += `<div class="col-12 mt-1"><p class="mb-1" style="font-size:12px"><b>${h(prod.title)}</b></p>`;
      for (const v of prod.variants) {
        const varLabel = v.attribute_implementations.map(ai=>`${ai.attribute.name}=${ai.value}`).join(', ') || `#${v.id}`;
        html += implField(`imp-v${prod.id}-${v.id}`, attr, null)
          .replace(`<label class="form-label">`, `<label class="form-label"><span class="text-muted">[${h(varLabel)}]</span> `);
      }
      html += `</div>`;
    }
  }
  html += '</div>';

  document.getElementById('impact-title').textContent = `⚠ Impacto: valores para "${attr.name}"`;
  document.getElementById('impact-body').innerHTML = html;

  if (!_bsImpact) _bsImpact = new bootstrap.Modal(document.getElementById('impactModal'));
  _bsImpact.show();
  log(`Impacto detectado: ${impactedProds.length} producto(s) requieren valor para "${attr.name}".`, 'warning');
}

window.saveImpact = () => {
  const { impactAttr: attr, impactCat: cat, impactProds } = _ctx;
  try {
    let result;
    if (attr.is_static) {
      const implementations = impactProds.map(prod => {
        const val = readField(`imp-p${prod.id}`, attr);
        if (val === undefined) throw new Error(`Falta el valor para "${prod.title}".`);
        return { product_id: prod.id, value: val };
      });
      result = cat.addStaticAttribute(attr, implementations);
    } else {
      const pvi = impactProds.map(prod => ({
        product_id: prod.id,
        variants: prod.variants.map(v => {
          const val = readField(`imp-v${prod.id}-${v.id}`, attr);
          if (val === undefined) throw new Error(`Falta valor para una variante de "${prod.title}".`);
          return { variant_id: v.id, value: val };
        }),
      }));
      result = cat.addDinamicAttribute(attr, pvi);
    }

    // Si todavía devuelve productos es que algo falló
    if (Array.isArray(result) && result.length > 0 && result[0]?.code !== undefined)
      throw new Error('Valores inválidos según el modelo. Revisá los tipos.');

    _bsImpact.hide();
    log(`✓ Atributo "${attr.name}" aplicado a "${cat.name}" con implementaciones en ${impactProds.length} producto(s).`, 'success');
    renderAll();
  } catch(e) {
    log(e.message, 'error');
    alert('Error: ' + e.message);
  }
};

// ─── Cytoscape ────────────────────────────────────────────────────────────────
let cy;

document.addEventListener('DOMContentLoaded', () => {
  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [],
    style: [
      { selector: 'node', style: {
        label: 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
        'font-size': 10, color: '#fff', 'text-wrap': 'wrap', 'text-max-width': 88, 'font-weight': 'bold',
      }},
      { selector: 'node[type="attr"]',  style: { 'background-color': '#0d6efd', shape: 'ellipse', width: 80, height: 80 }},
      { selector: 'node[type="cat"]',   style: { 'background-color': '#198754', shape: 'round-rectangle', width: 112, height: 44 }},
      { selector: 'node[type="prod"]',  style: { 'background-color': '#fd7e14', shape: 'rectangle', width: 112, height: 44 }},
      { selector: 'node[type="var"]',   style: { 'background-color': '#6f42c1', shape: 'diamond', width: 82, height: 82 }},
      { selector: 'node:selected', style: { 'border-width': 3, 'border-color': '#212529' }},
      { selector: '.faded',         style: { opacity: 0.12 }},
      { selector: 'edge', style: {
        width: 1.5, 'line-color': '#adb5bd', 'target-arrow-color': '#adb5bd',
        'target-arrow-shape': 'triangle', 'curve-style': 'bezier',
        label: 'data(label)', 'font-size': 9, color: '#6c757d', 'text-rotation': 'autorotate',
        'text-background-color': '#fff', 'text-background-opacity': 0.85, 'text-background-padding': '2px',
      }},
      { selector: '.hidden', style: { display: 'none' }},
    ],
    layout: { name: 'dagre' },
  });

  cy.on('tap', 'node', e => showNodeDetail(e.target.data()));
  cy.on('tap', e => { if (e.target === cy) { cy.elements().removeClass('faded'); hideDetail(); }});

  loadSample();
  renderAll();
});

window.relayout = () =>
  cy.layout({ name: 'dagre', rankDir: 'TB', nodeSep: 55, rankSep: 75, edgeSep: 15 }).run();

function refreshGraph() {
  cy.elements().remove();
  const els = [];
  let ei = 0;
  const edge = (src, tgt, lbl) => ({ data: { id: `e${ei++}`, source: src, target: tgt, label: lbl }});

  for (const [id, a] of R.attrs)
    els.push({ data: { id: `a${id}`, label: `${a.name}\n[${a.data_type}]`, type: 'attr', eid: id }});

  for (const [id, c] of R.cats) {
    els.push({ data: { id: `c${id}`, label: c.name, type: 'cat', eid: id }});
    if (c.father_categorie)
      els.push(edge(`c${id}`, `c${c.father_categorie.id}`, 'subcateg.'));
    for (const a of c.attributes)
      els.push(edge(`c${id}`, `a${a.id}`, a.is_static ? 'attr.est.' : 'attr.din.'));
  }

  for (const [id, p] of R.prods) {
    els.push({ data: { id: `p${id}`, label: `${p.title}\n${p.code}`, type: 'prod', eid: id }});
    if (p.category) els.push(edge(`p${id}`, `c${p.category.id}`, 'en'));
    for (const ai of p.attributes_implementations)
      els.push(edge(`p${id}`, `a${ai.attribute.id}`, `=${ai.value}`));
    for (const a of p.attributes)   // atributos propios del producto (no de categoría)
      els.push(edge(`p${id}`, `a${a.id}`, 'propio'));
  }

  for (const [id, v] of R.vars) {
    els.push({ data: { id: `v${id}`, label: `Var #${id}`, type: 'var', eid: id }});
    const prod = varOwner.get(v);
    if (prod) els.push(edge(`p${prod.id}`, `v${id}`, 'variante'));
    for (const ai of v.attribute_implementations)
      els.push(edge(`v${id}`, `a${ai.attribute.id}`, `=${ai.value}`));
  }

  cy.add(els);
  applyFilter();
  relayout();
}

window.applyFilter = () => {
  if (!cy) return;
  cy.nodes('[type="attr"]').toggleClass('hidden', !document.getElementById('fa').checked);
  cy.nodes('[type="cat"]').toggleClass('hidden',  !document.getElementById('fc').checked);
  cy.nodes('[type="prod"]').toggleClass('hidden', !document.getElementById('fp').checked);
  cy.nodes('[type="var"]').toggleClass('hidden',  !document.getElementById('fv').checked);
  cy.edges().forEach(e => e.toggleClass('hidden', e.source().hasClass('hidden') || e.target().hasClass('hidden')));
};

// ─── Node detail ──────────────────────────────────────────────────────────────
function showNodeDetail(data) {
  const { type, eid } = data;
  let html = '';

  if (type === 'attr') {
    const a = R.attrs.get(eid);
    if (!a) return;
    const usedBy = [...R.cats.values()].filter(c => c._attribute_keys.has(a.key)).map(c => c.name);
    html = `<b>Atributo</b>: ${h(a.name)}
      <span class="badge bg-primary" style="font-size:10px">${a.data_type}</span>
      ${a.is_static ? '<span class="badge bg-secondary" style="font-size:10px">estático</span>' : ''}
      <br><small>key: <code>${h(a.key)}</code>
      ${a.enum_values.length ? '· valores: ' + a.enum_values.join(', ') : ''}</small>
      <br><small>Usado en categorías: ${usedBy.join(', ') || 'ninguna'}</small>`;

  } else if (type === 'cat') {
    const c = R.cats.get(eid);
    if (!c) return;
    const inherited = c.father_categorie ? c.father_categorie.getAttributes().map(a=>a.name).join(', ') : '—';
    html = `<b>Categoría</b>: ${h(c.name)}
      <br><small>Padre: ${c.father_categorie ? h(c.father_categorie.name) : 'raíz'} · Sub: ${c.subcategories.map(s=>s.name).join(', ')||'ninguna'}</small>
      <br><small>Attrs propios: ${c.attributes.map(a=>a.name).join(', ')||'ninguno'}</small>
      <br><small>Attrs heredados: ${inherited}</small>
      <br><small>Productos: ${c.products.map(p=>p.title).join(', ')||'ninguno'}</small>`;

  } else if (type === 'prod') {
    const p = R.prods.get(eid);
    if (!p) return;
    const staticImpls = p.attributes_implementations.map(ai => `${ai.attribute.name}=${ai.value}`).join(', ');
    const neededStatic = [...p.getNeededAtributesImplementations(true)].map(a=>a.name).join(', ');
    const neededDyn    = [...p.getNeededAtributesImplementations(false)].map(a=>a.name).join(', ');
    html = `<b>Producto</b>: ${h(p.title)} <span class="badge bg-warning text-dark" style="font-size:10px">${h(p.code)}</span>
      <br><small>Marca: ${h(p.brand||'—')} · Precio: $${p.price} · Categoría: ${p.category?h(p.category.name):'—'}</small>
      <br><small>Impl. estáticas: ${staticImpls||'ninguna'}</small>
      <br><small>Attrs estáticos requeridos: ${neededStatic||'ninguno'}</small>
      <br><small>Attrs dinámicos requeridos (por variante): ${neededDyn||'ninguno'}</small>
      <br><small>Variantes: ${p.variants.length}</small>`;

  } else if (type === 'var') {
    const v = R.vars.get(eid);
    if (!v) return;
    const prod = varOwner.get(v);
    const impls = v.attribute_implementations.map(ai => `${h(ai.attribute.name)} = <b>${h(String(ai.value))}</b>`).join(' · ');
    html = `<b>Variante #${v.id}</b> → ${prod ? h(prod.title) : '—'}
      <br><small>${impls || 'Sin implementaciones'}</small>`;
  }

  cy.elements().removeClass('faded');
  const node = cy.getElementById(data.id);
  cy.elements().not(node.closedNeighborhood()).not('.hidden').addClass('faded');

  document.getElementById('detail-body').innerHTML = html;
  document.getElementById('detail').style.display = 'block';
}

window.hideDetail = () => {
  document.getElementById('detail').style.display = 'none';
  if (cy) cy.elements().removeClass('faded');
};

// ─── Sample data ──────────────────────────────────────────────────────────────
function loadSample() {
  // Atributos
  const color = new Attribute({ id: uid(), key: 'color', name: 'Color', data_type: 'enum', is_static: false });
  ['rojo','azul','negro','blanco'].forEach(v => color.addEnumValue(v));
  R.attrs.set(color.id, color);

  const talle = new Attribute({ id: uid(), key: 'talle', name: 'Talle', data_type: 'enum', is_static: false });
  ['S','M','L','XL'].forEach(v => talle.addEnumValue(v));
  R.attrs.set(talle.id, talle);

  const material = new Attribute({ id: uid(), key: 'material', name: 'Material', data_type: 'text', is_static: true });
  R.attrs.set(material.id, material);

  const peso = new Attribute({ id: uid(), key: 'peso', name: 'Peso (kg)', data_type: 'number', is_static: true });
  R.attrs.set(peso.id, peso);

  // Categorías
  const indum = new Category({ id: uid(), name: 'Indumentaria' });
  R.cats.set(indum.id, indum);

  const remeras = new Category({ id: uid(), name: 'Remeras' });
  R.cats.set(remeras.id, remeras);
  remeras.changeCategorieFather(indum, {}, 0);

  const pantalones = new Category({ id: uid(), name: 'Pantalones' });
  R.cats.set(pantalones.id, pantalones);
  pantalones.changeCategorieFather(indum, {}, 0);

  // Attrs a categorías (sin productos → sin impacto todavía)
  indum.addDinamicAttribute(color, []);
  indum.addDinamicAttribute(talle, []);
  remeras.addStaticAttribute(material, []);
  pantalones.addStaticAttribute(peso, []);

  // Productos
  const remera = new Product({ id: uid(), code: 'REM-001', title: 'Remera Básica', price: 2500, description: 'Algodón 100%', brand: 'LosMacoS', category: remeras });
  remeras.addProduct(remera);
  R.prods.set(remera.id, remera);
  remera.addProductImplementation(new AttributeImplementation({ attribute: material, value: 'Algodón', id: uid() }));

  const pantalon = new Product({ id: uid(), code: 'PAN-001', title: 'Pantalón Chino', price: 5500, description: 'Slim fit', brand: 'LosMacoS', category: pantalones });
  pantalones.addProduct(pantalon);
  R.prods.set(pantalon.id, pantalon);
  pantalon.addProductImplementation(new AttributeImplementation({ attribute: peso, value: 0.8, id: uid() }));

  // Variantes
  const addVar = (prod, pairs) => {
    const impls = pairs.map(([a, v]) => new AttributeImplementation({ attribute: a, value: v }));
    prod.createVariantByImplementations(impls);
    const v = prod.variants[prod.variants.length - 1];
    v.id = uid();
    R.vars.set(v.id, v);
    varOwner.set(v, prod);
  };

  addVar(remera,   [[color,'rojo'],  [talle,'M']]);
  addVar(remera,   [[color,'azul'],  [talle,'L']]);
  addVar(pantalon, [[color,'negro'], [talle,'XL']]);

  log('Datos de ejemplo cargados con instancias de models.js.', 'success');
}

// ─── Utils ────────────────────────────────────────────────────────────────────
const h  = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const ea = s => String(s??'').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
