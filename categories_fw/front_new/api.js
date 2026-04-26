const API = {
  BASE: 'http://localhost:8000',

  async _req(method, path, body = null) {
    Animations.spinner(true);
    try {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body !== null) opts.body = JSON.stringify(body);
      const res = await fetch(this.BASE + path, opts);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || res.statusText);
      return data;
    } finally {
      Animations.spinner(false);
    }
  },

  // ── GET ──────────────────────────────────────────────────────────────────
  categories:    ()       => API._req('GET',    '/categories'),
  attributes:    ()       => API._req('GET',    '/attributes'),
  products:      (catId)  => API._req('GET',    catId ? `/products?category_id=${catId}` : '/products'),
  product:       (id)     => API._req('GET',    `/products/${id}`),

  // ── CRUD ─────────────────────────────────────────────────────────────────
  createCategory:  (body) => API._req('POST',   '/categories',       body),
  createAttribute: (body) => API._req('POST',   '/attributes',       body),
  createProduct:   (body) => API._req('POST',   '/products',         body),
  deleteCategory:  (id)   => API._req('DELETE', `/categories/${id}`, null),
  deleteAttribute: (id)   => API._req('DELETE', `/attributes/${id}`, null),
  deleteProduct:   (id)   => API._req('DELETE', `/products/${id}`,   null),

  // ── Eventos de categoria ──────────────────────────────────────────────────
  changeFather:       (catId, body)         => API._req('PATCH',  `/categories/${catId}/father`,              body),
  addCatAttribute:    (catId, attrId, body) => API._req('POST',   `/categories/${catId}/attributes/${attrId}`, body),
  removeCatAttribute: (catId, attrId, body) => API._req('DELETE', `/categories/${catId}/attributes/${attrId}`, body),

  // ── Eventos de producto ───────────────────────────────────────────────────
  changeProductCat: (prodId, newCatId, body) => API._req('PATCH',  `/products/${prodId}/category/${newCatId}`, body),
  addVariant:       (prodId, body)           => API._req('POST',   `/products/${prodId}/variants`,             body),
  removeVariant:    (prodId, varId)          => API._req('DELETE', `/products/${prodId}/variants/${varId}`,    null),
};
