// ── Helpers ───────────────────────────────────────────────────────────────────

function typeBadge(data_type) {
  const map = {
    text:    ['primary',   'Texto'],
    number:  ['success',   'Número'],
    boolean: ['warning',   'Booleano'],
    enum:    ['secondary', 'Enum'],
  };
  const [cls, label] = map[data_type] || ['dark', data_type];
  return `<span class="badge bg-${cls}">${label}</span>`;
}

function staticBadge(is_static) {
  return is_static
    ? `<span class="badge bg-info text-dark">Estático</span>`
    : `<span class="badge bg-orange text-white" style="background:#fd7e14">Dinámico</span>`;
}

function showToast(msg, type = 'success') {
  const toast = document.getElementById('appToast');
  const body = document.getElementById('toastMessage');
  toast.className = `toast align-items-center text-bg-${type} border-0`;
  body.textContent = msg;
  bootstrap.Toast.getOrCreateInstance(toast, { delay: 3000 }).show();
}

// ── Attributes ────────────────────────────────────────────────────────────────

const Renders = {

  attributesList(attributes) {
    const el = document.getElementById('attributes-list');
    if (!attributes.length) {
      el.innerHTML = `<p class="text-muted">No hay atributos. Creá el primero.</p>`;
      return;
    }
    el.innerHTML = `
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th>Nombre</th><th>Key</th><th>Tipo</th><th>Modo</th><th>Valores Enum</th><th></th>
          </tr>
        </thead>
        <tbody>
          ${attributes.map(a => `
            <tr>
              <td>${a.name}</td>
              <td><code>${a.key}</code></td>
              <td>${typeBadge(a.data_type)}</td>
              <td>${staticBadge(a.is_static)}</td>
              <td>${a.enum_values.length ? a.enum_values.map(v => `<span class="chip">${v}</span>`).join('') : '<span class="text-muted">—</span>'}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary btn-edit-attr" data-id="${a.id}">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-delete-attr ms-1" data-id="${a.id}" data-name="${a.name}">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  },

  attributeForm(attr = null) {
    const isEdit = attr !== null;
    const enumVals = isEdit && attr.enum_values ? [...attr.enum_values] : [];
    document.getElementById('formModalTitle').textContent = isEdit ? 'Editar Atributo' : 'Nuevo Atributo';

    document.getElementById('formModalBody').innerHTML = `
      <form id="attr-form">
        <div class="mb-3">
          <label class="form-label">Key <span class="text-muted small">(único, no editable luego)</span></label>
          <input type="text" class="form-control" id="attr-key" value="${isEdit ? attr.key : ''}" ${isEdit ? 'readonly' : ''} required>
        </div>
        <div class="mb-3">
          <label class="form-label">Nombre</label>
          <input type="text" class="form-control" id="attr-name" value="${isEdit ? attr.name : ''}" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Tipo de dato</label>
          <select class="form-select" id="attr-data-type" ${isEdit ? 'disabled' : ''}>
            <option value="text"    ${isEdit && attr.data_type==='text'    ? 'selected':''}>Texto</option>
            <option value="number"  ${isEdit && attr.data_type==='number'  ? 'selected':''}>Número</option>
            <option value="boolean" ${isEdit && attr.data_type==='boolean' ? 'selected':''}>Booleano</option>
            <option value="enum"    ${isEdit && attr.data_type==='enum'    ? 'selected':''}>Enum</option>
          </select>
        </div>
        <div class="mb-3" id="static-toggle-section">
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox" id="attr-is-static" ${isEdit && attr.is_static ? 'checked' : ''}>
            <label class="form-check-label" for="attr-is-static">¿Es estático? (info del producto)</label>
          </div>
          <div class="form-text">Solo aplica para tipo Enum. Texto y Número son siempre estáticos; Booleano siempre dinámico.</div>
        </div>
        <div class="mb-3" id="enum-values-section" style="display:none">
          <label class="form-label">Valores posibles</label>
          <div id="enum-chips" class="mb-2">${enumVals.map(v => Renders._enumChip(v)).join('')}</div>
          <div class="input-group input-group-sm">
            <input type="text" class="form-control" id="enum-input" placeholder="Nuevo valor...">
            <button class="btn btn-outline-secondary" type="button" id="btn-add-enum">Agregar</button>
          </div>
        </div>
      </form>`;

    // Initialize enum values tracking
    window._enumValues = enumVals;

    const dataTypeEl = document.getElementById('attr-data-type');
    const updateVisibility = () => {
      const dt = isEdit ? attr.data_type : dataTypeEl.value;
      const isEnum = dt === 'enum';
      const isBool = dt === 'boolean';
      document.getElementById('enum-values-section').style.display = isEnum ? '' : 'none';
      const staticToggle = document.getElementById('attr-is-static');
      document.getElementById('static-toggle-section').style.display = (isEnum || !isEdit) ? '' : 'none';
      if (dt === 'text' || dt === 'number') staticToggle.checked = true, staticToggle.disabled = true;
      else if (isBool) staticToggle.checked = false, staticToggle.disabled = true;
      else staticToggle.disabled = false;
    };
    dataTypeEl.addEventListener('change', updateVisibility);
    updateVisibility();

    document.getElementById('btn-add-enum').addEventListener('click', () => {
      const input = document.getElementById('enum-input');
      const val = input.value.trim();
      if (!val || window._enumValues.includes(val)) return;
      window._enumValues.push(val);
      document.getElementById('enum-chips').insertAdjacentHTML('beforeend', Renders._enumChip(val));
      input.value = '';
    });

    document.getElementById('enum-chips').addEventListener('click', e => {
      if (e.target.classList.contains('chip-remove')) {
        const val = e.target.dataset.val;
        window._enumValues = window._enumValues.filter(v => v !== val);
        e.target.closest('.chip').remove();
      }
    });
  },

  _enumChip(val) {
    return `<span class="chip">${val}<span class="chip-remove ms-1" data-val="${val}" style="cursor:pointer;color:#6c757d">✕</span></span>`;
  },

  getAttributeFormData() {
    const dataType = document.getElementById('attr-data-type').value;
    return {
      key: document.getElementById('attr-key').value.trim(),
      name: document.getElementById('attr-name').value.trim(),
      data_type: dataType,
      is_static: document.getElementById('attr-is-static').checked,
      enum_values: dataType === 'enum' ? [...window._enumValues] : [],
    };
  },

  // ── Categories ─────────────────────────────────────────────────────────────

  categoriesList(categories) {
    const el = document.getElementById('categories-list');
    if (!categories.length) {
      el.innerHTML = `<p class="text-muted">No hay categorías. Creá la primera.</p>`;
      return;
    }
    el.innerHTML = `
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Nombre</th><th>Atributos</th><th></th></tr>
        </thead>
        <tbody>
          ${categories.map(c => `
            <tr>
              <td>${c.name}</td>
              <td>${c.attributes.map(a => `<span class="badge bg-light text-dark border me-1">${a.name}</span>`).join('') || '<span class="text-muted">—</span>'}</td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-secondary btn-edit-cat" data-id="${c.id}">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-delete-cat ms-1" data-id="${c.id}" data-name="${c.name}">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  },

  categoryForm(cat = null, allAttributes) {
    const isEdit = cat !== null;
    const selectedIds = isEdit ? cat.attributes.map(a => a.id) : [];
    document.getElementById('formModalTitle').textContent = isEdit ? 'Editar Categoría' : 'Nueva Categoría';

    document.getElementById('formModalBody').innerHTML = `
      <form id="cat-form">
        <div class="mb-3">
          <label class="form-label">Nombre</label>
          <input type="text" class="form-control" id="cat-name" value="${isEdit ? cat.name : ''}" required>
        </div>
        <div class="mb-3">
          <label class="form-label">Atributos</label>
          <div class="border rounded p-2" style="max-height:220px;overflow-y:auto">
            ${allAttributes.length ? allAttributes.map(a => `
              <div class="form-check">
                <input class="form-check-input cat-attr-check" type="checkbox" value="${a.id}" id="catattr-${a.id}"
                  ${selectedIds.includes(a.id) ? 'checked' : ''}>
                <label class="form-check-label" for="catattr-${a.id}">
                  ${a.name} ${typeBadge(a.data_type)} ${staticBadge(a.is_static)}
                </label>
              </div>`).join('')
            : '<span class="text-muted small">No hay atributos disponibles. Creá atributos primero.</span>'}
          </div>
        </div>
        ${isEdit ? `<div class="alert alert-warning small py-2">
          <i class="bi bi-exclamation-triangle me-1"></i>
          Modificar atributos puede afectar productos y variantes existentes de esta categoría.
        </div>` : ''}
      </form>`;
  },

  getCategoryFormData() {
    const checks = document.querySelectorAll('.cat-attr-check:checked');
    return {
      name: document.getElementById('cat-name').value.trim(),
      attribute_ids: Array.from(checks).map(c => parseInt(c.value)),
    };
  },

  // ── Products ───────────────────────────────────────────────────────────────

  productsList(products) {
    const el = document.getElementById('products-list');
    if (!products.length) {
      el.innerHTML = `<p class="text-muted">No hay productos. Creá el primero.</p>`;
      return;
    }
    el.innerHTML = `
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr><th>Código</th><th>Título</th><th>Precio</th><th>Marca</th><th>Categoría</th><th>Variantes</th><th></th></tr>
        </thead>
        <tbody>
          ${products.map(p => `
            <tr>
              <td><code>${p.code}</code></td>
              <td>${p.title}</td>
              <td>$${p.price.toFixed(2)}</td>
              <td>${p.brand}</td>
              <td><span class="badge bg-light text-dark border">${p.category_name}</span></td>
              <td><span class="badge bg-secondary">${p.variant_count}</span></td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-primary btn-view-product" data-id="${p.id}" title="Ver detalle">
                  <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-secondary btn-edit-product ms-1" data-id="${p.id}" title="Editar">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-delete-product ms-1" data-id="${p.id}" data-name="${p.title}" title="Eliminar">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  },

  productForm(product = null, categories, allAttributes) {
    const isEdit = product !== null;
    document.getElementById('formModalTitle').textContent = isEdit ? 'Editar Producto' : 'Nuevo Producto';

    const selectedCatId = isEdit ? product.category.id : '';
    const selectedAttrIds = isEdit ? product.attributes.map(a => a.id) : [];
    const existingImpls = isEdit
      ? Object.fromEntries(product.attributes_implementations.map(i => [i.attribute.id, i.value]))
      : {};

    document.getElementById('formModalBody').innerHTML = `
      <form id="product-form">
        <div class="row g-3 mb-3">
          <div class="col-md-4">
            <label class="form-label">Código</label>
            <input type="text" class="form-control" id="prod-code" value="${isEdit ? product.code : ''}" ${isEdit ? 'readonly' : ''} required>
          </div>
          <div class="col-md-8">
            <label class="form-label">Título</label>
            <input type="text" class="form-control" id="prod-title" value="${isEdit ? product.title : ''}" required>
          </div>
          <div class="col-md-4">
            <label class="form-label">Precio</label>
            <input type="number" step="0.01" class="form-control" id="prod-price" value="${isEdit ? product.price : ''}" required>
          </div>
          <div class="col-md-4">
            <label class="form-label">Marca</label>
            <input type="text" class="form-control" id="prod-brand" value="${isEdit ? product.brand : ''}">
          </div>
          <div class="col-md-4">
            <label class="form-label">Categoría</label>
            <select class="form-select" id="prod-category" required>
              <option value="">Seleccioná una categoría...</option>
              ${categories.map(c => `<option value="${c.id}" ${c.id === selectedCatId ? 'selected' : ''}>${c.name}</option>`).join('')}
            </select>
          </div>
          <div class="col-12">
            <label class="form-label">Descripción</label>
            <textarea class="form-control" id="prod-description" rows="2">${isEdit ? product.description : ''}</textarea>
          </div>
        </div>

        <div id="prod-attrs-section" class="mb-3" style="display:${isEdit ? '' : 'none'}">
          <label class="form-label fw-semibold">Atributos propios del producto</label>
          <div class="border rounded p-2 mb-2" style="max-height:160px;overflow-y:auto" id="prod-own-attrs-list">
            ${Renders._productOwnAttrsList(allAttributes, selectedAttrIds, selectedCatId, categories)}
          </div>
        </div>

        <div id="prod-impls-section" class="mb-3" style="display:${isEdit ? '' : 'none'}">
          <label class="form-label fw-semibold">Valores de atributos estáticos</label>
          <div id="prod-impls-list">
            ${isEdit ? Renders._implFields(product.category, product.attributes, existingImpls) : ''}
          </div>
        </div>

        <div id="prod-dynamic-info" style="display:none">
          <div class="alert alert-info small py-2 mb-0">
            <i class="bi bi-info-circle me-1"></i>
            Los atributos dinámicos se gestionan desde las variantes del producto.
          </div>
        </div>
      </form>`;

    // Store state for dynamic re-rendering
    window._prodFormState = { categories, allAttributes, selectedAttrIds: [...selectedAttrIds], existingImpls };

    document.getElementById('prod-category').addEventListener('change', () => {
      Renders._onProductCategoryChange(categories, allAttributes);
    });

    if (isEdit) Renders._onProductCategoryChange(categories, allAttributes, product.attributes, existingImpls);
  },

  _productOwnAttrsList(allAttributes, selectedAttrIds, catId, categories) {
    const cat = categories.find(c => c.id === parseInt(catId));
    const catAttrIds = cat ? cat.attributes.map(a => a.id) : [];
    const available = allAttributes.filter(a => !catAttrIds.includes(a.id));
    if (!available.length) return '<span class="text-muted small">No hay atributos adicionales disponibles.</span>';
    return available.map(a => `
      <div class="form-check">
        <input class="form-check-input prod-own-attr-check" type="checkbox" value="${a.id}" id="prodattr-${a.id}"
          ${selectedAttrIds.includes(a.id) ? 'checked' : ''}>
        <label class="form-check-label" for="prodattr-${a.id}">
          ${a.name} ${typeBadge(a.data_type)} ${staticBadge(a.is_static)}
        </label>
      </div>`).join('');
  },

  _implFields(category, ownAttrs, existingImpls) {
    const staticAttrs = [
      ...(category ? category.attributes.filter(a => a.is_static) : []),
      ...(ownAttrs ? ownAttrs.filter(a => a.is_static) : []),
    ];
    if (!staticAttrs.length) return '<p class="text-muted small">Sin atributos estáticos.</p>';
    return staticAttrs.map(a => {
      const val = existingImpls[a.id] || '';
      let input = '';
      if (a.data_type === 'enum') {
        input = `<select class="form-select form-select-sm" data-attr-id="${a.id}" name="impl-${a.id}">
          <option value="">Seleccioná...</option>
          ${a.enum_values.map(v => `<option value="${v}" ${v === val ? 'selected' : ''}>${v}</option>`).join('')}
        </select>`;
      } else {
        input = `<input type="${a.data_type === 'number' ? 'number' : 'text'}" class="form-control form-control-sm"
          data-attr-id="${a.id}" name="impl-${a.id}" value="${val}">`;
      }
      return `<div class="row align-items-center mb-2">
        <label class="col-sm-4 col-form-label col-form-label-sm">${a.name} ${typeBadge(a.data_type)}</label>
        <div class="col-sm-8">${input}</div>
      </div>`;
    }).join('');
  },

  _onProductCategoryChange(categories, allAttributes, ownAttrs = null, existingImpls = {}) {
    const catId = parseInt(document.getElementById('prod-category').value);
    const cat = categories.find(c => c.id === catId);
    const attrsSection = document.getElementById('prod-attrs-section');
    const implsSection = document.getElementById('prod-impls-section');
    const dynamicInfo = document.getElementById('prod-dynamic-info');

    if (!cat) {
      attrsSection.style.display = 'none';
      implsSection.style.display = 'none';
      dynamicInfo.style.display = 'none';
      return;
    }

    const catAttrIds = cat.attributes.map(a => a.id);
    const selectedOwnAttrIds = ownAttrs
      ? ownAttrs.map(a => a.id)
      : Array.from(document.querySelectorAll('.prod-own-attr-check:checked')).map(c => parseInt(c.value));

    // Re-render own attrs list
    document.getElementById('prod-own-attrs-list').innerHTML =
      Renders._productOwnAttrsList(allAttributes, selectedOwnAttrIds, catId, categories);

    // Attach change listener to own attrs for impl refresh
    document.querySelectorAll('.prod-own-attr-check').forEach(cb => {
      cb.addEventListener('change', () => {
        const ids = Array.from(document.querySelectorAll('.prod-own-attr-check:checked')).map(c => parseInt(c.value));
        const ownSelected = allAttributes.filter(a => ids.includes(a.id));
        document.getElementById('prod-impls-list').innerHTML =
          Renders._implFields(cat, ownSelected, existingImpls);
      });
    });

    // Render static impls
    const ownSelected = allAttributes.filter(a => selectedOwnAttrIds.includes(a.id));
    document.getElementById('prod-impls-list').innerHTML =
      Renders._implFields(cat, ownSelected, existingImpls);

    attrsSection.style.display = '';
    implsSection.style.display = '';

    // Show dynamic info if category has dynamic attrs
    const hasDynamic = cat.attributes.some(a => !a.is_static);
    dynamicInfo.style.display = hasDynamic ? '' : 'none';
  },

  getProductFormData() {
    const catId = parseInt(document.getElementById('prod-category').value);
    const ownAttrIds = Array.from(document.querySelectorAll('.prod-own-attr-check:checked')).map(c => parseInt(c.value));
    const implEls = document.querySelectorAll('[data-attr-id]');
    const staticImplementations = Array.from(implEls)
      .filter(el => el.value !== '')
      .map(el => Dtos.implementationIn(el.dataset.attrId, el.value));

    return {
      code:                  document.getElementById('prod-code').value.trim(),
      title:                 document.getElementById('prod-title').value.trim(),
      price:                 document.getElementById('prod-price').value,
      brand:                 document.getElementById('prod-brand').value.trim(),
      description:           document.getElementById('prod-description').value.trim(),
      category_id:           catId,
      attribute_ids:         ownAttrIds,
      static_implementations: staticImplementations,
    };
  },

  // ── Product Detail ─────────────────────────────────────────────────────────

  productDetail(product) {
    document.getElementById('productDetailTitle').textContent = `${product.title} · ${product.code}`;

    const dynamicAttrs = [
      ...product.category.attributes.filter(a => !a.is_static),
      ...product.attributes.filter(a => !a.is_static),
    ];

    document.getElementById('productDetailBody').innerHTML = `
      <div class="row">
        <div class="col-md-5">
          <h6 class="text-muted text-uppercase small mb-3">Info del producto</h6>
          <dl class="row small">
            <dt class="col-5">Código</dt><dd class="col-7"><code>${product.code}</code></dd>
            <dt class="col-5">Marca</dt><dd class="col-7">${product.brand}</dd>
            <dt class="col-5">Precio</dt><dd class="col-7">$${product.price.toFixed(2)}</dd>
            <dt class="col-5">Categoría</dt><dd class="col-7">${product.category.name}</dd>
            <dt class="col-5">Descripción</dt><dd class="col-7">${product.description || '—'}</dd>
          </dl>
          ${product.attributes_implementations.length ? `
            <h6 class="text-muted text-uppercase small mb-2">Atributos estáticos</h6>
            <dl class="row small">
              ${product.attributes_implementations.map(i => `
                <dt class="col-5">${i.attribute.name}</dt>
                <dd class="col-7">${i.value}</dd>
              `).join('')}
            </dl>` : ''}
        </div>

        <div class="col-md-7">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="text-muted text-uppercase small mb-0">Variantes</h6>
            ${dynamicAttrs.length ? `<button class="btn btn-sm btn-primary" id="btn-show-add-variant" data-prod-id="${product.id}">
              <i class="bi bi-plus-lg me-1"></i>Agregar variante
            </button>` : ''}
          </div>

          ${dynamicAttrs.length === 0 ? `
            <p class="text-muted small">Este producto no tiene atributos dinámicos. No requiere variantes.</p>` :
          product.variants.length === 0 ? `
            <p class="text-muted small">Sin variantes. Agregá la primera.</p>` :
          `<table class="table table-sm table-bordered align-middle">
            <thead class="table-light">
              <tr>
                ${dynamicAttrs.map(a => `<th>${a.name}</th>`).join('')}
                <th></th>
              </tr>
            </thead>
            <tbody>
              ${product.variants.map(v => `
                <tr>
                  ${dynamicAttrs.map(a => {
                    const impl = v.attribute_implementations.find(i => i.attribute.key === a.key);
                    return `<td>${impl ? impl.value : '—'}</td>`;
                  }).join('')}
                  <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger btn-delete-variant"
                      data-prod-id="${product.id}" data-variant-id="${v.id}">
                      <i class="bi bi-trash"></i>
                    </button>
                  </td>
                </tr>`).join('')}
            </tbody>
          </table>`}

          <div id="add-variant-form" style="display:none" class="mt-3 border rounded p-3 bg-light">
            <h6 class="small fw-semibold mb-2">Nueva variante</h6>
            ${dynamicAttrs.map(a => `
              <div class="mb-2">
                <label class="form-label form-label-sm">${a.name} ${typeBadge(a.data_type)}</label>
                ${a.data_type === 'boolean'
                  ? `<div class="form-check"><input type="checkbox" class="form-check-input variant-impl-input" data-attr-id="${a.id}" id="vi-${a.id}"><label class="form-check-label" for="vi-${a.id}">Sí</label></div>`
                  : a.data_type === 'enum'
                    ? `<select class="form-select form-select-sm variant-impl-input" data-attr-id="${a.id}">
                        <option value="">Seleccioná...</option>
                        ${a.enum_values.map(v => `<option value="${v}">${v}</option>`).join('')}
                       </select>`
                    : `<input type="${a.data_type === 'number' ? 'number' : 'text'}" class="form-control form-control-sm variant-impl-input" data-attr-id="${a.id}">`
                }
              </div>`).join('')}
            <button class="btn btn-sm btn-success" id="btn-confirm-variant" data-prod-id="${product.id}">
              <i class="bi bi-check-lg me-1"></i>Confirmar variante
            </button>
            <button class="btn btn-sm btn-link text-secondary" id="btn-cancel-variant">Cancelar</button>
          </div>
        </div>
      </div>`;
  },
};