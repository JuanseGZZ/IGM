// ── Helpers HTML ──────────────────────────────────────────────────────────────
const badge = (text, color) => `<span class="badge bg-${color} me-1">${text}</span>`;
const icon  = (name, cls='') => `<i class="bi bi-${name} ${cls}"></i>`;

// ── Render ────────────────────────────────────────────────────────────────────
const Render = {

  // ── Árbol ─────────────────────────────────────────────────────────────────
  tree() {
    const el = document.getElementById('tree-container');
    el.innerHTML = State.roots.map(c => this._treeNode(c)).join('');
    Animations.fadeIn(el);
  },

  _treeNode(cat) {
    const hasChildren = cat._children?.length > 0;
    const attrs = cat.attributes.map(a => `<span class="tree-attr">[${a.key}]</span>`).join('');
    const children = hasChildren
      ? `<div class="tree-children ms-3">${cat._children.map(c => this._treeNode(State.catById[c.id] || c)).join('')}</div>`
      : '';
    return `
      <div class="tree-node" id="node-${cat.id}">
        <div class="tree-item px-2 py-1 rounded d-flex align-items-center gap-1"
             data-id="${cat.id}" onclick="Events.selectCategory(${cat.id})">
          ${icon(hasChildren ? 'folder2' : 'folder2-open', 'text-warning')}
          <span class="tree-label">${cat.name}</span>
          <span class="tree-attrs ms-1">${attrs}</span>
        </div>
        ${children}
      </div>`;
  },

  // ── Detalle de categoria ───────────────────────────────────────────────────
  categoryDetail(cat) {
    const parent = cat.father_id ? (State.catById[cat.father_id]?.name || `#${cat.father_id}`) : '—';
    const used   = new Set(cat.attributes.map(a => a.id));
    const avail  = State.attributes.filter(a => !used.has(a.id));

    const attrBadges = cat.attributes.map(a => `
      <span class="badge bg-primary fs-6 d-inline-flex align-items-center gap-1 me-1 mb-1">
        ${a.key}
        <button class="btn-close btn-close-white btn-sm p-0" style="font-size:.6rem"
          title="Quitar atributo" onclick="Events.removeAttribute(${cat.id}, ${a.id})"></button>
      </span>`).join('');

    const addAttrDropdown = avail.length ? `
      <div class="dropdown d-inline-block">
        <button class="btn btn-sm btn-outline-primary dropdown-toggle" data-bs-toggle="dropdown">
          ${icon('plus')} Agregar
        </button>
        <ul class="dropdown-menu">
          ${avail.map(a => `
            <li><a class="dropdown-item d-flex justify-content-between align-items-center"
                   onclick="Events.addAttribute(${cat.id}, ${a.id})">
              <span>${a.name} <small class="text-muted">[${a.key}]</small></span>
              ${badge(a.is_static ? 'estático' : 'dinámico', a.is_static ? 'success' : 'info')}
            </a></li>`).join('')}
        </ul>
      </div>` : '';

    document.getElementById('detail-panel').innerHTML = `
      <div class="card shadow-sm fade-in">
        <div class="card-header d-flex justify-content-between align-items-center bg-warning bg-opacity-10">
          <h5 class="mb-0">${icon('folder2', 'text-warning me-2')}${cat.name}</h5>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-outline-danger" onclick="Events.deleteCategory(${cat.id})" title="Eliminar categoría">
              ${icon('trash')}
            </button>
          </div>
        </div>
        <div class="card-body">

          <div class="row mb-3">
            <div class="col">
              <label class="form-label fw-semibold text-muted small">PADRE</label>
              <div class="d-flex align-items-center gap-2">
                <span>${parent}</span>
                <button class="btn btn-sm btn-outline-secondary" onclick="Events.openChangeFather(${cat.id})">
                  ${icon('arrow-up-circle')} Cambiar padre
                </button>
                ${cat.father_id ? `<button class="btn btn-sm btn-outline-danger" onclick="Events.removeFather(${cat.id})">
                  ${icon('x-circle')} Quitar padre
                </button>` : ''}
              </div>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold text-muted small">ATRIBUTOS</label>
            <div class="d-flex flex-wrap align-items-center gap-1">
              ${attrBadges || '<span class="text-muted">Ninguno</span>'}
              ${addAttrDropdown}
            </div>
          </div>

          <div id="cat-children-section">
            <div class="text-muted small">${icon('arrow-clockwise')} Cargando...</div>
          </div>
        </div>
      </div>`;
    Animations.fadeIn(document.getElementById('detail-panel'));
    Events.loadCategoryChildren(cat);
  },

  categoryChildren(cat, products) {
    const section = document.getElementById('cat-children-section');
    if (!section) return;

    if (cat._children?.length) {
      section.innerHTML = `
        <label class="form-label fw-semibold text-muted small">SUBCATEGORÍAS</label>
        <div class="d-flex flex-wrap gap-2">
          ${cat._children.map(c => `
            <button class="btn btn-sm btn-outline-warning" onclick="Events.selectCategory(${c.id})">
              ${icon('folder2')} ${State.catById[c.id]?.name || c.name}
            </button>`).join('')}
        </div>`;
    } else if (products.length) {
      section.innerHTML = `
        <label class="form-label fw-semibold text-muted small">PRODUCTOS (${products.length})</label>
        <div class="list-group list-group-flush">
          ${products.map(p => `
            <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                 onclick="Events.selectProduct(${p.id})" style="cursor:pointer">
              <span>${icon('box-seam', 'text-success me-2')}${p.title}
                <small class="text-muted ms-2">${p.code}</small></span>
              <span class="text-muted">$${p.price}</span>
            </div>`).join('')}
        </div>
        <div class="mt-2">
          <button class="btn btn-sm btn-outline-success" onclick="Events.openCreateProduct(${cat.id})">
            ${icon('plus-circle')} Nuevo producto
          </button>
        </div>`;
    } else {
      section.innerHTML = `
        <div class="text-muted small mb-2">Sin productos aún.</div>
        <button class="btn btn-sm btn-outline-success" onclick="Events.openCreateProduct(${cat.id})">
          ${icon('plus-circle')} Nuevo producto
        </button>`;
    }
  },

  // ── Detalle de producto ────────────────────────────────────────────────────
  productDetail(prod) {
    const catName = State.catById[prod.category_id]?.name || `Cat #${prod.category_id}`;
    const catSel = State.categories
      .filter(c => !c._children?.length && c.id !== prod.category_id)
      .map(c => `<option value="${c.id}">${c.name}</option>`).join('');

    const implTable = prod.attributes_implementations.length
      ? `<table class="table table-sm table-bordered mb-0">
          <thead class="table-light"><tr><th>Atributo</th><th>Tipo</th><th>Valor</th></tr></thead>
          <tbody>${prod.attributes_implementations.map(i => `
            <tr>
              <td>${badge(i.attribute.key, i.attribute.is_static ? 'success' : 'info')}</td>
              <td><small class="text-muted">${i.attribute.data_type}</small></td>
              <td>${i.value}</td>
            </tr>`).join('')}
          </tbody>
        </table>`
      : '<p class="text-muted small mb-0">Sin implementaciones</p>';

    const varCards = prod.variants.map(v => `
      <div class="card card-body p-2 position-relative" style="min-width:140px">
        ${v.attribute_implementations.map(i =>
          `<div class="small"><span class="text-muted">${i.attribute.key}:</span> ${i.value}</div>`
        ).join('')}
        <button class="btn btn-sm btn-link text-danger p-0 mt-1"
                onclick="Events.removeVariant(${prod.id}, ${v.id})">
          ${icon('trash')} quitar
        </button>
      </div>`).join('');

    document.getElementById('detail-panel').innerHTML = `
      <div class="card shadow-sm fade-in">
        <div class="card-header d-flex justify-content-between align-items-center bg-success bg-opacity-10">
          <h5 class="mb-0">${icon('box-seam', 'text-success me-2')}${prod.title}</h5>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-outline-secondary"
                    onclick="Events.openChangeCategory(${prod.id})" title="Cambiar categoría">
              ${icon('arrow-left-right')} Cambiar categoría
            </button>
            <button class="btn btn-sm btn-outline-danger"
                    onclick="Events.deleteProduct(${prod.id})" title="Eliminar producto">
              ${icon('trash')}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="row text-muted small mb-3">
            <div class="col-md-3"><strong>Código:</strong> ${prod.code}</div>
            <div class="col-md-3"><strong>Precio:</strong> $${prod.price}</div>
            <div class="col-md-3"><strong>Marca:</strong> ${prod.brand || '—'}</div>
            <div class="col-md-3"><strong>Categoría:</strong> ${catName}</div>
          </div>

          <div class="mb-4">
            <label class="form-label fw-semibold text-muted small">ATRIBUTOS IMPLEMENTADOS</label>
            ${implTable}
          </div>

          <div>
            <div class="d-flex justify-content-between align-items-center mb-2">
              <label class="form-label fw-semibold text-muted small mb-0">VARIANTES (${prod.variants.length})</label>
              <button class="btn btn-sm btn-outline-success" onclick="Events.openAddVariant(${prod.id})">
                ${icon('plus')} Agregar variante
              </button>
            </div>
            ${prod.variants.length
              ? `<div class="d-flex flex-wrap gap-2">${varCards}</div>`
              : '<p class="text-muted small">Sin variantes</p>'}
          </div>
        </div>
      </div>`;
    Animations.fadeIn(document.getElementById('detail-panel'));
  },

  // ── Modal: impacto (E1-E5) ────────────────────────────────────────────────
  impactModal(impact, msg = null) {
    return new Promise(resolve => {
      document.getElementById('impact-modal-body').innerHTML = `
        ${msg ? `<div class="alert alert-warning py-2">${msg}</div>` : ''}
        <p class="text-muted small">Elegí qué hacer con cada grupo antes de confirmar.</p>
        ${impact.map((g, i) => `
          <div class="card mb-3">
            <div class="card-header py-2">
              <strong>Atributos:</strong>
              ${g.attrs.map(a => badge(a.key, 'warning text-dark')).join(' ')}
            </div>
            <div class="card-body py-2">
              <div class="mb-2 small">
                <strong>Productos afectados:</strong>
                ${g.products.map(p => `<span class="me-1 text-secondary">${p.title}</span>`).join(', ')}
              </div>
              <div class="d-flex align-items-center gap-2">
                <label class="mb-0 small fw-semibold">Acción:</label>
                <select class="form-select form-select-sm w-auto" id="imp-action-${i}">
                  <option value="eliminar">Eliminar implementaciones</option>
                  <option value="heredar">Mantener (heredar)</option>
                </select>
              </div>
            </div>
          </div>`).join('')}`;

      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('impact-modal'));
      modal.show();

      const confirmBtn = document.getElementById('impact-confirm-btn');
      confirmBtn.onclick = () => {
        const resolution = impact.map((g, i) => ({
          attr_ids:    g.attrs.map(a => a.id),
          product_ids: g.products.map(p => p.id),
          action:      document.getElementById(`imp-action-${i}`).value,
        }));
        modal.hide();
        resolve(resolution);
      };
      document.getElementById('impact-cancel-btn').onclick = () => { modal.hide(); resolve(null); };
    });
  },

  // ── Modal: cambio de categoria (E6) ───────────────────────────────────────
  e6Modal(toAdd, toRemove, msg = null) {
    return new Promise(resolve => {
      const removeSection = toRemove.length ? `
        <div class="mb-3">
          <label class="fw-semibold small">Atributos que se perderán:</label>
          <div class="mb-2">${toRemove.map(a => badge(a.key, 'danger')).join(' ')}</div>
          <select class="form-select form-select-sm w-auto" id="e6-remove-action">
            <option value="eliminar">Eliminar implementaciones</option>
            <option value="heredar">Mantener como están</option>
          </select>
        </div>` : '';

      const addSection = toAdd.length ? `
        <div class="mb-3">
          <label class="fw-semibold small">Atributos a implementar (completar valores):</label>
          ${toAdd.map(a => `
            <div class="mb-2">
              <label class="form-label small mb-1">${badge(a.key, 'success')} ${a.name}
                <span class="text-muted">(${a.data_type})</span>
              </label>
              ${a.data_type === 'enum'
                ? `<select class="form-select form-select-sm" id="e6-val-${a.id}">
                    ${(a.enum_values || []).map(v => `<option>${v}</option>`).join('')}
                   </select>`
                : `<input type="${a.data_type === 'number' ? 'number' : 'text'}"
                          class="form-control form-control-sm" id="e6-val-${a.id}"
                          placeholder="Valor para ${a.key}">`}
            </div>`).join('')}
        </div>` : '';

      document.getElementById('e6-modal-body').innerHTML = `
        ${msg ? `<div class="alert alert-info py-2 small">${msg}</div>` : ''}
        ${removeSection}
        ${addSection}
        ${!removeSection && !addSection ? '<p class="text-muted">Sin cambios requeridos.</p>' : ''}`;

      const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('e6-modal'));
      modal.show();

      document.getElementById('e6-confirm-btn').onclick = () => {
        const new_implementations = toAdd.map(a => ({
          attr_id: a.id,
          value: document.getElementById(`e6-val-${a.id}`)?.value || '',
        }));
        const remove_action = document.getElementById('e6-remove-action')?.value || 'eliminar';
        modal.hide();
        resolve({ remove_action, new_implementations });
      };
      document.getElementById('e6-cancel-btn').onclick = () => { modal.hide(); resolve(null); };
    });
  },

  // ── Modal genérico (formularios) ──────────────────────────────────────────
  formModal(title, bodyHtml, onConfirm) {
    document.getElementById('form-modal-title').textContent = title;
    document.getElementById('form-modal-body').innerHTML = bodyHtml;
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('form-modal'));
    modal.show();
    document.getElementById('form-confirm-btn').onclick = () => {
      if (onConfirm()) modal.hide();
    };
  },

  closeFormModal() {
    bootstrap.Modal.getOrCreateInstance(document.getElementById('form-modal')).hide();
  },

  // ── Placeholder ───────────────────────────────────────────────────────────
  placeholder(msg = 'Seleccioná una categoría o producto del árbol') {
    document.getElementById('detail-panel').innerHTML = `
      <div class="text-center text-muted mt-5">
        ${icon('diagram-3', 'fs-1 d-block mb-3')}
        <p>${msg}</p>
      </div>`;
  },
};
