function esc(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

const Render = {

    tabs(active) {
        return ['products', 'brands'].map(t => `
            <li class="nav-item">
                <button type="button" class="nav-link ${active === t ? 'active' : ''}" data-tab="${t}">
                    ${t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
            </li>
        `).join('');
    },

    // ── Products ─────────────────────────────────────────────────────────────

    attrRow(attr, productId) {
        const valueBadges = attr.values.map(v =>
            `<span class="pill">${esc(v)}</span>`
        ).join(' ');
        return `
            <div class="attr-row">
                <span class="attr-key" title="${esc(attr.key)}">${esc(attr.key)}</span>
                <div class="d-flex flex-wrap gap-1 flex-grow-1">
                    ${valueBadges || '<small class="text-muted">—</small>'}
                </div>
                <div class="d-flex gap-1 flex-shrink-0">
                    <button class="btn btn-outline-secondary btn-xs"
                            data-action="edit-attr" data-product-id="${productId}" data-id="${attr.id}">Edit</button>
                    <button class="btn btn-outline-danger btn-xs"
                            data-action="delete-attr" data-product-id="${productId}" data-id="${attr.id}">×</button>
                </div>
            </div>
        `;
    },

    productCard(product) {
        const brandName = product.brand ? product.brand.name : '';
        const attrRows  = product.attributes.map(a => this.attrRow(a, product.id)).join('');
        const vCount    = product.variants.length;
        return `
            <div class="card">
                <div class="card-body">

                    <!-- Header -->
                    <div class="d-flex justify-content-between align-items-start gap-3">
                        <div>
                            <span class="prod-name">${esc(product.name)}</span>
                            ${brandName
                                ? `<span class="chip-brand">${esc(brandName)}</span>`
                                : ''}
                            ${product.description
                                ? `<div class="prod-desc">${esc(product.description)}</div>`
                                : ''}
                        </div>
                        <div class="d-flex gap-1 flex-shrink-0">
                            <button class="btn btn-outline-secondary btn-sm" data-action="edit-product" data-id="${product.id}">Edit</button>
                            <button class="btn btn-outline-danger btn-sm" data-action="delete-product" data-id="${product.id}">Delete</button>
                        </div>
                    </div>

                    <!-- Attributes section -->
                    <div class="panel">
                        <div class="panel-head">
                            <span class="panel-label">Attributes</span>
                            <div class="d-flex gap-1">
                                <button class="btn btn-outline-secondary btn-xs"
                                        data-action="new-attr" data-product-id="${product.id}">+ Add</button>
                                <button class="btn btn-outline-secondary btn-xs"
                                        data-action="copy-attr" data-product-id="${product.id}">Copy</button>
                            </div>
                        </div>
                        <div class="d-flex flex-column">
                            ${attrRows || '<small class="text-muted">No attributes yet</small>'}
                        </div>
                    </div>

                    <!-- Variants section -->
                    <div class="panel">
                        <div class="panel-head" style="margin-bottom:0">
                            <span class="panel-label">
                                Variants <span class="num">${vCount}</span>
                            </span>
                            <button class="btn btn-outline-secondary btn-xs"
                                    data-action="manage-variants" data-product-id="${product.id}">Manage</button>
                        </div>
                    </div>

                </div>
            </div>
        `;
    },

    productsTab(products) {
        return `
            <div class="section-bar">
                <div>
                    <h6>Products<span class="count">${products.length} total</span></h6>
                </div>
                <button class="btn btn-primary btn-sm" data-action="new-product">+ New Product</button>
            </div>
            ${products.length
                ? products.map(p => this.productCard(p)).join('')
                : `<div class="empty">
                       <div class="empty-title">No products yet</div>
                       <div>Create your first product to start adding attributes and variants.</div>
                   </div>`}
        `;
    },

    productForm(product, allBrands) {
        const brandOpts = allBrands.map(b =>
            `<option value="${b.id}" ${product?.brand?.id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`
        ).join('');
        return `
            <h6>${product ? 'Edit Product' : 'New Product'}</h6>
            <form id="product-form">
                <input type="hidden" name="id" value="${product ? product.id : ''}">
                <div class="mb-3">
                    <label class="form-label form-label-sm">Name</label>
                    <input type="text" class="form-control form-control-sm" name="name"
                           value="${product ? esc(product.name) : ''}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label form-label-sm">Description</label>
                    <textarea class="form-control form-control-sm" name="description" rows="2">${product ? esc(product.description) : ''}</textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label form-label-sm">Brand</label>
                    <select class="form-select form-select-sm" name="brand">
                        <option value="">— No brand —</option>
                        ${brandOpts}
                    </select>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" data-action="save-product">Save</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Cancel</button>
                </div>
            </form>
        `;
    },

    // ── Attribute form (belongs to a product) ────────────────────────────────

    attrForm(attr, pendingValues, pendingKey) {
        const key    = pendingKey    !== undefined ? pendingKey    : (attr ? attr.key    : '');
        const values = pendingValues !== undefined ? pendingValues : (attr ? attr.values : []);
        const valueBadges = values.map((v, i) => `
            <span class="pill">
                ${esc(v)}
                <button type="button" class="btn-close"
                        data-action="remove-value" data-index="${i}" aria-label="Remove"></button>
            </span>
        `).join(' ');
        return `
            <h6>${attr ? 'Edit Attribute' : 'New Attribute'}</h6>
            <form id="attr-form">
                <input type="hidden" name="id" value="${attr ? attr.id : ''}">
                <div class="mb-3">
                    <label class="form-label form-label-sm">Key <small>e.g. Color, Size</small></label>
                    <input type="text" class="form-control form-control-sm" name="key" value="${esc(key)}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label form-label-sm">Values</label>
                    <div class="d-flex flex-wrap gap-1 mb-2 p-2 rounded-2" style="min-height:44px" id="values-preview">
                        ${valueBadges || '<small class="text-muted">No values yet</small>'}
                    </div>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" id="new-value-input" placeholder="Type and press Enter…">
                        <button type="button" class="btn btn-outline-secondary" data-action="add-value">Add</button>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" data-action="save-attr">Save</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Cancel</button>
                </div>
            </form>
        `;
    },

    attrCopyPicker(allProducts, targetProductId) {
        const items = [];
        allProducts.forEach(p => {
            p.attributes.forEach(a => {
                items.push({ attr: a, productId: p.id, productName: p.name });
            });
        });
        const rows = items.map(item => `
            <button type="button"
                    class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                    data-action="confirm-copy-attr"
                    data-source-product-id="${item.productId}"
                    data-attr-id="${item.attr.id}"
                    data-target-product-id="${targetProductId}">
                <span class="d-flex align-items-center gap-2 flex-grow-1" style="min-width:0">
                    <span class="attr-key" style="min-width:auto;max-width:none">${esc(item.attr.key)}</span>
                    <span class="d-flex align-items-center gap-1 flex-wrap">
                        ${item.attr.values.map(v =>
                            `<span class="pill">${esc(v)}</span>`
                        ).join('')}
                    </span>
                </span>
                <small class="text-muted ms-2 flex-shrink-0">${esc(item.productName)}</small>
            </button>
        `).join('');
        return `
            <h6>Copy Attribute</h6>
            <p class="text-muted small mb-3">Pick one — a copy will be added to the product.</p>
            ${items.length
                ? `<div class="list-group">${rows}</div>`
                : '<p class="text-muted small">No attributes in any product yet.</p>'}
            <div class="mt-3">
                <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Cancel</button>
            </div>
        `;
    },

    // ── Variants modal ───────────────────────────────────────────────────────

    variantsModal(product, editingVariant = null) {
        const attrs = product.attributes;

        if (attrs.length === 0) {
            return `
                <h6>Variants <span class="text-muted" style="font-family:'Geist',sans-serif;font-size:.85rem;font-weight:400">· ${esc(product.name)}</span></h6>
                <div class="empty">
                    <div class="empty-title">No attributes</div>
                    <div>Add attributes to this product first to create variants.</div>
                </div>
                <div class="mt-3">
                    <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Close</button>
                </div>
            `;
        }

        const variantRows = product.variants.map(v => {
            const isEditing = editingVariant?.id === v.id;
            const pills = attrs.map(a => {
                const impl = v.implementations.find(i => i.attributeId === a.id);
                return `<span class="pill pill-variant">
                    <span class="pill-key">${esc(a.key)}</span>${esc(impl?.value ?? '?')}
                </span>`;
            }).join(' ');
            return `
                <div class="variant-row ${isEditing ? 'editing' : ''}">
                    <div class="d-flex flex-wrap gap-1 align-items-center">
                        ${pills}
                        <span class="pill pill-price">$${parseFloat(v.price).toFixed(2)}</span>
                    </div>
                    <div class="d-flex gap-1 flex-shrink-0">
                        <button class="btn btn-xs"
                                style="font-size:.72rem;padding:.1rem .5rem;color:#16a34a;border:1px solid #86efac;background:#dcfce7"
                                data-action="manage-stock" data-product-id="${product.id}" data-id="${v.id}">Stock</button>
                        <button class="btn btn-outline-secondary btn-xs"
                                data-action="edit-variant" data-product-id="${product.id}" data-id="${v.id}">Edit</button>
                        <button class="btn btn-outline-danger btn-xs"
                                data-action="delete-variant" data-product-id="${product.id}" data-id="${v.id}">×</button>
                    </div>
                </div>
            `;
        }).join('');

        const selects = attrs.map(a => {
            const currentVal = editingVariant?.implementations.find(i => i.attributeId === a.id)?.value ?? '';
            const opts = a.values.map(v =>
                `<option value="${esc(v)}" ${v === currentVal ? 'selected' : ''}>${esc(v)}</option>`
            ).join('');
            return `
                <div class="mb-2">
                    <label class="form-label form-label-sm">${esc(a.key)}</label>
                    <select class="form-select form-select-sm" name="attr-${a.id}" required>
                        <option value="">— Select —</option>
                        ${opts}
                    </select>
                </div>
            `;
        }).join('');

        const editing = !!editingVariant;
        return `
            <h6>Variants <span class="text-muted" style="font-family:'Geist',sans-serif;font-size:.85rem;font-weight:400">· ${esc(product.name)}</span></h6>
            <p class="panel-label mb-2" style="margin-top:-.4rem">${attrs.map(a => esc(a.key)).join(' · ')}</p>

            <div style="max-height:220px;overflow-y:auto" class="mb-3">
                ${variantRows || `<div class="empty" style="padding:1.25rem">No variants yet.</div>`}
            </div>

            <hr class="my-3">
            <p class="panel-label mb-2" style="color:${editing ? 'var(--accent)' : ''}">
                ${editing ? 'Editing Variant' : 'Add Variant'}
            </p>
            <form id="variant-form">
                <input type="hidden" name="product-id" value="${product.id}">
                <input type="hidden" name="variant-id" value="${editingVariant ? editingVariant.id : ''}">
                ${selects}
                <div class="mb-3">
                    <label class="form-label form-label-sm">Price</label>
                    <input type="number" class="form-control form-control-sm" name="price"
                           min="0" step="0.01" placeholder="0.00"
                           value="${editing ? parseFloat(editingVariant.price).toFixed(2) : ''}" required>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" data-action="save-variant">
                        ${editing ? 'Update' : 'Add Variant'}
                    </button>
                    ${editing ? `<button type="button" class="btn btn-outline-secondary btn-sm"
                                         data-action="cancel-edit-variant"
                                         data-product-id="${product.id}">Cancel</button>` : ''}
                    <button type="button" class="btn btn-outline-secondary btn-sm ms-auto" data-action="close-modal">Close</button>
                </div>
            </form>
        `;
    },

    // ── Brands ────────────────────────────────────────────────────────────────

    brandCard(brand) {
        const initial = (brand.name || '?').trim().charAt(0).toUpperCase();
        return `
            <div class="card brand-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center gap-3">
                            <span class="brand-mark">${esc(initial)}</span>
                            <span class="brand-name">${esc(brand.name)}</span>
                        </div>
                        <div class="d-flex gap-1">
                            <button class="btn btn-sm btn-outline-secondary" data-action="edit-brand" data-id="${brand.id}">Edit</button>
                            <button class="btn btn-sm btn-outline-danger" data-action="delete-brand" data-id="${brand.id}">Delete</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    brandsTab(brands) {
        return `
            <div class="section-bar">
                <div>
                    <h6>Brands<span class="count">${brands.length} total</span></h6>
                </div>
                <button class="btn btn-primary btn-sm" data-action="new-brand">+ New Brand</button>
            </div>
            ${brands.length
                ? brands.map(b => this.brandCard(b)).join('')
                : `<div class="empty">
                       <div class="empty-title">No brands yet</div>
                       <div>Add a brand to associate it with your products.</div>
                   </div>`}
        `;
    },

    brandForm(brand) {
        return `
            <h6>${brand ? 'Edit Brand' : 'New Brand'}</h6>
            <form id="brand-form">
                <input type="hidden" name="id" value="${brand ? brand.id : ''}">
                <div class="mb-3">
                    <label class="form-label form-label-sm">Name</label>
                    <input type="text" class="form-control form-control-sm" name="name"
                           value="${brand ? esc(brand.name) : ''}" required>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" data-action="save-brand">Save</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Cancel</button>
                </div>
            </form>
        `;
    },

    // ── Stock modal ───────────────────────────────────────────────────────────

    stockModal(product, variant, editingStock = null) {
        const today  = new Date().toISOString().split('T')[0];
        const attrs  = product.attributes;
        const pills  = attrs.map(a => {
            const impl = variant.implementations.find(i => i.attributeId === a.id);
            return `<span class="badge rounded-pill" style="background:#e0e7ff;color:#3730a3">
                <span style="opacity:.6;font-size:.7em">${esc(a.key)}</span> ${esc(impl?.value ?? '?')}
            </span>`;
        }).join(' ');

        const totalStock = variant.historical_stocks.reduce((sum, s) => sum + s.quantity, 0);

        const rows = [...variant.historical_stocks].reverse().map(s => {
            const isEditing = editingStock?.id === s.id;
            return `
            <tr style="${isEditing ? 'background:#f5f3ff' : ''}">
                <td>${esc(s.date)}</td>
                <td class="text-end">${s.quantity}</td>
                <td class="text-end">$${parseFloat(s.cost_unit_price).toFixed(2)}</td>
                <td class="text-end">$${(s.quantity * s.cost_unit_price).toFixed(2)}</td>
                <td>
                    <div class="d-flex gap-1 justify-content-end">
                        <button class="btn btn-outline-secondary btn-xs"
                                data-action="edit-stock"
                                data-product-id="${product.id}" data-variant-id="${variant.id}" data-id="${s.id}">Edit</button>
                        <button class="btn btn-outline-danger btn-xs"
                                data-action="delete-stock"
                                data-product-id="${product.id}" data-variant-id="${variant.id}" data-id="${s.id}">×</button>
                    </div>
                </td>
            </tr>`;
        }).join('');

        const editing = !!editingStock;
        return `
            <div class="d-flex align-items-center gap-2 mb-2">
                <h6 class="fw-semibold mb-0">Stock</h6>
                <span class="text-muted small">— ${esc(product.name)}</span>
            </div>
            <div class="d-flex flex-wrap gap-1 mb-3">${pills || '<small class="text-muted">—</small>'}</div>

            <div class="rounded-2 p-2 mb-3 d-flex align-items-center justify-content-between"
                 style="background:#f0fdf4">
                <span style="font-size:.7rem;font-weight:700;letter-spacing:.08em;color:#16a34a;text-transform:uppercase">
                    Stock actual
                </span>
                <span class="badge rounded-pill" style="background:#bbf7d0;color:#166534;font-size:1rem;padding:.3rem .75rem">
                    ${totalStock}
                </span>
            </div>

            ${variant.historical_stocks.length ? `
            <div style="max-height:160px;overflow-y:auto" class="mb-3">
                <table class="table table-sm table-borderless mb-0" style="font-size:.8rem">
                    <thead>
                        <tr class="text-muted" style="font-size:.7rem">
                            <th>Fecha</th>
                            <th class="text-end">Cant.</th>
                            <th class="text-end">Costo unit.</th>
                            <th class="text-end">Total</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>` : '<p class="text-muted small mb-3">Sin entradas aún.</p>'}

            <hr class="my-2">
            <p class="small fw-semibold mb-2" style="color:${editing ? '#6366f1' : 'inherit'}">
                ${editing ? 'Editando entrada' : 'Agregar entrada'}
            </p>
            <form id="stock-form">
                <input type="hidden" name="product-id" value="${product.id}">
                <input type="hidden" name="variant-id" value="${variant.id}">
                <input type="hidden" name="stock-id"   value="${editing ? editingStock.id : ''}">
                <div class="row g-2 mb-3">
                    <div class="col-4">
                        <label class="form-label form-label-sm">Cantidad</label>
                        <input type="number" class="form-control form-control-sm" name="quantity"
                               min="1" step="1" value="${editing ? editingStock.quantity : ''}" required>
                    </div>
                    <div class="col-4">
                        <label class="form-label form-label-sm">Fecha</label>
                        <input type="date" class="form-control form-control-sm" name="date"
                               value="${editing ? editingStock.date : today}" required>
                    </div>
                    <div class="col-4">
                        <label class="form-label form-label-sm">Costo unit.</label>
                        <input type="number" class="form-control form-control-sm" name="cost_unit_price"
                               min="0" step="0.01" placeholder="0.00"
                               value="${editing ? editingStock.cost_unit_price : ''}">
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button type="button" class="btn btn-primary btn-sm" data-action="save-stock">
                        ${editing ? 'Guardar' : 'Agregar'}
                    </button>
                    ${editing ? `<button type="button" class="btn btn-outline-secondary btn-sm"
                                         data-action="cancel-edit-stock"
                                         data-product-id="${product.id}" data-variant-id="${variant.id}">Cancelar</button>` : ''}
                    <button type="button" class="btn btn-outline-secondary btn-sm"
                            data-action="back-to-variants" data-product-id="${product.id}">Volver</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm ms-auto"
                            data-action="close-modal">Cerrar</button>
                </div>
            </form>
        `;
    }
};
