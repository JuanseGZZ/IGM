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
    }
};
