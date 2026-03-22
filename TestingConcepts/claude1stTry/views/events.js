// ── State ─────────────────────────────────────────────────────────────────────

const State = {
  attributes: [],
  categories: [],
  products:   [],
  activeSection: 'attributes',
  editingId: null,
  formMode: null, // 'attribute' | 'category' | 'product'
};

// ── Services ──────────────────────────────────────────────────────────────────

const Services = {

  // ── Attributes ──────────────────────────────────────────────────────────────

  async loadAttributes() {
    try {
      const data = await Api.attributes.list();
      State.attributes = data.map(a => new Attribute(a));
      Renders.attributesList(State.attributes);
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  openNewAttribute() {
    State.editingId = null;
    State.formMode = 'attribute';
    Renders.attributeForm(null);
    bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
  },

  async openEditAttribute(id) {
    try {
      const data = await Api.attributes.get(id);
      const attr = new Attribute(data);
      State.editingId = id;
      State.formMode = 'attribute';
      Renders.attributeForm(attr);
      bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async submitAttribute() {
    const raw = Renders.getAttributeFormData();
    if (!raw.key || !raw.name) return showToast('Completá los campos obligatorios.', 'warning');
    try {
      if (State.editingId) {
        await Api.attributes.update(State.editingId, Dtos.attributeUpdate(raw));
        showToast('Atributo actualizado.');
      } else {
        await Api.attributes.create(Dtos.attributeCreate(raw));
        showToast('Atributo creado.');
      }
      bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
      await Services.loadAttributes();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async deleteAttribute(id, name) {
    if (!confirm(`¿Eliminar el atributo "${name}"?`)) return;
    try {
      await Api.attributes.delete(id);
      showToast('Atributo eliminado.');
      await Services.loadAttributes();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  // ── Categories ──────────────────────────────────────────────────────────────

  async loadCategories() {
    try {
      const [cats, attrs] = await Promise.all([Api.categories.list(), Api.attributes.list()]);
      State.categories = cats.map(c => new Category(c));
      State.attributes = attrs.map(a => new Attribute(a));
      Renders.categoriesList(State.categories);
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  openNewCategory() {
    State.editingId = null;
    State.formMode = 'category';
    Renders.categoryForm(null, State.attributes);
    bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
  },

  async openEditCategory(id) {
    try {
      const [catData, attrsData] = await Promise.all([Api.categories.get(id), Api.attributes.list()]);
      const cat = new Category(catData);
      State.editingId = id;
      State.formMode = 'category';
      Renders.categoryForm(cat, attrsData.map(a => new Attribute(a)));
      bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async submitCategory() {
    const raw = Renders.getCategoryFormData();
    if (!raw.name) return showToast('El nombre es obligatorio.', 'warning');
    try {
      if (State.editingId) {
        await Api.categories.update(State.editingId, Dtos.categoryUpdate(raw));
        showToast('Categoría actualizada.');
      } else {
        await Api.categories.create(Dtos.categoryCreate(raw));
        showToast('Categoría creada.');
      }
      bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
      await Services.loadCategories();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async deleteCategory(id, name) {
    if (!confirm(`¿Eliminar la categoría "${name}"?`)) return;
    try {
      await Api.categories.delete(id);
      showToast('Categoría eliminada.');
      await Services.loadCategories();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  // ── Products ────────────────────────────────────────────────────────────────

  async loadProducts() {
    try {
      const data = await Api.products.list();
      State.products = data.map(p => new ProductSummary(p));
      Renders.productsList(State.products);
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async openNewProduct() {
    try {
      const [cats, attrs] = await Promise.all([Api.categories.list(), Api.attributes.list()]);
      State.editingId = null;
      State.formMode = 'product';
      Renders.productForm(null, cats.map(c => new Category(c)), attrs.map(a => new Attribute(a)));
      bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async openEditProduct(id) {
    try {
      const [prodData, cats, attrs] = await Promise.all([
        Api.products.get(id),
        Api.categories.list(),
        Api.attributes.list(),
      ]);
      const product = new Product(prodData);
      State.editingId = id;
      State.formMode = 'product';
      Renders.productForm(product, cats.map(c => new Category(c)), attrs.map(a => new Attribute(a)));
      bootstrap.Modal.getOrCreateInstance(document.getElementById('formModal')).show();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async submitProduct() {
    const raw = Renders.getProductFormData();
    if (!raw.code || !raw.title || !raw.price || !raw.category_id) {
      return showToast('Completá los campos obligatorios.', 'warning');
    }
    try {
      if (State.editingId) {
        await Api.products.update(State.editingId, Dtos.productUpdate(raw));
        showToast('Producto actualizado.');
      } else {
        await Api.products.create(Dtos.productCreate(raw));
        showToast('Producto creado.');
      }
      bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
      await Services.loadProducts();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async deleteProduct(id, name) {
    if (!confirm(`¿Eliminar el producto "${name}"?`)) return;
    try {
      await Api.products.delete(id);
      showToast('Producto eliminado.');
      await Services.loadProducts();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async openProductDetail(id) {
    try {
      const data = await Api.products.get(id);
      const product = new Product(data);
      Renders.productDetail(product);
      bootstrap.Modal.getOrCreateInstance(document.getElementById('productDetailModal')).show();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async addVariant(prodId) {
    const inputs = document.querySelectorAll('.variant-impl-input');
    const implementations = Array.from(inputs).map(el => {
      const value = el.type === 'checkbox' ? String(el.checked) : el.value;
      return Dtos.implementationIn(el.dataset.attrId, value);
    });
    try {
      await Api.products.addVariant(prodId, Dtos.variantIn(implementations));
      showToast('Variante agregada.');
      await Services.openProductDetail(prodId);
      await Services.loadProducts();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },

  async deleteVariant(prodId, variantId) {
    if (!confirm('¿Eliminar esta variante?')) return;
    try {
      await Api.products.deleteVariant(prodId, variantId);
      showToast('Variante eliminada.');
      await Services.openProductDetail(prodId);
      await Services.loadProducts();
    } catch (e) {
      showToast(e.message, 'danger');
    }
  },
};

// ── Navigation ────────────────────────────────────────────────────────────────

function switchSection(section) {
  document.querySelectorAll('.section').forEach(el => el.classList.add('d-none'));
  document.querySelectorAll('[data-section]').forEach(el => el.classList.remove('active'));

  document.getElementById(`section-${section}`).classList.remove('d-none');
  document.getElementById(`nav-${section}`).classList.add('active');
  State.activeSection = section;

  if (section === 'attributes') Services.loadAttributes();
  if (section === 'categories') Services.loadCategories();
  if (section === 'products')   Services.loadProducts();
}

// ── Event Bindings ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Sidebar nav
  document.querySelectorAll('[data-section]').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      switchSection(link.dataset.section);
    });
  });

  // New buttons
  document.getElementById('btn-new-attribute').addEventListener('click', () => Services.openNewAttribute());
  document.getElementById('btn-new-category').addEventListener('click',  () => Services.openNewCategory());
  document.getElementById('btn-new-product').addEventListener('click',   () => Services.openNewProduct());

  // Generic form submit
  document.getElementById('btn-form-submit').addEventListener('click', () => {
    if (State.formMode === 'attribute') Services.submitAttribute();
    if (State.formMode === 'category')  Services.submitCategory();
    if (State.formMode === 'product')   Services.submitProduct();
  });

  // Attributes list actions (delegated)
  document.getElementById('attributes-list').addEventListener('click', e => {
    const editBtn   = e.target.closest('.btn-edit-attr');
    const deleteBtn = e.target.closest('.btn-delete-attr');
    if (editBtn)   Services.openEditAttribute(parseInt(editBtn.dataset.id));
    if (deleteBtn) Services.deleteAttribute(parseInt(deleteBtn.dataset.id), deleteBtn.dataset.name);
  });

  // Categories list actions (delegated)
  document.getElementById('categories-list').addEventListener('click', e => {
    const editBtn   = e.target.closest('.btn-edit-cat');
    const deleteBtn = e.target.closest('.btn-delete-cat');
    if (editBtn)   Services.openEditCategory(parseInt(editBtn.dataset.id));
    if (deleteBtn) Services.deleteCategory(parseInt(deleteBtn.dataset.id), deleteBtn.dataset.name);
  });

  // Products list actions (delegated)
  document.getElementById('products-list').addEventListener('click', e => {
    const viewBtn   = e.target.closest('.btn-view-product');
    const editBtn   = e.target.closest('.btn-edit-product');
    const deleteBtn = e.target.closest('.btn-delete-product');
    if (viewBtn)   Services.openProductDetail(parseInt(viewBtn.dataset.id));
    if (editBtn)   Services.openEditProduct(parseInt(editBtn.dataset.id));
    if (deleteBtn) Services.deleteProduct(parseInt(deleteBtn.dataset.id), deleteBtn.dataset.name);
  });

  // Product detail modal actions (delegated)
  document.getElementById('productDetailBody').addEventListener('click', e => {
    const showVariantBtn   = e.target.closest('#btn-show-add-variant');
    const cancelVariantBtn = e.target.closest('#btn-cancel-variant');
    const confirmVariantBtn = e.target.closest('#btn-confirm-variant');
    const deleteVariantBtn = e.target.closest('.btn-delete-variant');

    if (showVariantBtn) {
      document.getElementById('add-variant-form').style.display = '';
      showVariantBtn.style.display = 'none';
    }
    if (cancelVariantBtn) {
      document.getElementById('add-variant-form').style.display = 'none';
      document.getElementById('btn-show-add-variant').style.display = '';
    }
    if (confirmVariantBtn) {
      Services.addVariant(parseInt(confirmVariantBtn.dataset.prodId));
    }
    if (deleteVariantBtn) {
      Services.deleteVariant(
        parseInt(deleteVariantBtn.dataset.prodId),
        parseInt(deleteVariantBtn.dataset.variantId)
      );
    }
  });

  // Initial load
  switchSection('attributes');
});