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
            `<span class="badge rounded-pill" style="background:#e0e7ff;color:#3730a3;font-weight:500">${esc(v)}</span>`
        ).join(' ');
        return `
            <div class="d-flex align-items-center gap-2 py-1">
                <span class="badge rounded-2 text-nowrap"
                      style="background:#c7d2fe;color:#3730a3;font-size:.72rem;min-width:70px;text-align:center">
                    ${esc(attr.key)}
                </span>
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
            <div class="card mb-3 shadow-sm" style="border-left:4px solid #6366f1">
                <div class="card-body p-3">

                    <!-- Header -->
                    <div class="d-flex justify-content-between align-items-start gap-3 mb-3">
                        <div>
                            <span class="fw-bold" style="font-size:1rem">${esc(product.name)}</span>
                            ${brandName
                                ? `<span class="badge ms-2 fw-normal"
                                         style="background:#dcfce7;color:#166534;font-size:.75rem">${esc(brandName)}</span>`
                                : ''}
                            ${product.description
                                ? `<div class="text-muted mt-1" style="font-size:.82rem">${esc(product.description)}</div>`
                                : ''}
                        </div>
                        <div class="d-flex gap-1 flex-shrink-0">
                            <button class="btn btn-outline-secondary btn-sm" data-action="edit-product" data-id="${product.id}">Edit</button>
                            <button class="btn btn-outline-danger btn-sm" data-action="delete-product" data-id="${product.id}">Delete</button>
                        </div>
                    </div>

                    <!-- Attributes section -->
                    <div class="rounded-2 p-2 mb-2" style="background:#f5f3ff">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span style="font-size:.65rem;font-weight:700;letter-spacing:.08em;color:#6366f1;text-transform:uppercase">
                                Attributes
                            </span>
                            <div class="d-flex gap-1">
                                <button class="btn btn-xs" style="font-size:.72rem;padding:.1rem .5rem;color:#6366f1;border:1px solid #c7d2fe;background:#ede9fe"
                                        data-action="new-attr" data-product-id="${product.id}">+ Add</button>
                                <button class="btn btn-xs btn-outline-secondary" style="font-size:.72rem;padding:.1rem .5rem"
                                        data-action="copy-attr" data-product-id="${product.id}">Copy</button>
                            </div>
                        </div>
                        <div class="d-flex flex-column gap-1">
                            ${attrRows || '<small class="text-muted">No attributes yet</small>'}
                        </div>
                    </div>

                    <!-- Variants section -->
                    <div class="rounded-2 p-2" style="background:#f0fdf4">
                        <div class="d-flex justify-content-between align-items-center">
                            <span style="font-size:.65rem;font-weight:700;letter-spacing:.08em;color:#16a34a;text-transform:uppercase">
                                Variants
                                <span class="badge rounded-pill ms-1"
                                      style="background:#bbf7d0;color:#166534;font-size:.65rem">${vCount}</span>
                            </span>
                            <button class="btn btn-xs" style="font-size:.72rem;padding:.1rem .5rem;color:#16a34a;border:1px solid #86efac;background:#dcfce7"
                                    data-action="manage-variants" data-product-id="${product.id}">Manage</button>
                        </div>
                    </div>

                </div>
            </div>
        `;
    },

    productsTab(products) {
        return `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-semibold">Products</h6>
                <button class="btn btn-primary btn-sm" data-action="new-product">+ New Product</button>
            </div>
            ${products.length
                ? products.map(p => this.productCard(p)).join('')
                : '<p class="text-muted small">No products yet.</p>'}
        `;
    },

    productForm(product, allBrands) {
        const brandOpts = allBrands.map(b =>
            `<option value="${b.id}" ${product?.brand?.id === b.id ? 'selected' : ''}>${esc(b.name)}</option>`
        ).join('');
        return `
            <h6 class="fw-semibold mb-3">${product ? 'Edit Product' : 'New Product'}</h6>
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
            <span class="badge rounded-pill d-inline-flex align-items-center gap-1"
                  style="background:#e0e7ff;color:#3730a3">
                ${esc(v)}
                <button type="button" class="btn-close" style="font-size:.5rem;filter:none;opacity:.6"
                        data-action="remove-value" data-index="${i}" aria-label="Remove"></button>
            </span>
        `).join(' ');
        return `
            <h6 class="fw-semibold mb-3">${attr ? 'Edit Attribute' : 'New Attribute'}</h6>
            <form id="attr-form">
                <input type="hidden" name="id" value="${attr ? attr.id : ''}">
                <div class="mb-3">
                    <label class="form-label form-label-sm">Key <small class="text-muted">(e.g. Color, Size)</small></label>
                    <input type="text" class="form-control form-control-sm" name="key" value="${esc(key)}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label form-label-sm">Values</label>
                    <div class="d-flex flex-wrap gap-1 mb-2 p-2 rounded-2" style="min-height:36px;background:#f5f3ff" id="values-preview">
                        ${valueBadges || '<small class="text-muted">No values yet</small>'}
                    </div>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" id="new-value-input" placeholder="Type and press Enter or Add...">
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
                    class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2"
                    data-action="confirm-copy-attr"
                    data-source-product-id="${item.productId}"
                    data-attr-id="${item.attr.id}"
                    data-target-product-id="${targetProductId}">
                <span class="badge rounded-2 me-2" style="background:#c7d2fe;color:#3730a3">${esc(item.attr.key)}</span>
                <span class="d-flex align-items-center gap-1 flex-wrap flex-grow-1">
                    ${item.attr.values.map(v =>
                        `<small class="badge rounded-pill" style="background:#e0e7ff;color:#3730a3">${esc(v)}</small>`
                    ).join('')}
                </span>
                <small class="text-muted ms-2 flex-shrink-0">${esc(item.productName)}</small>
            </button>
        `).join('');
        return `
            <h6 class="fw-semibold mb-2">Copy Attribute</h6>
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
                <h6 class="fw-semibold mb-3">Variants — ${esc(product.name)}</h6>
                <p class="text-muted small">Add attributes to this product first.</p>
                <button type="button" class="btn btn-outline-secondary btn-sm" data-action="close-modal">Close</button>
            `;
        }

        const variantRows = product.variants.map(v => {
            const isEditing = editingVariant?.id === v.id;
            const pills = attrs.map(a => {
                const impl = v.implementations.find(i => i.attributeId === a.id);
                return `<span class="badge rounded-pill" style="background:#e0e7ff;color:#3730a3">
                    <span style="opacity:.6;font-size:.7em">${esc(a.key)}</span> ${esc(impl?.value ?? '?')}
                </span>`;
            }).join(' ');
            return `
                <div class="d-flex justify-content-between align-items-center py-2 border-bottom gap-2
                            ${isEditing ? 'rounded px-2' : ''}"
                     style="${isEditing ? 'background:#f5f3ff' : ''}">
                    <div class="d-flex flex-wrap gap-1 align-items-center">
                        ${pills}
                        <span class="badge rounded-pill ms-1" style="background:#dcfce7;color:#166534">
                            $${parseFloat(v.price).toFixed(2)}
                        </span>
                    </div>
                    <div class="d-flex gap-1 flex-shrink-0">
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
                    <label class="form-label form-label-sm d-flex align-items-center gap-1">
                        <span class="badge rounded-2" style="background:#c7d2fe;color:#3730a3">${esc(a.key)}</span>
                    </label>
                    <select class="form-select form-select-sm" name="attr-${a.id}" required>
                        <option value="">— Select —</option>
                        ${opts}
                    </select>
                </div>
            `;
        }).join('');

        const editing = !!editingVariant;
        return `
            <div class="d-flex align-items-center gap-2 mb-1">
                <h6 class="fw-semibold mb-0">Variants</h6>
                <span class="text-muted small">— ${esc(product.name)}</span>
            </div>
            <p class="text-muted mb-2" style="font-size:.75rem">${attrs.map(a => esc(a.key)).join(' · ')}</p>

            <div style="max-height:200px;overflow-y:auto" class="mb-3">
                ${variantRows || '<p class="text-muted small mb-0">No variants yet.</p>'}
            </div>

            <hr class="my-2">
            <p class="small fw-semibold mb-2" style="color:${editing ? '#6366f1' : 'inherit'}">
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
        return `
            <div class="card mb-2 shadow-sm" style="border-left:4px solid #16a34a">
                <div class="card-body py-2 px-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center gap-2">
                            <span class="badge rounded-2" style="background:#dcfce7;color:#166534;font-size:.7rem">Brand</span>
                            <span class="fw-semibold">${esc(brand.name)}</span>
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
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-semibold">Brands</h6>
                <button class="btn btn-primary btn-sm" data-action="new-brand">+ New Brand</button>
            </div>
            ${brands.length
                ? brands.map(b => this.brandCard(b)).join('')
                : '<p class="text-muted small">No brands yet.</p>'}
        `;
    },

    brandForm(brand) {
        return `
            <h6 class="fw-semibold mb-3">${brand ? 'Edit Brand' : 'New Brand'}</h6>
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
    }
};
