const App = {
    state: {
        tab: 'products',
        products: [],
        brands: [],
        modal: null,            // { type: 'product'|'attr'|'attr-copy'|'brand', data: any }
        attrPendingValues: [],
        attrPendingKey: '',
        dirty: false
    },

    render() {
        const { tab, products, brands, modal } = this.state;

        document.getElementById('tabs').innerHTML = Render.tabs(tab);

        let content = '';
        if (tab === 'products') content = Render.productsTab(products);
        if (tab === 'brands')   content = Render.brandsTab(brands);
        document.getElementById('content').innerHTML = content;

        const overlay = document.getElementById('modal-overlay');
        if (modal) {
            let html = '';
            if (modal.type === 'product')   html = Render.productForm(modal.data, brands);
            if (modal.type === 'attr')      html = Render.attrForm(modal.data?.attr, this.state.attrPendingValues, this.state.attrPendingKey);
            if (modal.type === 'attr-copy') html = Render.attrCopyPicker(products, modal.data?.targetProductId);
            if (modal.type === 'variants')  html = Render.variantsModal(modal.data.product);
            if (modal.type === 'brand')     html = Render.brandForm(modal.data);
            if (modal.type === 'stock')     html = Render.stockModal(modal.data.product, modal.data.variant);
            document.getElementById('modal-body').innerHTML = html;
            overlay.classList.add('open');
            requestAnimationFrame(() => {
                const first = document.querySelector('#modal-body input[type="text"]');
                if (first) first.focus();
            });
        } else {
            overlay.classList.remove('open');
        }
    },

    openModal(type, data = null) {
        this.state.modal = { type, data };
        if (type === 'attr') {
            this.state.attrPendingValues = data?.attr ? [...data.attr.values] : [];
            this.state.attrPendingKey    = data?.attr ? data.attr.key : '';
        }
        this.render();
    },

    closeModal() {
        this.state.modal = null;
        this.render();
    },

    setDirty() {
        this.state.dirty = true;
        const el = document.getElementById('dirty-indicator');
        if (el) el.style.display = 'inline';
    },

    clearDirty() {
        this.state.dirty = false;
        const el = document.getElementById('dirty-indicator');
        if (el) el.style.display = 'none';
    },

    rerenderAttrModal() {
        document.getElementById('modal-body').innerHTML =
            Render.attrForm(this.state.modal.data?.attr, this.state.attrPendingValues, this.state.attrPendingKey);
    },

    // ── State mutations ───────────────────────────────────────────────────────

    upsertProduct(product) {
        const i = this.state.products.findIndex(p => p.id === product.id);
        if (i >= 0) this.state.products[i] = product;
        else this.state.products.push(product);
        this.setDirty();
    },

    upsertBrand(brand) {
        const i = this.state.brands.findIndex(b => b.id === brand.id);
        if (i >= 0) this.state.brands[i] = brand;
        else this.state.brands.push(brand);
        this.setDirty();
    },

    // ── Action handler ────────────────────────────────────────────────────────

    async handleAction(action, target) {
        const id = target.dataset.id;

        // Global DB
        if (action === 'db-bring') {
            const data = await API.bring();
            this.state.products = data.products;
            this.state.brands   = data.brands;
            this.render();
            this.clearDirty();
            return;
        }
        if (action === 'db-save') {
            await API.save(this.state);
            this.clearDirty();
            const btn = document.querySelector('[data-action="db-save"]');
            if (btn) {
                const orig = btn.textContent;
                btn.textContent = 'Saved!';
                btn.disabled = true;
                setTimeout(() => { btn.textContent = orig; btn.disabled = false; }, 1200);
            }
            return;
        }

        if (action === 'close-modal') { this.closeModal(); return; }

        // Products
        if (action === 'new-product')    { this.openModal('product', null); return; }
        if (action === 'edit-product')   { this.openModal('product', this.state.products.find(p => p.id === id)); return; }
        if (action === 'delete-product') {
            if (!confirm('Delete this product?')) return;
            this.state.products = this.state.products.filter(p => p.id !== id);
            this.setDirty();
            this.render();
            return;
        }

        // Attributes (belong to a product)
        if (action === 'new-attr') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            this.openModal('attr', { product, attr: null });
            return;
        }
        if (action === 'edit-attr') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const attr    = product?.attributes.find(a => a.id === id);
            this.openModal('attr', { product, attr });
            return;
        }
        if (action === 'delete-attr') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product || !confirm('Delete this attribute?')) return;
            product.attributes = product.attributes.filter(a => a.id !== id);
            this.setDirty();
            this.render();
            return;
        }

        // Stock
        if (action === 'manage-stock') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const variant = product?.variants.find(v => v.id === id);
            if (!product || !variant) return;
            this.openModal('stock', { product, variant });
            return;
        }
        if (action === 'back-to-variants') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product) return;
            this.openModal('variants', { product });
            return;
        }
        if (action === 'edit-stock') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const variant = product?.variants.find(v => v.id === target.dataset.variantId);
            const stock   = variant?.historical_stocks.find(s => s.id === id);
            if (!product || !variant || !stock) return;
            document.getElementById('modal-body').innerHTML = Render.stockModal(product, variant, stock);
            return;
        }
        if (action === 'cancel-edit-stock') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const variant = product?.variants.find(v => v.id === target.dataset.variantId);
            if (!product || !variant) return;
            document.getElementById('modal-body').innerHTML = Render.stockModal(product, variant);
            return;
        }
        if (action === 'delete-stock') {
            if (!confirm('¿Eliminar esta entrada de stock?')) return;
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const variant = product?.variants.find(v => v.id === target.dataset.variantId);
            if (!product || !variant) return;
            variant.historical_stocks = variant.historical_stocks.filter(s => s.id !== id);
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.stockModal(product, variant);
            return;
        }
        if (action === 'save-stock') {
            const form = document.getElementById('stock-form');
            if (!form.reportValidity()) return;
            const data    = new FormData(form);
            const product = this.state.products.find(p => p.id === data.get('product-id'));
            const variant = product?.variants.find(v => v.id === data.get('variant-id'));
            if (!product || !variant) return;
            const stockId = data.get('stock-id');
            const entry   = new Stock(
                stockId || genId(),
                parseFloat(data.get('quantity')),
                data.get('date'),
                parseFloat(data.get('cost_unit_price')) || 0
            );
            if (stockId) {
                const i = variant.historical_stocks.findIndex(s => s.id === stockId);
                if (i >= 0) variant.historical_stocks[i] = entry;
            } else {
                variant.historical_stocks.push(entry);
            }
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.stockModal(product, variant);
            return;
        }

        // Variant offer (bulk actions from product form)
        if (action === 'set-all-oferta') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product) return;
            const input = document.getElementById('global-oferta-input');
            const pct   = parseFloat(input?.value);
            if (isNaN(pct) || pct < 0 || pct > 100) { alert('Ingresá un porcentaje entre 0 y 100.'); return; }
            product.variants.forEach(v => { v.oferta = pct / 100; });
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.productForm(product, this.state.brands);
            return;
        }
        if (action === 'clear-all-oferta') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product) return;
            product.variants.forEach(v => { v.oferta = null; });
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.productForm(product, this.state.brands);
            return;
        }

        // Variants
        if (action === 'manage-variants') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            this.openModal('variants', { product });
            return;
        }
        if (action === 'edit-variant') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            const variant = product?.variants.find(v => v.id === id);
            if (!product || !variant) return;
            document.getElementById('modal-body').innerHTML = Render.variantsModal(product, variant);
            return;
        }
        if (action === 'cancel-edit-variant') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product) return;
            document.getElementById('modal-body').innerHTML = Render.variantsModal(product);
            return;
        }
        if (action === 'delete-variant') {
            const product = this.state.products.find(p => p.id === target.dataset.productId);
            if (!product) return;
            product.variants = product.variants.filter(v => v.id !== id);
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.variantsModal(product);
            return;
        }
        if (action === 'save-variant') {
            const form = document.getElementById('variant-form');
            if (!form.reportValidity()) return;
            const data      = new FormData(form);
            const product   = this.state.products.find(p => p.id === data.get('product-id'));
            if (!product) return;
            const variantId = data.get('variant-id');
            const price     = parseFloat(data.get('price')) || 0;
            const ofertaRaw = data.get('oferta');
            const oferta    = ofertaRaw !== '' && ofertaRaw !== null ? parseFloat(ofertaRaw) / 100 : null;
            const implementations = product.attributes.map(a =>
                new AttributeImplementation(a.id, data.get(`attr-${a.id}`))
            );
            const isDuplicate = product.variants.some(v => {
                if (variantId && v.id === variantId) return false; // skip self when editing
                return v.implementations.length === implementations.length &&
                    v.implementations.every(existing => {
                        const incoming = implementations.find(i => i.attributeId === existing.attributeId);
                        return incoming?.value === existing.value;
                    });
            });
            if (isDuplicate) { alert('This combination already exists.'); return; }
            if (variantId) {
                const i = product.variants.findIndex(v => v.id === variantId);
                if (i >= 0) {
                    const stocks = product.variants[i].historical_stocks;
                    product.variants[i] = new Variant(variantId, price, implementations, stocks, oferta);
                }
            } else {
                product.variants.push(new Variant(genId(), price, implementations, [], oferta));
            }
            this.setDirty();
            document.getElementById('modal-body').innerHTML = Render.variantsModal(product);
            return;
        }

        // Copy attr picker
        if (action === 'copy-attr') {
            this.openModal('attr-copy', { targetProductId: target.dataset.productId });
            return;
        }
        if (action === 'confirm-copy-attr') {
            const sourceProduct = this.state.products.find(p => p.id === target.dataset.sourceProductId);
            const sourceAttr    = sourceProduct?.attributes.find(a => a.id === target.dataset.attrId);
            const targetProduct = this.state.products.find(p => p.id === target.dataset.targetProductId);
            if (!sourceAttr || !targetProduct) return;
            targetProduct.attributes.push(new Attribute(genId(), sourceAttr.key, [...sourceAttr.values]));
            this.setDirty();
            this.closeModal();
            return;
        }

        // Brands
        if (action === 'new-brand')    { this.openModal('brand', null); return; }
        if (action === 'edit-brand')   { this.openModal('brand', this.state.brands.find(b => b.id === id)); return; }
        if (action === 'delete-brand') {
            if (!confirm('Delete this brand?')) return;
            this.state.brands = this.state.brands.filter(b => b.id !== id);
            this.setDirty();
            this.render();
            return;
        }

        // Save forms
        if (action === 'save-product') {
            const form = document.getElementById('product-form');
            if (!form.reportValidity()) return;
            this.handleProductSubmit(form);
            return;
        }
        if (action === 'save-attr') {
            const form = document.getElementById('attr-form');
            if (!form.reportValidity()) return;
            this.handleAttrSubmit(form);
            return;
        }
        if (action === 'save-brand') {
            const form = document.getElementById('brand-form');
            if (!form.reportValidity()) return;
            this.handleBrandSubmit(form);
            return;
        }

        // Attribute value editing
        if (action === 'add-value') {
            const input = document.getElementById('new-value-input');
            const val = input.value.trim();
            if (!val) return;
            const keyInput = document.querySelector('#attr-form [name="key"]');
            if (keyInput) this.state.attrPendingKey = keyInput.value;
            this.state.attrPendingValues.push(val);
            this.rerenderAttrModal();
            requestAnimationFrame(() => document.getElementById('new-value-input')?.focus());
            return;
        }
        if (action === 'remove-value') {
            const keyInput = document.querySelector('#attr-form [name="key"]');
            if (keyInput) this.state.attrPendingKey = keyInput.value;
            this.state.attrPendingValues.splice(parseInt(target.dataset.index, 10), 1);
            this.rerenderAttrModal();
            return;
        }
    },

    // ── Form handlers ─────────────────────────────────────────────────────────

    handleProductSubmit(form) {
        try {
            const data        = new FormData(form);
            const id          = data.get('id') || genId();
            const name        = (data.get('name') || '').trim();
            const description = (data.get('description') || '').trim();
            const brandId     = data.get('brand');
            const brand       = brandId ? (this.state.brands.find(b => b.id === brandId) ?? null) : null;
            const existing    = this.state.products.find(p => p.id === id);
            const photo       = data.get('photo') || null;
            this.upsertProduct(new Product(
                id, name, description,
                existing ? existing.attributes : [],
                brand,
                existing ? existing.variants   : [],
                photo
            ));
            this.closeModal();
        } catch (err) {
            console.error('handleProductSubmit:', err);
            alert('Error: ' + err.message);
        }
    },

    handleAttrSubmit(form) {
        try {
            const data    = new FormData(form);
            const id      = data.get('id') || genId();
            const key     = (data.get('key') || '').trim();
            const newAttr = new Attribute(id, key, [...this.state.attrPendingValues]);

            const product = this.state.modal.data.product;
            const i = product.attributes.findIndex(a => a.id === id);
            if (i >= 0) product.attributes[i] = newAttr;
            else product.attributes.push(newAttr);

            this.setDirty();
            this.closeModal();
        } catch (err) {
            console.error('handleAttrSubmit:', err);
            alert('Error: ' + err.message);
        }
    },

    handleBrandSubmit(form) {
        try {
            const data = new FormData(form);
            const id   = data.get('id') || genId();
            const name = (data.get('name') || '').trim();
            this.upsertBrand(new Brand(id, name));
            this.closeModal();
        } catch (err) {
            console.error('handleBrandSubmit:', err);
            alert('Error: ' + err.message);
        }
    },

    // ── Init ──────────────────────────────────────────────────────────────────

    init() {
        window.addEventListener('beforeunload', (e) => {
            if (this.state.dirty) e.preventDefault();
        });

        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (btn) {
                e.preventDefault();
                this.handleAction(btn.dataset.action, btn);
                return;
            }
            const tab = e.target.closest('[data-tab]');
            if (tab) {
                this.state.tab = tab.dataset.tab;
                this.render();
            }
        });

        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });

        document.addEventListener('change', (e) => {
            if (e.target.id !== 'photo-input') return;
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (evt) => {
                const src = evt.target.result;
                document.getElementById('photo-data').value = src;
                const preview = document.getElementById('photo-preview');
                preview.src   = src;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter') return;
            if (e.target.id === 'new-value-input') {
                e.preventDefault();
                document.querySelector('[data-action="add-value"]')?.click();
                return;
            }
            // Prevent native form submission (page reload) and trigger save instead
            if (e.target.matches('#modal-body input[type="text"]')) {
                e.preventDefault();
                e.target.closest('form')?.querySelector('[data-action^="save-"]')?.click();
            }
        });

        this.render();

        API.bring().then(data => {
            this.state.products = data.products;
            this.state.brands   = data.brands;
            this.render();
        }).catch(() => {
            alert('No se pudo conectar con el backend. Levantá el servidor con:\n\ncd back\npython -m uvicorn app.main:app --reload');
        });
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
