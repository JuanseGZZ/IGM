const BASE = "http://localhost:8000/api";

const API = {
    bring: async () => {
        const res = await fetch(`${BASE}/state`);
        if (!res.ok) throw new Error(`Bring failed: ${res.status}`);
        const raw = await res.json();
        return {
            products: raw.products.map(Product.fromJson),
            brands:   raw.brands.map(Brand.fromJson)
        };
    },

    save: async (state) => {
        const res = await fetch(`${BASE}/state`, {
            method:  "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                products: state.products.map(p => p.toJson()),
                brands:   state.brands.map(b => b.toJson())
            })
        });
        if (!res.ok) throw new Error(`Save failed: ${res.status}`);
    }
};
