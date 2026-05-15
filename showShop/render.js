function esc(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

const Render = {

    grid(products) {
        if (!products.length) {
            return `<div class="col-12 empty-state">
                        <div style="font-size:3rem;margin-bottom:1rem">🛍️</div>
                        <div class="fw-semibold">No hay productos todavía</div>
                    </div>`;
        }
        return products.map(p => this.productCard(p)).join('');
    },

    productCard(product) {
        const prices   = product.variants.map(v => v.price);
        const minPrice = prices.length ? Math.min(...prices) : null;
        const maxPrice = prices.length ? Math.max(...prices) : null;
        const priceStr = minPrice === null     ? ''
                       : minPrice === maxPrice ? `$${minPrice.toFixed(2)}`
                       :                        `Desde $${minPrice.toFixed(2)}`;

        const photo = product.photo
            ? `<img class="prod-photo" src="${product.photo}" alt="${esc(product.name)}">`
            : `<div class="prod-photo-placeholder">📦</div>`;

        return `
            <div class="col-6 col-md-4">
                <div class="card shadow-sm prod-card h-100"
                     data-action="open-product" data-id="${product.id}">
                    ${photo}
                    <div class="card-body p-3">
                        ${product.brand
                            ? `<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin-bottom:.2rem">
                                   ${esc(product.brand.name)}
                               </div>`
                            : ''}
                        <div class="fw-semibold" style="font-size:.95rem;line-height:1.3">
                            ${esc(product.name)}
                        </div>
                        ${product.description
                            ? `<div class="text-muted mt-1" style="font-size:.78rem;line-height:1.4">
                                   ${esc(product.description)}
                               </div>`
                            : ''}
                        ${priceStr
                            ? `<div class="mt-2 fw-bold" style="color:#6366f1;font-size:.95rem">
                                   ${priceStr}
                               </div>`
                            : ''}
                    </div>
                </div>
            </div>
        `;
    },

    productModal(product, selection) {
        const photo = product.photo
            ? `<img src="${product.photo}"
                    style="width:100%;max-height:260px;object-fit:cover;display:block">`
            : '';

        const attrGroups = product.attributes.map(a => {
            const pills = a.values.map(v => `
                <button type="button"
                        class="attr-pill ${selection[a.id] === v ? 'selected' : ''}"
                        data-action="select-attr"
                        data-attr-id="${a.id}"
                        data-value="${esc(v)}">${esc(v)}</button>
            `).join('');
            return `
                <div class="mb-3">
                    <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;margin-bottom:.5rem">
                        ${esc(a.key)}
                    </div>
                    <div class="d-flex flex-wrap gap-2">${pills}</div>
                </div>
            `;
        }).join('');

        // Match selected combination to a variant
        const allSelected = product.attributes.length > 0 &&
                            Object.keys(selection).length === product.attributes.length;
        const matched = allSelected
            ? product.variants.find(v =>
                v.implementations.every(i => selection[i.attributeId] === i.value)
              )
            : null;

        let priceBlock = '';
        if (product.variants.length === 0) {
            priceBlock = '';
        } else if (matched) {
            priceBlock = `<div class="fw-bold" style="font-size:1.4rem;color:#6366f1">
                              $${parseFloat(matched.price).toFixed(2)}
                          </div>`;
        } else if (product.attributes.length === 0 && product.variants.length === 1) {
            priceBlock = `<div class="fw-bold" style="font-size:1.4rem;color:#6366f1">
                              $${parseFloat(product.variants[0].price).toFixed(2)}
                          </div>`;
        } else {
            priceBlock = `<div class="text-muted" style="font-size:.85rem">
                              Seleccioná las opciones para ver el precio
                          </div>`;
        }

        return `
            ${photo}
            <div class="p-4">
                ${product.brand
                    ? `<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;margin-bottom:.3rem">
                           ${esc(product.brand.name)}
                       </div>`
                    : ''}
                <h5 class="fw-bold mb-1">${esc(product.name)}</h5>
                ${product.description
                    ? `<p class="text-muted mb-3" style="font-size:.88rem">${esc(product.description)}</p>`
                    : '<div class="mb-3"></div>'}

                ${attrGroups}

                <div class="mt-1 mb-4">${priceBlock}</div>

                <button type="button"
                        class="btn btn-outline-secondary btn-sm"
                        data-action="close-modal">Cerrar</button>
            </div>
        `;
    }
};
