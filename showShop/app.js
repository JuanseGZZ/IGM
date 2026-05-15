const Shop = {
    state: {
        products:  [],
        brands:    [],
        activeId:  null,   // product id open in modal
        selection: {}      // { [attrId]: value }
    },

    renderGrid() {
        const { products } = this.state;
        document.getElementById('subtitle').textContent =
            `${products.length} producto${products.length !== 1 ? 's' : ''}`;
        document.getElementById('grid').innerHTML = Render.grid(products);
    },

    openModal(productId) {
        this.state.activeId  = productId;
        this.state.selection = {};
        this._refreshModal();
        document.getElementById('modal-overlay').classList.add('open');
    },

    closeModal() {
        this.state.activeId  = null;
        this.state.selection = {};
        document.getElementById('modal-overlay').classList.remove('open');
    },

    _refreshModal() {
        const product = this.state.products.find(p => p.id === this.state.activeId);
        if (!product) return;
        document.getElementById('modal-body').innerHTML =
            Render.productModal(product, this.state.selection);
    },

    init() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;

            const action = btn.dataset.action;

            if (action === 'open-product') {
                this.openModal(btn.dataset.id);
            } else if (action === 'close-modal') {
                this.closeModal();
            } else if (action === 'select-attr') {
                this.state.selection[btn.dataset.attrId] = btn.dataset.value;
                this._refreshModal();
            }
        });

        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });

        API.bring().then(data => {
            this.state.products = data.products;
            this.state.brands   = data.brands;
            this.renderGrid();
        }).catch(() => {
            document.getElementById('grid').innerHTML =
                `<div class="col-12 empty-state">
                    <div style="font-size:2.5rem;margin-bottom:1rem">⚠️</div>
                    <div class="fw-semibold">No se pudo conectar con el backend</div>
                    <div class="mt-1" style="font-size:.85rem">
                        Levantá el servidor desde <code>short_products_manager/back</code>
                    </div>
                 </div>`;
        });
    }
};

document.addEventListener('DOMContentLoaded', () => Shop.init());
