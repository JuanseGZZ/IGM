import { Chart } from "./charts.js";
import { Organigram } from "./organigram.js";

export class Handler {
  constructor() {
    this.root   = new Chart({ id: 0, idParent: null, chartType: "root", model: null });
    this.lastId = 0;
    this.layout = new Organigram(this.root);
  }

  reset() {
    this.root   = new Chart({ id: 0, idParent: null, chartType: "root", model: null });
    this.lastId = 0;
    this.layout = new Organigram(this.root);
  }

  // ── búsqueda ───────────────────────────────────────────────────────────────

  static findNode(node, id) {
    if (!node) return null;
    if (node.id === id) return node;
    for (const hijo of node.listaHijos) {
      const found = Handler.findNode(hijo, id);
      if (found) return found;
    }
    return null;
  }

  // ── CRUD ───────────────────────────────────────────────────────────────────

  addNodeTo(parentId, chartType, model) {
    const parent = Handler.findNode(this.root, parentId);
    if (!parent) return null;
    this.lastId++;
    const chart = new Chart({ id: this.lastId, idParent: parentId, chartType, model });
    parent.addChild(chart);
    return chart;
  }

  deleteById(id) {
    if (id === 0) return false;
    const node   = Handler.findNode(this.root, id);
    if (!node) return false;
    const parent = Handler.findNode(this.root, node.idParent);
    if (!parent) return false;
    const idx = parent.listaHijos.findIndex(h => h.id === id);
    if (idx === -1) return false;
    parent.listaHijos.splice(idx, 1);
    parent.down = parent.listaHijos.length > 0 ? 1 : 0;
    return true;
  }

  deleteByIdAndRefresh(id) {
    const ok = this.deleteById(id);
    if (!ok) return false;
    this.treeToMax();
    this.render();
    return true;
  }

  // mueve fromId como hijo de toId
  moveNode(fromId, toId) {
    if (fromId === toId) return false;
    const node = Handler.findNode(this.root, fromId);
    if (!node || node.idParent === null) return false;
    if (Handler.findNode(node, toId)) return false; // ciclo

    const parent    = Handler.findNode(this.root, node.idParent);
    const newParent = Handler.findNode(this.root, toId);
    if (!parent || !newParent) return false;

    parent.listaHijos.splice(parent.listaHijos.findIndex(h => h.id === fromId), 1);
    parent.down = parent.listaHijos.length > 0 ? 1 : 0;

    node.up = 0; node.left = 0; node.right = 0;
    node.idParent = toId;
    newParent.addChild(node);
    return true;
  }

  // mueve fromId para quedar justo después de afterId (hermano)
  moveNodeAfter(fromId, afterId) {
    if (fromId === afterId) return false;
    const node = Handler.findNode(this.root, fromId);
    if (!node || node.idParent === null) return false;
    if (Handler.findNode(node, afterId)) return false;

    const afterNode  = Handler.findNode(this.root, afterId);
    if (!afterNode || afterNode.idParent === null) return false;

    const newParent = Handler.findNode(this.root, afterNode.idParent);
    const oldParent = Handler.findNode(this.root, node.idParent);
    if (!newParent || !oldParent) return false;

    oldParent.listaHijos.splice(oldParent.listaHijos.findIndex(h => h.id === fromId), 1);
    oldParent.down = oldParent.listaHijos.length > 0 ? 1 : 0;

    const afterIdx = newParent.listaHijos.findIndex(h => h.id === afterId);
    node.idParent = newParent.id;
    node.up = 0; node.left = 0; node.right = 0;
    newParent.listaHijos.splice(afterIdx + 1, 0, node);
    return true;
  }

  // ── layout y render ────────────────────────────────────────────────────────

  treeToMax() {
    this.layout.toMatrix(this.root);
  }

  render({ container = "#igm-board" } = {}) {
    this.layout.render({ container });
  }

  // ── serialización ──────────────────────────────────────────────────────────

  toJson() {
    const serNode = (chart) => ({
      id:         chart.id,
      idParent:   chart.idParent,
      chartType:  chart.chartType,
      model:      serModel(chart.chartType, chart.model),
      collapsed:  chart.collapsed,
      listaHijos: chart.listaHijos.map(serNode),
    });
    return JSON.stringify({ lastId: this.lastId, root: serNode(this.root) }, null, 2);
  }

  fromJson(json) {
    const data = typeof json === "string" ? JSON.parse(json) : json;

    const buildNode = (d) => {
      const chart = new Chart({
        id:        d.id,
        idParent:  d.idParent,
        chartType: d.chartType,
        model:     deserModel(d.chartType, d.model),
        collapsed: d.collapsed ?? false,
      });
      for (const hd of d.listaHijos) chart.addChild(buildNode(hd));
      return chart;
    };

    this.root   = buildNode(data.root);
    this.lastId = data.lastId;
    this.layout = new Organigram(this.root);
  }
}

// ── helpers de serialización del modelo ────────────────────────────────────

function serModel(chartType, model) {
  if (!model) return null;
  if (chartType === "category") {
    return {
      name:       model.name,
      id:         model.id ?? null,
      attributes: (model.attributes ?? []).map(a => (typeof a.to_json === "function" ? a.to_json() : a)),
    };
  }
  if (chartType === "product") {
    return {
      code:        model.code,
      title:       model.title,
      price:       model.price,
      description: model.description,
      brand:       model.brand,
      id:          model.id ?? null,
      attributes_implementations: (model.attributes_implementations ?? []).map(ai =>
        typeof ai.to_json === "function"
          ? ai.to_json()
          : { id: ai.id ?? null, attribute: ai.attribute, value: ai.value }
      ),
    };
  }
  if (chartType === "variant") {
    return {
      id: model.id ?? null,
      attribute_implementations: (model.attribute_implementations ?? []).map(ai =>
        typeof ai.to_json === "function" ? ai.to_json() : ai
      ),
    };
  }
  return null;
}

// Para el MVP, deserializamos a objetos planos que el render puede leer.
// La reconstrucción de objetos de dominio completos (con clases y validaciones)
// queda para cuando el árbol se integre con la capa de negocio.
function deserModel(chartType, data) {
  if (!data) return null;
  if (chartType === "category") {
    return { id: data.id ?? null, name: data.name, attributes: data.attributes ?? [] };
  }
  if (chartType === "product") {
    return {
      id:                         data.id ?? null,
      code:                       data.code,
      title:                      data.title,
      price:                      data.price,
      description:                data.description,
      brand:                      data.brand,
      attributes_implementations: data.attributes_implementations ?? [],
    };
  }
  if (chartType === "variant") {
    return { id: data.id ?? null, attribute_implementations: data.attribute_implementations ?? [] };
  }
  return null;
}
