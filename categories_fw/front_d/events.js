import { Handler }                              from "./Handler.js";
import { CHART_TYPE, CHART_BG }                from "./charts.js";
import { Category, Product, Variant, Attribute } from "./models.js";
import { showMenu, showGestorDialog, initZoom } from "./ui.js";
import { Gestor }                               from "./Gestor.js";
import { attrStore }                            from "./stores/attrStore.js";
import { catalogStore }                         from "./stores/catalogStore.js";
import { renderAttrList, renderImplsEditable }  from "./renders/renderEditModal.js";
import { renderAttrRows, renderEnumValues }     from "./renders/renderAttrsModal.js";
import { renderPicker as renderPickerView }     from "./renders/renderAttrPicker.js";
import { saveCatalog, fetchCatalog, buildAPIPayload, loadFromAPIData } from "./api.js";

// ── Inicialización ─────────────────────────────────────────────────────────────

attrStore.load();

const handler = new Handler();
const gestor  = new Gestor(handler);

const _render = handler.render.bind(handler);
handler.render = (opts) => {
  _render(opts);
  catalogStore.save(handler);
};

catalogStore.load(handler);
handler.treeToMax();
handler.render({ container: "#igm-board" });

// ── Canvas virtual ─────────────────────────────────────────────────────────────

const CANVAS_PADDING = 2000;
const boardContainer = document.querySelector("#igm-board-container");
if (boardContainer) {
  requestAnimationFrame(() => {
    boardContainer.scrollLeft = CANVAS_PADDING - 80;
    boardContainer.scrollTop  = CANVAS_PADDING - 80;
  });
}

// ── Layout actors ──────────────────────────────────────────────────────────────

const layoutActors = {
  organigram: {
    add(base, dir, chartType, model) {
      if (dir === "down") {
        handler.addNodeTo(base.id, chartType, model);
      } else if (dir === "right") {
        if (base.idParent === null) { alert("El nodo raíz no puede tener hermano."); return; }
        handler.addNodeTo(base.idParent, chartType, model);
      }
      handler.treeToMax();
      handler.render({ container: "#igm-board" });
    },
    addRoot(chartType, model) {
      handler.addNodeTo(0, chartType, model);
      handler.treeToMax();
      handler.render({ container: "#igm-board" });
    },
    deleteNode(id) {
      handler.deleteByIdAndRefresh(id);
    },
    moveToChild(fromId, toId) {
      if (handler.moveNode(fromId, toId)) {
        handler.treeToMax();
        handler.render({ container: "#igm-board" });
      }
    },
    moveToSibling(fromId, afterId) {
      if (handler.moveNodeAfter(fromId, afterId)) {
        handler.treeToMax();
        handler.render({ container: "#igm-board" });
      }
    },
  },
};

const currentLayout = "organigram";

// ── Crear modelo por tipo (abre el modal correspondiente) ──────────────────────

function createModel(chartType, onReady) {
  if (chartType === CHART_TYPE.CATEGORY) _openNewCatModal(onReady);
  else if (chartType === CHART_TYPE.PRODUCT) _openNewProdModal(onReady);
  else if (chartType === CHART_TYPE.VARIANT) _openNewVarModal(onReady);
  else onReady(null);
}

function _openNewCatModal(onReady) {
  const overlay   = document.getElementById("igm-new-cat-overlay");
  const nameInput = document.getElementById("igm-new-cat-name");
  nameInput.value = "";

  const newOk     = document.getElementById("igm-new-cat-ok").cloneNode(true);
  const newCancel = document.getElementById("igm-new-cat-cancel").cloneNode(true);
  document.getElementById("igm-new-cat-ok").replaceWith(newOk);
  document.getElementById("igm-new-cat-cancel").replaceWith(newCancel);

  const ac  = new AbortController();
  const sig = { signal: ac.signal };

  const close = (model) => {
    ac.abort();
    overlay.classList.add("igm-hidden");
    onReady(model);
  };

  newOk.addEventListener("click", () => {
    const name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    close({ name, id: null, attributes: [] });
  }, sig);
  newCancel.addEventListener("click", () => close(null), sig);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(null); }, sig);
  nameInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); newOk.click(); }
    if (e.key === "Escape") close(null);
  }, sig);

  overlay.classList.remove("igm-hidden");
  nameInput.focus();
}

function _openNewProdModal(onReady) {
  const overlay    = document.getElementById("igm-new-prod-overlay");
  const titleInput = document.getElementById("igm-new-prod-title");
  const codeInput  = document.getElementById("igm-new-prod-code");
  const priceInput = document.getElementById("igm-new-prod-price");
  const brandInput = document.getElementById("igm-new-prod-brand");
  titleInput.value = codeInput.value = priceInput.value = brandInput.value = "";

  const newOk     = document.getElementById("igm-new-prod-ok").cloneNode(true);
  const newCancel = document.getElementById("igm-new-prod-cancel").cloneNode(true);
  document.getElementById("igm-new-prod-ok").replaceWith(newOk);
  document.getElementById("igm-new-prod-cancel").replaceWith(newCancel);

  const ac  = new AbortController();
  const sig = { signal: ac.signal };

  const close = (model) => {
    ac.abort();
    overlay.classList.add("igm-hidden");
    onReady(model);
  };

  newOk.addEventListener("click", () => {
    const title = titleInput.value.trim();
    if (!title) { titleInput.focus(); return; }
    const code  = codeInput.value.trim() || `SKU-${Date.now()}`;
    const price = parseFloat(priceInput.value) || 0;
    const brand = brandInput.value.trim();
    close({ title, code, price, brand, description: "", id: null, attributes_implementations: [] });
  }, sig);
  newCancel.addEventListener("click", () => close(null), sig);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(null); }, sig);
  titleInput.addEventListener("keydown", (e) => { if (e.key === "Escape") close(null); }, sig);

  overlay.classList.remove("igm-hidden");
  titleInput.focus();
}

function _openNewVarModal(onReady) {
  const overlay = document.getElementById("igm-new-var-overlay");

  const newOk     = document.getElementById("igm-new-var-ok").cloneNode(true);
  const newCancel = document.getElementById("igm-new-var-cancel").cloneNode(true);
  document.getElementById("igm-new-var-ok").replaceWith(newOk);
  document.getElementById("igm-new-var-cancel").replaceWith(newCancel);

  const ac  = new AbortController();
  const sig = { signal: ac.signal };

  const close = (model) => {
    ac.abort();
    overlay.classList.add("igm-hidden");
    onReady(model);
  };

  newOk.addEventListener("click", () => close({ id: null, attribute_implementations: [] }), sig);
  newCancel.addEventListener("click", () => close(null), sig);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(null); }, sig);

  overlay.classList.remove("igm-hidden");
  newOk.focus();
}

// ── Helpers de impacto para movimientos ───────────────────────────────────────

function applyAdditiveFilled(filled) {
  filled.forEach(f => {
    if (f.variantId != null) {
      const varChart = Handler.findNode(handler.root, f.variantId);
      if (!varChart?.model) return;
      if (!varChart.model.attribute_implementations) varChart.model.attribute_implementations = [];
      const already = varChart.model.attribute_implementations.some(i => (i.attribute?.key ?? i.key) === f.attr.key);
      if (!already) varChart.model.attribute_implementations.push({ attribute: f.attr, value: f.value, id: null });
    } else if (f.productId != null) {
      const prodChart = Handler.findNode(handler.root, f.productId);
      if (!prodChart?.model) return;
      if (!prodChart.model.attributes_implementations) prodChart.model.attributes_implementations = [];
      const already = prodChart.model.attributes_implementations.some(i => (i.attribute?.key ?? i.key) === f.attr.key);
      if (!already) prodChart.model.attributes_implementations.push({ attribute: f.attr, value: f.value, id: null });
    }
  });
}

function applyDestructiveDeletions(deletions) {
  deletions.forEach(d => {
    if (d.variantId != null && !d.attrKey) {
      handler.deleteById(d.variantId);
      return;
    }
    if (!d.attrKey) return;
    if (d.variantId != null) {
      const varChart = Handler.findNode(handler.root, d.variantId);
      if (!varChart?.model?.attribute_implementations) return;
      varChart.model.attribute_implementations = varChart.model.attribute_implementations
        .filter(i => (i.attribute?.key ?? i.key) !== d.attrKey);
    } else if (d.productId != null) {
      const prodChart = Handler.findNode(handler.root, d.productId);
      if (!prodChart?.model?.attributes_implementations) return;
      prodChart.model.attributes_implementations = prodChart.model.attributes_implementations
        .filter(i => (i.attribute?.key ?? i.key) !== d.attrKey);
    }
  });
}

function moveMsgFor(flow) {
  if (flow === "additive")    return "Mover esta carta incorpora atributos que deben implementarse:";
  if (flow === "destructive") return "Mover esta carta elimina implementaciones de atributos existentes:";
  return "Este movimiento impacta en las implementaciones de atributos:";
}

// ══════════════════════════════════════════════════════════════════════════════
// MODAL GLOBAL DE ATRIBUTOS (CRUD)
// ══════════════════════════════════════════════════════════════════════════════

let attrsModalReady   = false;
let currentEnumValues = [];
let editingAttrId     = null;

function openAttrsModal() {
  const overlay = document.getElementById("igm-attrs-overlay");

  const refreshEnumValues = () => {
    renderEnumValues(
      document.getElementById("igm-na-enum-list"),
      currentEnumValues,
      (idx) => { currentEnumValues.splice(idx, 1); refreshEnumValues(); },
    );
  };

  const resetForm = () => {
    editingAttrId = null;
    document.getElementById("igm-na-key").value     = "";
    document.getElementById("igm-na-key").readOnly  = false;
    document.getElementById("igm-na-name").value    = "";
    document.getElementById("igm-na-dtype").value   = "text";
    document.getElementById("igm-na-static").value  = "false";
    document.getElementById("igm-na-heading").textContent    = "Nuevo atributo";
    document.getElementById("igm-na-create-btn").textContent = "+ Crear atributo";
    document.getElementById("igm-na-cancel-edit").classList.add("igm-hidden");
    currentEnumValues = [];
    document.getElementById("igm-na-enum-section").classList.add("igm-hidden");
    refreshEnumValues();
  };

  const renderExistingList = () => {
    renderAttrRows(
      document.getElementById("igm-attrs-list"),
      attrStore.attrs,
      (attr) => {
        if (!confirm(`¿Eliminar el atributo "${attr.name}" (${attr.key})?`)) return;
        attrStore.remove(attr.id);
        if (editingAttrId === attr.id) resetForm();
        renderExistingList();
      },
      (attr) => {
        editingAttrId = attr.id;
        document.getElementById("igm-na-key").value     = attr.key;
        document.getElementById("igm-na-key").readOnly  = true;
        document.getElementById("igm-na-name").value    = attr.name;
        document.getElementById("igm-na-dtype").value   = attr.data_type;
        document.getElementById("igm-na-static").value  = String(attr.is_static);
        currentEnumValues = [...(attr.enum_values ?? [])];
        const isEnum = attr.data_type === "enum";
        document.getElementById("igm-na-enum-section").classList.toggle("igm-hidden", !isEnum);
        refreshEnumValues();
        document.getElementById("igm-na-heading").textContent    = `Editando: ${attr.key}`;
        document.getElementById("igm-na-create-btn").textContent = "Guardar cambios";
        document.getElementById("igm-na-cancel-edit").classList.remove("igm-hidden");
        document.getElementById("igm-na-name").focus();
      },
    );
  };

  if (!attrsModalReady) {
    attrsModalReady = true;

    document.getElementById("igm-na-dtype").addEventListener("change", () => {
      const isEnum = document.getElementById("igm-na-dtype").value === "enum";
      document.getElementById("igm-na-enum-section").classList.toggle("igm-hidden", !isEnum);
      if (!isEnum) { currentEnumValues = []; refreshEnumValues(); }
    });

    const addEnumValue = () => {
      const input = document.getElementById("igm-na-enum-input");
      const val   = input.value.trim();
      if (!val || currentEnumValues.includes(val)) { input.focus(); return; }
      currentEnumValues.push(val);
      input.value = "";
      refreshEnumValues();
      input.focus();
    };
    document.getElementById("igm-na-enum-add").addEventListener("click", addEnumValue);
    document.getElementById("igm-na-enum-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); addEnumValue(); }
    });

    document.getElementById("igm-na-cancel-edit").addEventListener("click", resetForm);

    document.getElementById("igm-na-create-btn").addEventListener("click", () => {
      const name     = document.getElementById("igm-na-name").value.trim();
      const dataType = document.getElementById("igm-na-dtype").value;
      const isStatic = document.getElementById("igm-na-static").value === "true";

      if (editingAttrId !== null) {
        if (!name) { document.getElementById("igm-na-name").focus(); return; }
        if (dataType === "enum" && currentEnumValues.length === 0) {
          alert("El atributo enum necesita al menos una opción.");
          return;
        }
        attrStore.update(editingAttrId, { name, data_type: dataType, is_static: isStatic, enum_values: currentEnumValues });
        resetForm();
        renderExistingList();
        return;
      }

      const key = document.getElementById("igm-na-key").value.trim();
      if (!key || !name) { document.getElementById("igm-na-key").focus(); return; }
      if (attrStore.attrs.some(a => a.key === key)) {
        alert(`Ya existe un atributo con key "${key}".`);
        document.getElementById("igm-na-key").focus();
        return;
      }
      if (dataType === "enum" && currentEnumValues.length === 0) {
        alert("El atributo enum necesita al menos una opción.");
        return;
      }

      attrStore.add({ key, name, data_type: dataType, is_static: isStatic, enum_values: currentEnumValues });
      resetForm();
      renderExistingList();
    });

    document.getElementById("igm-attrs-close").addEventListener("click", () => {
      overlay.classList.add("igm-hidden");
    });
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.add("igm-hidden");
    });
  }

  renderExistingList();
  resetForm();
  overlay.classList.remove("igm-hidden");
  document.getElementById("igm-na-key").focus();
}

// ── Botón "Atributos" en navbar ───────────────────────────────────────────────

const attrsMgrBtn = document.getElementById("igm-attrs-btn");
if (attrsMgrBtn) attrsMgrBtn.addEventListener("click", openAttrsModal);

// ══════════════════════════════════════════════════════════════════════════════
// PICKER DE ATRIBUTOS (selector desde modal de categoría)
// ══════════════════════════════════════════════════════════════════════════════

function openAttrPicker() {
  const overlay = document.getElementById("igm-attr-picker-overlay");

  let pickerSelection = [...pendingAttrs];

  const getContainers = () => ({
    haveStatic:  document.getElementById("igm-picker-have-static"),
    haveDynamic: document.getElementById("igm-picker-have-dynamic"),
    allStatic:   document.getElementById("igm-picker-all-static"),
    allDynamic:  document.getElementById("igm-picker-all-dynamic"),
  });

  const renderPicker = () => {
    renderPickerView(pickerSelection, attrStore.attrs, getContainers(), {
      onRemove: (attr) => {
        pickerSelection = pickerSelection.filter(a => a.key !== attr.key);
        renderPicker();
      },
      onAdd: (attr) => {
        pickerSelection.push({ ...attr });
        renderPicker();
      },
    });
  };

  renderPicker();

  const actionsDiv = overlay.querySelector(".igm-modal-actions");
  const oldConfirm = document.getElementById("igm-picker-confirm");
  const oldCancel  = document.getElementById("igm-picker-cancel");
  const newConfirm = oldConfirm.cloneNode(true);
  const newCancel  = oldCancel.cloneNode(true);
  actionsDiv.replaceChild(newConfirm, oldConfirm);
  actionsDiv.replaceChild(newCancel,  oldCancel);

  newCancel.addEventListener("click",  () => overlay.classList.add("igm-hidden"));
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.add("igm-hidden");
  }, { once: true });

  newConfirm.addEventListener("click", () => {
    overlay.classList.add("igm-hidden");

    const added   = pickerSelection.filter(a => !pendingAttrs.some(p => p.key === a.key));
    const removed = pendingAttrs.filter(a => !pickerSelection.some(p => p.key === a.key));

    let allInputs        = [];
    let allDeletions     = [];
    let affectedRemovals = [];

    if (editingChart) {
      for (const attr of added) {
        const an = gestor.analyzeAddAttribute(editingChart.id, attr);
        if (an.flow === "additive") allInputs.push(...an.inputs);
      }
      for (const attr of removed) {
        const an = gestor.analyzeRemoveAttribute(editingChart.id, attr);
        if (an.flow === "destructive") {
          allDeletions.push(...an.deletions);
          affectedRemovals.push({ attr, affected: an.affected, affectedVariants: an.affectedVariants ?? [], variantsToDelete: an.variantsToDelete ?? [] });
        }
      }
    }

    const applyChanges = (filled = []) => {
      filled.forEach(f => {
        if (f.variantId != null) {
          const varChart = Handler.findNode(handler.root, f.variantId);
          if (!varChart?.model) return;
          if (!varChart.model.attribute_implementations) varChart.model.attribute_implementations = [];
          const already = varChart.model.attribute_implementations.some(i => (i.attribute?.key ?? i.key) === f.attr.key);
          if (!already) varChart.model.attribute_implementations.push({ attribute: f.attr, value: f.value, id: null });
        } else if (f.productId != null) {
          const prodChart = Handler.findNode(handler.root, f.productId);
          if (!prodChart?.model) return;
          if (!prodChart.model.attributes_implementations) prodChart.model.attributes_implementations = [];
          const already = prodChart.model.attributes_implementations.some(i => (i.attribute?.key ?? i.key) === f.attr.key);
          if (!already) prodChart.model.attributes_implementations.push({ attribute: f.attr, value: f.value, id: null });
        }
      });
      affectedRemovals.forEach(({ attr, affected, affectedVariants, variantsToDelete }) => {
        affected.forEach(({ id: prodChartId }) => {
          const prodChart = Handler.findNode(handler.root, prodChartId);
          if (!prodChart?.model?.attributes_implementations) return;
          prodChart.model.attributes_implementations = prodChart.model.attributes_implementations
            .filter(i => (i.attribute?.key ?? i.key) !== attr.key);
        });
        (affectedVariants ?? []).forEach(({ id: varChartId }) => {
          const varChart = Handler.findNode(handler.root, varChartId);
          if (!varChart?.model?.attribute_implementations) return;
          varChart.model.attribute_implementations = varChart.model.attribute_implementations
            .filter(i => (i.attribute?.key ?? i.key) !== attr.key);
        });
        (variantsToDelete ?? []).forEach(({ id: varChartId }) => {
          handler.deleteById(varChartId);
        });
      });
      pendingAttrs = [...pickerSelection];
      refreshAttrList();
      if (editingChart?.model) editingChart.model.attributes = [...pendingAttrs];
      handler.treeToMax();
      handler.render({ container: "#igm-board" });
    };

    if (allInputs.length > 0 || allDeletions.length > 0) {
      showGestorDialog({
        title:       "Impacto de los cambios",
        description: "Los atributos modificados requieren actualizar los siguientes elementos:",
        inputs:      allInputs,
        deletions:   allDeletions,
        onConfirm:   applyChanges,
        onCancel:    () => {},
      });
    } else {
      applyChanges();
    }
  });

  overlay.classList.remove("igm-hidden");
}

// ── Botón "Agregar atributos" en el modal de categoría ────────────────────────

const attrPickerBtn = document.getElementById("igm-attr-picker-btn");
if (attrPickerBtn) attrPickerBtn.addEventListener("click", () => openAttrPicker());

// ══════════════════════════════════════════════════════════════════════════════
// EVENTOS DEL BOARD
// ══════════════════════════════════════════════════════════════════════════════

const board = document.querySelector("#igm-board");

board.addEventListener("igm-collapse", () => {
  catalogStore.save(handler);
});

// ── Agregar carta ─────────────────────────────────────────────────────────────

const LABEL = {
  [CHART_TYPE.CATEGORY]: "Categoría",
  [CHART_TYPE.PRODUCT]:  "Producto",
  [CHART_TYPE.VARIANT]:  "Variante",
};

/**
 * Devuelve las opciones válidas para el menú "+" según el nodo y dirección.
 *
 * - down en product   → solo Variante
 * - down en category  → Category y/o Product según hijos existentes
 * - right en cualquiera → mismo tipo que el nodo
 */
function getMenuOptions(base, dir) {
  const opt = (type) => ({ value: type, label: LABEL[type] });

  if (dir === "right") return [opt(base.chartType)];

  // dir === "down"
  if (base.chartType === CHART_TYPE.PRODUCT) return [opt(CHART_TYPE.VARIANT)];

  if (base.chartType === CHART_TYPE.CATEGORY) {
    const firstChildType = base.listaHijos[0]?.chartType;
    if (firstChildType === CHART_TYPE.PRODUCT)  return [opt(CHART_TYPE.PRODUCT)];
    if (firstChildType === CHART_TYPE.CATEGORY) return [opt(CHART_TYPE.CATEGORY)];
    return [opt(CHART_TYPE.CATEGORY), opt(CHART_TYPE.PRODUCT)];
  }

  return [];
}

board.addEventListener("igm-add-chart", (ev) => {
  const { fromId, dir } = ev.detail;
  const base = Handler.findNode(handler.root, fromId);
  if (!base) return;

  const opts = getMenuOptions(base, dir);
  if (opts.length === 0) return;

  const doAdd = (chartType) => {
    const parentId = dir === "down" ? base.id : base.idParent;

    const check = gestor.checkAdd(parentId, chartType);
    if (!check.ok) { alert(check.reason); return; }

    createModel(chartType, (model) => {
      if (!model) return;

      if (chartType === CHART_TYPE.PRODUCT) {
        const analysis = gestor.analyzeAddProduct(parentId);
        if (analysis.flow === "additive") {
          showGestorDialog({
            title:        "Implementar atributos",
            description:  "Este producto hereda atributos estáticos de su categoría. Completá los valores:",
            inputs:       analysis.inputs,
            confirmLabel: "Crear producto",
            onConfirm: (filled) => {
              model.attributes_implementations = filled.map(f => ({ attribute: f.attr, value: f.value, id: null }));
              layoutActors[currentLayout].add(base, dir, chartType, model);
            },
            onCancel: () => {},
          });
          return;
        }
      }

      if (chartType === CHART_TYPE.VARIANT) {
        const analysis = gestor.analyzeAddVariant(parentId);
        if (analysis.blocked) { alert(analysis.reason); return; }
        if (analysis.flow === "additive") {
          showGestorDialog({
            title:        "Implementar atributos de variante",
            description:  "Esta variante debe implementar los atributos dinámicos requeridos por su categoría:",
            inputs:       analysis.inputs,
            confirmLabel: "Crear variante",
            onConfirm: (filled) => {
              const impls = filled.map(f => ({ attribute: f.attr, value: f.value, id: null }));
              const unique = gestor.checkVariantUnique(parentId, impls);
              if (!unique.ok) { alert(unique.reason); return; }
              model.attribute_implementations = impls;
              layoutActors[currentLayout].add(base, dir, chartType, model);
            },
            onCancel: () => {},
          });
          return;
        }
      }

      layoutActors[currentLayout].add(base, dir, chartType, model);
    });
  };

  // Si solo hay una opción válida, no mostramos el menú
  if (opts.length === 1) { doAdd(opts[0].value); return; }

  const btn = board.querySelector(`.igm-add-${dir}[data-id="${fromId}"]`);
  if (!btn) return;
  showMenu(btn, opts, doAdd);
});

// ── Eliminar carta ────────────────────────────────────────────────────────────

board.addEventListener("click", (ev) => {
  const del = ev.target.closest(".igm-btn-del");
  if (!del) return;

  const id   = parseInt(del.dataset.id, 10);
  const node = Handler.findNode(handler.root, id);
  if (!node) return;

  const analysis = gestor.analyzeDelete(id);

  if (analysis.deletions.length <= 1) {
    if (!confirm(`¿Eliminar "${node.label}"?`)) return;
    layoutActors[currentLayout].deleteNode(id);
    return;
  }

  showGestorDialog({
    title:        `Eliminar "${node.label}"`,
    description:  `Se eliminarán ${analysis.deletions.length} elementos en total:`,
    deletions:    analysis.deletions,
    confirmLabel: "Eliminar todo",
    onConfirm:    () => layoutActors[currentLayout].deleteNode(id),
    onCancel:     () => {},
  });
});

// ── Doble click → editar ──────────────────────────────────────────────────────

board.addEventListener("dblclick", (ev) => {
  const box = ev.target.closest(".igm-box");
  if (!box) return;
  const id   = parseInt(box.dataset.id, 10);
  const node = Handler.findNode(handler.root, id);
  if (!node) return;
  openModal(node);
});

// ── Agregar al root ────────────────────────────────────────────────────────────

const addRootBtn = document.getElementById("igm-add-root");
if (addRootBtn) {
  addRootBtn.addEventListener("click", () => {
    const check = gestor.checkAdd(0, CHART_TYPE.CATEGORY);
    if (!check.ok) { alert(check.reason); return; }
    createModel(CHART_TYPE.CATEGORY, (model) => {
      if (!model) return;
      layoutActors[currentLayout].addRoot(CHART_TYPE.CATEGORY, model);
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// MODAL DE EDICIÓN
// ══════════════════════════════════════════════════════════════════════════════

const overlay     = document.getElementById("igm-modal-overlay");
const modalTitle  = document.getElementById("igm-modal-title");

const secCategory = document.getElementById("igm-sec-category");
const secProduct  = document.getElementById("igm-sec-product");
const secVariant  = document.getElementById("igm-sec-variant");
const allSections = [secCategory, secProduct, secVariant];

const catName  = document.getElementById("igm-cat-name");
const attrList = document.getElementById("igm-attr-list");

const prodTitle = document.getElementById("igm-prod-title");
const prodCode  = document.getElementById("igm-prod-code");
const prodPrice = document.getElementById("igm-prod-price");
const prodBrand = document.getElementById("igm-prod-brand");
const prodDesc  = document.getElementById("igm-prod-desc");

let editingChart = null;
let pendingAttrs = [];

function openModal(chart) {
  editingChart = chart;

  const color = CHART_BG[chart.chartType] ?? "#888";
  modalTitle.textContent = `Editar ${
    chart.chartType === CHART_TYPE.CATEGORY ? "Categoría" :
    chart.chartType === CHART_TYPE.PRODUCT  ? "Producto"  : "Variante"
  }`;
  modalTitle.style.color = color;

  allSections.forEach(s => s.classList.remove("igm-active"));

  if (chart.chartType === CHART_TYPE.CATEGORY) {
    secCategory.classList.add("igm-active");
    catName.value = chart.model?.name ?? "";
    pendingAttrs  = [...(chart.model?.attributes ?? [])].map(a => ({ ...a }));
    refreshAttrList();

  } else if (chart.chartType === CHART_TYPE.PRODUCT) {
    secProduct.classList.add("igm-active");
    const m = chart.model ?? {};
    prodTitle.value = m.title       ?? "";
    prodCode.value  = m.code        ?? "";
    prodPrice.value = m.price       ?? "";
    prodBrand.value = m.brand       ?? "";
    prodDesc.value  = m.description ?? "";
    renderImplsEditable(document.getElementById("igm-prod-impls"), m.attributes_implementations ?? []);

  } else if (chart.chartType === CHART_TYPE.VARIANT) {
    secVariant.classList.add("igm-active");
    renderImplsEditable(document.getElementById("igm-var-impls"), chart.model?.attribute_implementations ?? []);
  }

  overlay.classList.remove("igm-hidden");
  if (chart.chartType === CHART_TYPE.CATEGORY) catName.focus();
  else if (chart.chartType === CHART_TYPE.PRODUCT) prodTitle.focus();
}

function closeModal() {
  overlay.classList.add("igm-hidden");
  editingChart = null;
  pendingAttrs = [];
}

function refreshAttrList() {
  renderAttrList(attrList, pendingAttrs, (attr, idx) => {
    if (!editingChart) return;
    const analysis = gestor.analyzeRemoveAttribute(editingChart.id, attr);
    if (analysis.flow === "destructive" && analysis.deletions.length > 0) {
      showGestorDialog({
        title:        `Quitar atributo "${attr.name}"`,
        description:  "Se eliminarán las siguientes implementaciones en los productos:",
        deletions:    analysis.deletions,
        confirmLabel: "Quitar atributo",
        onConfirm: () => {
          analysis.affected.forEach(({ id: prodChartId }) => {
            const prodChart = Handler.findNode(handler.root, prodChartId);
            if (!prodChart?.model?.attributes_implementations) return;
            prodChart.model.attributes_implementations = prodChart.model.attributes_implementations
              .filter(i => (i.attribute?.key ?? i.key) !== attr.key);
          });
          (analysis.affectedVariants ?? []).forEach(({ id: varChartId }) => {
            const varChart = Handler.findNode(handler.root, varChartId);
            if (!varChart?.model?.attribute_implementations) return;
            varChart.model.attribute_implementations = varChart.model.attribute_implementations
              .filter(i => (i.attribute?.key ?? i.key) !== attr.key);
          });
          (analysis.variantsToDelete ?? []).forEach(({ id: varChartId }) => {
            handler.deleteById(varChartId);
          });
          pendingAttrs.splice(idx, 1);
          refreshAttrList();
        },
        onCancel: () => {},
      });
      return;
    }
    pendingAttrs.splice(idx, 1);
    refreshAttrList();
  });
}

// ── Guardar modal ─────────────────────────────────────────────────────────────

function _readBackImpls(containerEl, impls) {
  containerEl?.querySelectorAll("[data-impl-idx]").forEach(el => {
    const impl = impls[parseInt(el.dataset.implIdx, 10)];
    if (!impl) return;
    impl.value = el.type === "checkbox" ? el.checked : el.value;
  });
}

document.getElementById("igm-modal-save").addEventListener("click", () => {
  if (!editingChart) return;

  if (editingChart.chartType === CHART_TYPE.CATEGORY) {
    const name = catName.value.trim();
    if (!name) { catName.focus(); return; }
    if (!editingChart.model) editingChart.model = { id: null, attributes: [] };
    editingChart.model.name       = name;
    editingChart.model.attributes = pendingAttrs;

  } else if (editingChart.chartType === CHART_TYPE.PRODUCT) {
    const title = prodTitle.value.trim();
    if (!title) { prodTitle.focus(); return; }
    if (!editingChart.model) editingChart.model = {};
    editingChart.model.title       = title;
    editingChart.model.code        = prodCode.value.trim()  || `SKU-${editingChart.id}`;
    editingChart.model.price       = parseFloat(prodPrice.value) || 0;
    editingChart.model.brand       = prodBrand.value.trim();
    editingChart.model.description = prodDesc.value.trim();
    _readBackImpls(
      document.getElementById("igm-prod-impls"),
      editingChart.model.attributes_implementations ?? [],
    );

  } else if (editingChart.chartType === CHART_TYPE.VARIANT) {
    if (!editingChart.model) editingChart.model = {};
    const impls     = editingChart.model.attribute_implementations ?? [];
    const container = document.getElementById("igm-var-impls");

    const proposed = impls.map(impl => ({ ...impl }));
    container?.querySelectorAll("[data-impl-idx]").forEach(el => {
      const impl = proposed[parseInt(el.dataset.implIdx, 10)];
      if (impl) impl.value = el.type === "checkbox" ? el.checked : el.value;
    });

    const unique = gestor.checkVariantUnique(editingChart.idParent, proposed, editingChart.id);
    if (!unique.ok) { alert(unique.reason); return; }

    _readBackImpls(container, impls);
  }

  handler.treeToMax();
  handler.render({ container: "#igm-board" });
  closeModal();
});

document.getElementById("igm-modal-cancel").addEventListener("click", closeModal);
overlay.addEventListener("click", (ev) => { if (ev.target === overlay) closeModal(); });

// ══════════════════════════════════════════════════════════════════════════════
// DRAG & DROP
// ══════════════════════════════════════════════════════════════════════════════

let dragId   = null;
let dropZone = null;
const SIBLING_THRESHOLD = 0.65;

function clearDropHighlights() {
  board.querySelectorAll(".drop-child, .drop-sibling").forEach(el => {
    el.classList.remove("drop-child", "drop-sibling");
  });
}

board.addEventListener("dragstart", (ev) => {
  const box = ev.target.closest(".igm-box");
  if (!box) return;
  dragId = parseInt(box.dataset.id, 10);
  ev.dataTransfer.setData("text/plain", String(dragId));
  ev.dataTransfer.effectAllowed = "move";
});

board.addEventListener("dragover", (ev) => {
  const box = ev.target.closest(".igm-box");
  if (!box) return;
  ev.preventDefault();
  ev.dataTransfer.dropEffect = "move";
  clearDropHighlights();
  const rect = box.getBoundingClientRect();
  const relX = (ev.clientX - rect.left) / rect.width;
  if (relX > SIBLING_THRESHOLD) {
    box.classList.add("drop-sibling"); dropZone = "sibling";
  } else {
    box.classList.add("drop-child");   dropZone = "child";
  }
});

board.addEventListener("dragleave", (ev) => {
  if (!board.contains(ev.relatedTarget)) clearDropHighlights();
});

board.addEventListener("drop", (ev) => {
  clearDropHighlights();
  const raw    = ev.dataTransfer.getData("text/plain");
  const fromId = Number.isFinite(parseInt(raw, 10)) ? parseInt(raw, 10) : dragId;
  if (!Number.isFinite(fromId)) return;

  const box = ev.target.closest(".igm-box");
  if (!box) return;
  ev.preventDefault();

  const toId = parseInt(box.dataset.id, 10);
  if (!Number.isFinite(toId)) return;

  const mode     = dropZone === "sibling" ? "sibling" : "child";
  const analysis = gestor.analyzeMove(fromId, toId, mode);

  if (analysis.blocked) { alert(analysis.reason); return; }

  const doMove = () => {
    if (mode === "sibling") {
      const dest = Handler.findNode(handler.root, toId);
      if (!dest || dest.idParent === null) return;
      layoutActors[currentLayout].moveToSibling(fromId, toId);
    } else {
      layoutActors[currentLayout].moveToChild(fromId, toId);
    }
  };

  if (analysis.flow === "none") { doMove(); return; }

  showGestorDialog({
    title:        "Mover carta",
    description:  moveMsgFor(analysis.flow),
    inputs:       analysis.inputs    ?? [],
    deletions:    analysis.deletions ?? [],
    confirmLabel: "Mover",
    onConfirm: (filled) => {
      if (filled.length > 0)              applyAdditiveFilled(filled);
      if (analysis.deletions?.length > 0) applyDestructiveDeletions(analysis.deletions);
      doMove();
    },
    onCancel: () => {},
  });
});

board.addEventListener("dragend", () => {
  dragId = null; dropZone = null; clearDropHighlights();
});

// ══════════════════════════════════════════════════════════════════════════════
// BOTONES API — Save / Bring Tree
// ══════════════════════════════════════════════════════════════════════════════

const saveBtn  = document.getElementById("igm-save-btn");
const bringBtn = document.getElementById("igm-bring-btn");

if (saveBtn) {
  saveBtn.addEventListener("click", async () => {
    saveBtn.disabled    = true;
    saveBtn.textContent = "Guardando…";
    try {
      const payload = buildAPIPayload(handler, attrStore);
      const result  = await saveCatalog(payload);
      if (result.valid) {
        alert("Catálogo guardado correctamente.");
      } else {
        alert(`Error de validación:\n${result.error}`);
      }
    } catch (err) {
      alert(`Error al guardar:\n${err.message}`);
    } finally {
      saveBtn.disabled    = false;
      saveBtn.textContent = "Save";
    }
  });
}

if (bringBtn) {
  bringBtn.addEventListener("click", async () => {
    bringBtn.disabled    = true;
    bringBtn.textContent = "Cargando…";
    try {
      localStorage.removeItem(catalogStore.KEY);
      localStorage.removeItem("igm-attrs");

      const data = await fetchCatalog();

      if (!data.tree) {
        alert("La base de datos está vacía. No hay árbol que cargar.");
        return;
      }

      loadFromAPIData(handler, attrStore, data);
      handler.treeToMax();
      handler.render({ container: "#igm-board" });
      alert("Árbol cargado correctamente desde la API.");
    } catch (err) {
      alert(`Error al cargar:\n${err.message}`);
    } finally {
      bringBtn.disabled    = false;
      bringBtn.textContent = "Bring Tree";
    }
  });
}

initZoom();

export { handler, gestor };
