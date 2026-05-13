const DB_KEY = 'spm_state';

const LocalDB = {
    save(state) {
        localStorage.setItem(DB_KEY, JSON.stringify({
            products: state.products.map(p => p.toJson()),
            brands:   state.brands.map(b => b.toJson())
        }));
    },
    load() {
        try {
            const raw = JSON.parse(localStorage.getItem(DB_KEY) || '{}');
            return {
                products: (raw.products || []).map(Product.fromJson),
                brands:   (raw.brands   || []).map(Brand.fromJson)
            };
        } catch {
            return { products: [], brands: [] };
        }
    }
};
