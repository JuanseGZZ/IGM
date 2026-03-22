const BASE_URL = 'http://localhost:8000';

const Api = {
  async _fetch(method, path, body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(`${BASE_URL}${path}`, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
    return data;
  },

  attributes: {
    list:   ()        => Api._fetch('GET',    '/attributes'),
    get:    (id)      => Api._fetch('GET',    `/attributes/${id}`),
    create: (dto)     => Api._fetch('POST',   '/attributes', dto),
    update: (id, dto) => Api._fetch('PUT',    `/attributes/${id}`, dto),
    delete: (id)      => Api._fetch('DELETE', `/attributes/${id}`),
  },

  categories: {
    list:   ()        => Api._fetch('GET',    '/categories'),
    get:    (id)      => Api._fetch('GET',    `/categories/${id}`),
    create: (dto)     => Api._fetch('POST',   '/categories', dto),
    update: (id, dto) => Api._fetch('PUT',    `/categories/${id}`, dto),
    delete: (id)      => Api._fetch('DELETE', `/categories/${id}`),
  },

  products: {
    list:          ()               => Api._fetch('GET',    '/products'),
    get:           (id)             => Api._fetch('GET',    `/products/${id}`),
    create:        (dto)            => Api._fetch('POST',   '/products', dto),
    update:        (id, dto)        => Api._fetch('PUT',    `/products/${id}`, dto),
    delete:        (id)             => Api._fetch('DELETE', `/products/${id}`),
    addVariant:    (id, dto)        => Api._fetch('POST',   `/products/${id}/variants`, dto),
    deleteVariant: (id, variantId)  => Api._fetch('DELETE', `/products/${id}/variants/${variantId}`),
  },
};