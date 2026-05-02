import { Handler }                                       from "./Handler.js";
import { CHART_TYPE, CHART_BG }                          from "./charts.js";
import { Category, Product, Variant, Attribute }         from "./models.js";
import { initUI, showMenu, showGestorDialog }            from "./ui.js";
import { Gestor }                                        from "./Gestor.js";

// ── Inicialización ─────────────────────────────────────────────────────────────

initUI();

const handler = new Handler();
const gestor  = new Gestor(handler);

// Wrap render para auto-guardado
const _render = handler.render.bind(handler);
handler.render = (opts) => {
  _render(opts);
  localStorage.setItem("igm-catalog", handler.toJson());
};

const saved = localStorage.getItem("igm-catalog");
if (saved) {
  try { handler.fromJson(saved); } catch (e) { console.warn("Error al cargar estado:", e); }
}

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

// ── Layout actors (solo organigram) ───────────────────────────────────────────

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

// ── Crear modelo por tipo ──────────────────────────────────────────────────────

function createModel(chartType) {
  if (chartType === CHART_TYPE.CATEGORY) {
    const name = (prompt("Nombre de la categoría:", "") ?? "").trim();
    if (!name) return null;
    return { name, id: null, attributes: [] };
  }
  if (chartType === CHART_TYPE.PRODUCT) {
    const title = (prompt("Título del producto:", "") ?? "").trim();
    if (!title) return null;
    const code  = (prompt("Código SKU:", "") ?? "").trim() || `SKU-${Date.now()}`;
    const price = parseFloat(prompt("Precio:", "0") || "0");
    const brand = (prompt("Marca:", "") ?? "").trim();
    return { title, code, price, brand, description: "", id: null, attributes_implementations: [] };
  }
  if (chartType === CHART_TYPE.VARIANT) {
    return { id: null, attribute_implementations: [] };
  }
  return null;
}

// ── Helpers para aplicar impactos tras un movimiento ──────────────────────────

function applyAdditiveFilled(filled) {
  filled.forEach(f => {
    if (!f.productId) return;
    const prodChart = Handler.findNode(handler.root, f.productId);
    if (!prodChart?.model) return;
    if (!prodChart.model.attributes_implementations) prodChart.model.attributes_implementations = [];
    const already = prodChart.model.attributes_implementations.some(i => (i.attribute?.key ?? i.key) === f.attr.key);
    if (!already) prodChart.model.attributes_implementations.push({ attribute: f.attr, value: f.value, id: null });
  });
}

function applyDestructiveDeletions(deletions) {
  deletions.forEach(d => {
    if (!d.productId || !d.attrKey) return;
    const prodChart = Handler.findNode(handler.root, d.productId);
    if (!prodChart?.model?.attributes_implementations) return;
    prodChart.model.attributes_implementations = prodChart.model.attributes_implementations
      .filter(i => (i.attribute?.key ?? i.key) !== d.attrKey);
  });
}

// Descripción del dialog para movimientos con impacto
function moveMsgFor(flow) {
  if (flow === "additive")    return "Mover esta carta incorpora atributos heredados que los productos afectados deben implementar:";
  if (flow === "destructive") return "Mover esta carta elimina atributos que los productos afectados tenían implementados:";
  return "Este movimiento tiene impacto en las implementaciones de atributos:";
}

// ── Eventos del board ──────────────────────────────────────────────────────────

const board = document.querySelector("#igm-board");

board.addEventListener("igm-collapse", () => {
  localStorage.setItem("igm-catalog", handler.toJson());
});

// ── Agregar carta ─────────────────────────────────────────────────────────────

const CHART_OPCIONES = [
  { value: CHART_TYPE.CATEGORY, label: "Categoría" },
  { value: CHART_TYPE.PRODUCT,  label: "Producto"  },
  { value: CHART_TYPE.VARIANT,  label: "Variante"  },
];

board.addEventListener("igm-add-chart", (ev) => {
  const { fromId, dir } = ev.detail;
  const base = Handler.findNode(handler.root, fromId);
  if (!base) return;

  const btn = board.querySelector(`.igm-add-${dir}[data-id="${fromId}"]`);
  if (!btn) return;

  showMenu(btn, CHART_OPCIONES, (chartType) => {
    const parentId = dir === "down" ? base.id : base.idParent;

    // Validación estructural antes de cualquier otra cosa
    const check = gestor.checkAdd(parentId, chartType);
    if (!check.ok) { alert(check.reason); return; }

    const model = createModel(chartType);
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
          title:        "Implementar atributos dinámicos",
          description:  "Esta variante debe implementar todos los atributos dinámicos de la categoría:",
          inputs:       analysis.inputs,
          confirmLabel: "Crear variante",
          onConfirm: (filled) => {
            model.attribute_implementations = filled.map(f => ({ attribute: f.attr, value: f.value, id: null }));
            layoutActors[currentLayout].add(base, dir, chartType, model);
          },
          onCancel: () => {},
        });
        return;
      }
    }

    layoutActors[currentLayout].add(base, dir, chartType, model);
  });
});

// ── Eliminar carta ────────────────────────────────────────────────────────────

board.addEventListener("click", (ev) => {
  const del = ev.target.closest(".igm-btn-del");
  if (!del) return;

  const id   = parseInt(del.dataset.id, 10);
  const node = Handler.findNode(handler.root, id);
  if (!node) return;

  const analysis = gestor.analyzeDelete(id);

  // Caso simple: solo el propio nodo, sin hijos
  if (analysis.deletions.length <= 1) {
    if (!confirm(`¿Eliminar "${node.label}"?`)) return;
    layoutActors[currentLayout].deleteNode(id);
    return;
  }

  // Caso con cascada: mostrar dialog con lista completa
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

// ── Botón agregar al root ──────────────────────────────────────────────────────

const addRootBtn = document.getElementById("igm-add-root");
if (addRootBtn) {
  addRootBtn.addEventListener("click", () => {
    showMenu(addRootBtn, CHART_OPCIONES, (chartType) => {
      const check = gestor.checkAdd(0, chartType);
      if (!check.ok) { alert(check.reason); return; }
      const model = createModel(chartType);
      if (!model) return;
      layoutActors[currentLayout].addRoot(chartType, model);
    });
  });
}

// ══════════════════════════════════════════════════════════════════════════════
// MODAL DE EDICIÓN
// ══════════════════════════════════════════════════════════════════════════════

const overlay  = document.getElementById("igm-modal-overlay");
const modalTitle = document.getElementById("igm-modal-title");

const secCategory = document.getElementById("igm-sec-category");
const secProduct  = document.getElementById("igm-sec-product");
const secVariant  = document.getElementById("igm-sec-variant");
const allSections = [secCategory, secProduct, secVariant];

const catName     = document.getElementById("igm-cat-name");
const attrList    = document.getElementById("igm-attr-list");
const attrKey     = document.getElementById("igm-attr-key");
const attrNameInp = document.getElementById("igm-attr-name-inp");
const attrDtype   = document.getElementById("igm-attr-dtype");
const attrStatic  = document.getElementById("igm-attr-static");
const attrAddBtn  = document.getElementById("igm-attr-add-btn");

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
    renderAttrList();

  } else if (chart.chartType === CHART_TYPE.PRODUCT) {
    secProduct.classList.add("igm-active");
    const m = chart.model ?? {};
    prodTitle.value = m.title       ?? "";
    prodCode.value  = m.code        ?? "";
    prodPrice.value = m.price       ?? "";
    prodBrand.value = m.brand       ?? "";
    prodDesc.value  = m.description ?? "";

  } else if (chart.chartType === CHART_TYPE.VARIANT) {
    secVariant.classList.add("igm-active");
    renderVariantImpls(chart.model);
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

function renderAttrList() {
  attrList.innerHTML = "";
  if (pendingAttrs.length === 0) {
    const empty = document.createElement("span");
    empty.className   = "igm-body-empty";
    empty.textContent = "Sin atributos";
    attrList.appendChild(empty);
    return;
  }
  pendingAttrs.forEach((attr, idx) => {
    const item = document.createElement("div");
    item.className = "igm-attr-item";

    const info = document.createElement("div");
    info.className = "igm-attr-item-info";
    info.innerHTML =
      `<span class="igm-attr-item-key">${attr.key}</span>` +
      `<span class="igm-attr-item-meta">${attr.name}</span>` +
      `<span class="igm-attr-item-type">${attr.data_type}</span>` +
      (attr.is_static ? `<span class="igm-attr-item-type igm-attr-item-static">estático</span>` : "");

    const removeBtn = document.createElement("button");
    removeBtn.className   = "igm-attr-remove";
    removeBtn.textContent = "×";
    removeBtn.title       = "Quitar atributo";
    removeBtn.addEventListener("click", () => {
      if (!editingChart) return;

      const analysis = gestor.analyzeRemoveAttribute(editingChart.id, attr);
      if (analysis.flow === "destructive" && analysis.deletions.length > 0) {
        showGestorDialog({
          title:        `Quitar atributo "${attr.name}"`,
          description:  "Se eliminarán las siguientes implementaciones en los productos:",
          deletions:    analysis.deletions,
          confirmLabel: "Quitar atributo",
          onConfirm: () => {
            // Borrar implementaciones en los productos afectados
            analysis.affected.forEach(({ id: prodChartId }) => {
              const prodChart = Handler.findNode(handler.root, prodChartId);
              if (!prodChart?.model?.attributes_implementations) return;
              prodChart.model.attributes_implementations = prodChart.model.attributes_implementations
                .filter(i => (i.attribute?.key ?? i.key) !== attr.key);
            });
            pendingAttrs.splice(idx, 1);
            renderAttrList();
          },
          onCancel: () => {},
        });
        return;
      }

      pendingAttrs.splice(idx, 1);
      renderAttrList();
    });

    item.appendChild(info);
    item.appendChild(removeBtn);
    attrList.appendChild(item);
  });
}

function renderVariantImpls(model) {
  const container = document.getElementById("igm-var-impls");
  if (!container) return;
  container.innerHTML = "";
  const impls = model?.attribute_implementations ?? [];
  if (impls.length === 0) {
    container.textContent = "Esta variante no tiene implementaciones.";
    return;
  }
  impls.forEach(impl => {
    const row = document.createElement("div");
    row.className   = "igm-attr-item";
    row.textContent = `${impl.attribute?.key ?? "?"}: ${impl.value}`;
    container.appendChild(row);
  });
}

// ── Agregar atributo (dentro del modal) ───────────────────────────────────────

function resetAttrForm() {
  attrKey.value = ""; attrNameInp.value = ""; attrDtype.value = "text"; attrStatic.value = "false";
  attrKey.focus();
}

attrAddBtn.addEventListener("click", () => {
  const key      = attrKey.value.trim();
  const name     = attrNameInp.value.trim();
  const dataType = attrDtype.value;
  const isStatic = attrStatic.value === "true";

  if (!key || !name) { attrKey.focus(); return; }
  if (pendingAttrs.some(a => a.key === key)) {
    alert(`Ya existe un atributo con key "${key}".`); attrKey.focus(); return;
  }

  const newAttr = { key, name, data_type: dataType, is_static: isStatic, enum_values: [], id: null };

  if (editingChart) {
    const analysis = gestor.analyzeAddAttribute(editingChart.id, newAttr);
    if (analysis.flow === "additive" && analysis.inputs.length > 0) {
      showGestorDialog({
        title:       `Agregar atributo "${name}"`,
        description: `Este atributo ${isStatic ? "estático" : "dinámico"} impacta en ${analysis.affected.length} producto(s). Ingresá un valor inicial para cada uno:`,
        inputs:      analysis.inputs,
        onConfirm: (filled) => {
          // Aplicar implementación en cada producto afectado
          filled.forEach(f => {
            if (!f.productId) return;
            const prodChart = Handler.findNode(handler.root, f.productId);
            if (!prodChart?.model) return;
            if (!prodChart.model.attributes_implementations) prodChart.model.attributes_implementations = [];
            const already = prodChart.model.attributes_implementations.some(i => (i.attribute?.key ?? i.key) === key);
            if (!already) prodChart.model.attributes_implementations.push({ attribute: newAttr, value: f.value, id: null });
          });
          pendingAttrs.push(newAttr);
          renderAttrList();
          resetAttrForm();
        },
        onCancel: () => {},
      });
      return;
    }
  }

  pendingAttrs.push(newAttr);
  renderAttrList();
  resetAttrForm();
});

// ── Guardar modal ─────────────────────────────────────────────────────────────

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

  const mode = dropZone === "sibling" ? "sibling" : "child";
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

  if (analysis.flow === "none") {
    doMove();
    return;
  }

  // Hay impacto — mostrar dialog para confirmar y/o rellenar
  showGestorDialog({
    title:        "Mover carta",
    description:  moveMsgFor(analysis.flow),
    inputs:       analysis.inputs    ?? [],
    deletions:    analysis.deletions ?? [],
    confirmLabel: "Mover",
    onConfirm: (filled) => {
      // Aplicar implementaciones aditivas antes del movimiento
      if (filled.length > 0) applyAdditiveFilled(filled);
      // Limpiar implementaciones destructivas
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
// ZOOM
// ══════════════════════════════════════════════════════════════════════════════

let zoomLevel = 1.0;
const ZOOM_STEP = 0.1;
const ZOOM_MIN  = 0.2;
const ZOOM_MAX  = 3.0;

function applyZoom(z) {
  zoomLevel      = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, +z.toFixed(2)));
  board.style.zoom = zoomLevel;
}

function fitToScreen() {
  if (!boardContainer) return;
  const natW    = board.offsetWidth  / zoomLevel;
  const natH    = board.offsetHeight / zoomLevel;
  const fitZoom = Math.min(boardContainer.clientWidth / natW, boardContainer.clientHeight / natH, 1.0);
  applyZoom(fitZoom);
  boardContainer.scrollLeft = 0;
  boardContainer.scrollTop  = 0;
}

document.querySelectorAll("[data-igm='zoom-in']").forEach(b =>
  b.addEventListener("click", () => applyZoom(zoomLevel + ZOOM_STEP)));
document.querySelectorAll("[data-igm='zoom-out']").forEach(b =>
  b.addEventListener("click", () => applyZoom(zoomLevel - ZOOM_STEP)));
document.querySelectorAll("[data-igm='zoom-fit']").forEach(b =>
  b.addEventListener("click", fitToScreen));

if (boardContainer) {
  boardContainer.addEventListener("wheel", (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
    const newZ  = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, +(zoomLevel + delta).toFixed(2)));
    const rect  = boardContainer.getBoundingClientRect();
    const bx    = (boardContainer.scrollLeft + e.clientX - rect.left) / zoomLevel;
    const by    = (boardContainer.scrollTop  + e.clientY - rect.top)  / zoomLevel;
    applyZoom(newZ);
    boardContainer.scrollLeft = bx * zoomLevel - (e.clientX - rect.left);
    boardContainer.scrollTop  = by * zoomLevel - (e.clientY - rect.top);
  }, { passive: false });
}

// ── Pan con botón del medio ───────────────────────────────────────────────────

if (boardContainer) {
  let isPanning = false, panX = 0, panY = 0, panSL = 0, panST = 0;

  boardContainer.addEventListener("mousedown", (e) => {
    if (e.button !== 1) return;
    e.preventDefault();
    isPanning = true;
    panX = e.clientX; panY = e.clientY;
    panSL = boardContainer.scrollLeft; panST = boardContainer.scrollTop;
    boardContainer.style.cursor = "grabbing";
  });
  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;
    boardContainer.scrollLeft = panSL - (e.clientX - panX);
    boardContainer.scrollTop  = panST - (e.clientY - panY);
  });
  window.addEventListener("mouseup", (e) => {
    if (e.button !== 1 || !isPanning) return;
    isPanning = false;
    boardContainer.style.cursor = "";
  });
}

// ── Export ────────────────────────────────────────────────────────────────────

export { handler, gestor };
