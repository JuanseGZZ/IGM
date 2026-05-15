const CACHE_KEY = 'spm_shop_cache';

const LocalCache = {
    save(state) {
        try {
            localStorage.setItem(CACHE_KEY, JSON.stringify({
                products: state.products.map(p => p.toJson()),
                brands:   state.brands.map(b => b.toJson())
            }));
        } catch {}
    },

    load() {
        try {
            const raw = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
            return {
                products: (raw.products || []).map(Product.fromJson),
                brands:   (raw.brands   || []).map(Brand.fromJson)
            };
        } catch {
            return { products: [], brands: [] };
        }
    },

    clear() {
        localStorage.removeItem(CACHE_KEY);
    }
};
