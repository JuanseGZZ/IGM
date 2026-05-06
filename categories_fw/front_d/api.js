// api.js — comunicación con la API REST del catálogo

const API_BASE = "http://localhost:8000";

// ── HTTP ────────────────────────────────────────────────────────────────────

export async function saveCatalog(payload) {
  const res = await fetch(`${API_BASE}/catalog`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  if (!res.ok && res.status !== 422) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

export async function fetchCatalog() {
  const res = await fetch(`${API_BASE}/catalog`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Serialización (handler + attrStore → payload API) ───────────────────────

export function buildAPIPayload(handler, attrStore) {
  const attributes = attrStore.attrs.map(a => ({
    id:          a.id,
    key:         a.key,
    name:        a.name,
    data_type:   a.data_type,
    is_static:   a.is_static,
    enum_values: a.enum_values ?? [],
  }));

  const topCats = handler.root.listaHijos.filter(c => c.chartType === "category");
  if (topCats.length === 0) return { attributes, tree: null };

  function serCategory(chart) {
    const m = chart.model ?? {};
    return {
      id:            m.id ?? null,
      name:          m.name ?? "",
      attribute_ids: (m.attributes ?? []).map(a => a.id).filter(id => id != null),
      subcategories: chart.listaHijos.filter(c => c.chartType === "category").map(serCategory),
      products:      chart.listaHijos.filter(c => c.chartType === "product").map(serProduct),
    };
  }

  function serProduct(chart) {
    const m = chart.model ?? {};
    return {
      id:          m.id ?? null,
      code:        m.code        ?? "",
      title:       m.title       ?? "",
      price:       m.price       ?? 0,
      description: m.description ?? "",
      brand:       m.brand       ?? "",
      attributes_implementations: (m.attributes_implementations ?? []).map(ai => ({
        attribute_key: ai.attribute?.key ?? ai.key ?? "",
        value:         ai.value,
      })),
      variants: chart.listaHijos.filter(c => c.chartType === "variant").map(serVariant),
    };
  }

  function serVariant(chart) {
    const m = chart.model ?? {};
    return {
      id:                        m.id ?? null,
      attribute_implementations: (m.attribute_implementations ?? []).map(ai => ({
        attribute_key: ai.attribute?.key ?? ai.key ?? "",
        value:         ai.value,
      })),
    };
  }

  const tree = topCats.length === 1
    ? serCategory(topCats[0])
    : {
        id:            null,
        name:          "Catálogo",
        attribute_ids: [],
        subcategories: topCats.map(serCategory),
        products:      [],
      };

  return { attributes, tree };
}

// ── Deserialización (payload API → handler + attrStore) ──────────────────────

export function loadFromAPIData(handler, attrStore, data) {
  handler.reset();
  attrStore.attrs  = [];
  attrStore.lastId = 0;

  for (const a of data.attributes ?? []) {
    attrStore.attrs.push({ ...a, enum_values: a.enum_values ?? [] });
    if ((a.id ?? 0) > attrStore.lastId) attrStore.lastId = a.id;
  }
  attrStore._save();

  if (!data.tree) return;

  function buildCategory(apiCat, parentId) {
    const attrs = (apiCat.attribute_ids ?? [])
      .map(id => attrStore.attrs.find(a => a.id === id))
      .filter(Boolean);
    const chart = handler.addNodeTo(parentId, "category", {
      id:         apiCat.id,
      name:       apiCat.name,
      attributes: attrs,
    });
    if (!chart) return;
    for (const sub  of apiCat.subcategories ?? []) buildCategory(sub,  chart.id);
    for (const prod of apiCat.products      ?? []) buildProduct(prod,  chart.id);
  }

  function buildProduct(apiProd, parentId) {
    const impls = (apiProd.attributes_implementations ?? []).map(ai => ({
      attribute: attrStore.attrs.find(a => a.key === ai.attribute_key) ?? { key: ai.attribute_key },
      value:     ai.value,
      id:        null,
    }));
    const chart = handler.addNodeTo(parentId, "product", {
      id:                         apiProd.id,
      code:                       apiProd.code,
      title:                      apiProd.title,
      price:                      apiProd.price,
      description:                apiProd.description,
      brand:                      apiProd.brand,
      attributes_implementations: impls,
    });
    if (!chart) return;
    for (const v of apiProd.variants ?? []) buildVariant(v, chart.id);
  }

  function buildVariant(apiVar, parentId) {
    const impls = (apiVar.attribute_implementations ?? []).map(ai => ({
      attribute: attrStore.attrs.find(a => a.key === ai.attribute_key) ?? { key: ai.attribute_key },
      value:     ai.value,
      id:        null,
    }));
    handler.addNodeTo(parentId, "variant", {
      id:                        apiVar.id,
      attribute_implementations: impls,
    });
  }

  buildCategory(data.tree, 0);
}
