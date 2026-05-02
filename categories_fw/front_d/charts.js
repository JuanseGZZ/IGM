export const CHART_TYPE = {
  CATEGORY: "category",
  PRODUCT:  "product",
  VARIANT:  "variant",
};

export const CHART_BG = {
  category: "#f97316",
  product:  "#3b82f6",
  variant:  "#8b5cf6",
};

export const CHART_LABEL = {
  category: "Categoría",
  product:  "Producto",
  variant:  "Variante",
};

export class Chart {
  constructor({ id, idParent = null, chartType = CHART_TYPE.CATEGORY, model = null, collapsed = false }) {
    this.id         = id;
    this.idParent   = idParent;
    this.chartType  = chartType;
    this.model      = model;
    this.collapsed  = collapsed;
    this.listaHijos = [];

    // flags de dibujo de conectores
    this.up    = 0;
    this.down  = 0;
    this.left  = 0;
    this.right = 0;
  }

  get label() {
    if (!this.model) return "(vacío)";
    if (this.chartType === CHART_TYPE.CATEGORY) return this.model.name  ?? "(categoría)";
    if (this.chartType === CHART_TYPE.PRODUCT)  return this.model.title ?? this.model.code ?? "(producto)";
    if (this.chartType === CHART_TYPE.VARIANT)  return `Variante #${this.id}`;
    return "";
  }

  addChild(child) {
    if (this.listaHijos.length === 0) this.down = 1;
    if (this.listaHijos.length >= 1) {
      child.left = 1;
      this.listaHijos[this.listaHijos.length - 1].right = 1;
    }
    if (this.idParent !== null && this.listaHijos.length === 0) child.up = 1;
    this.listaHijos.push(child);
  }
}
