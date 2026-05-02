import { Chart, CHART_TYPE, CHART_BG, CHART_LABEL } from "./charts.js";
import { Void, WireTop } from "./btandvoid.js";

export class Organigram {
  constructor(root) {
    this.nodoRaiz = root;
    this.matiz    = [];
  }

  setRoot(root) { this.nodoRaiz = root; }

  // ── helpers de matriz ──────────────────────────────────────────────────────

  ensureSize(rows, cols) {
    while (this.matiz.length <= rows) this.matiz.push([]);
    for (let y = 0; y <= rows; y++) {
      while (this.matiz[y].length <= cols) this.matiz[y].push(new Void());
    }
  }

  setAt(y, x, v) { this.ensureSize(y, x); this.matiz[y][x] = v; }

  getAt(y, x) {
    if (y < 0 || x < 0 || y >= this.matiz.length || x >= this.matiz[y].length) return undefined;
    return this.matiz[y][x];
  }

  // ── toMatrix (mismo algoritmo que Diagramer, adaptado a Chart.id) ─────────

  toMatrix(root) {
    this.setRoot(root);
    this.matiz = [];

    const widths = new Map();
    const calcWidth = (node) => {
      const hijos = node.listaHijos ?? [];
      const w = hijos.length === 0 ? 1 : hijos.reduce((s, h) => s + calcWidth(h), 0);
      widths.set(node.id, w);
      return w;
    };
    for (const hijo of root.listaHijos) calcWidth(hijo);

    const place = (node, startCol, depth) => {
      const w       = widths.get(node.id) ?? 1;
      const nodeCol = startCol + Math.floor((w - 1) / 2);

      node.up    = depth > 0 ? 1 : 0;
      node.down  = (node.listaHijos?.length ?? 0) > 0 ? 1 : 0;
      node.left  = 0;
      node.right = 0;

      this.setAt(depth, nodeCol, node);

      const hijos = node.listaHijos ?? [];
      if (hijos.length === 0) return;

      const childRow = depth + 1;
      let cs = startCol;
      const childCols = hijos.map(h => {
        const cw  = widths.get(h.id) ?? 1;
        const col = cs + Math.floor((cw - 1) / 2);
        cs += cw;
        return col;
      });

      cs = startCol;
      for (const hijo of hijos) {
        place(hijo, cs, depth + 1);
        cs += widths.get(hijo.id) ?? 1;
      }

      // flags left/right DESPUÉS de la recursión
      if (hijos.length > 1) {
        hijos[0].right = 1;
        hijos[hijos.length - 1].left = 1;
        for (let i = 1; i < hijos.length - 1; i++) {
          hijos[i].left = 1; hijos[i].right = 1;
        }
      }

      // WireTop en columnas gap entre hermanos no adyacentes
      const leftCol  = childCols[0];
      const rightCol = childCols[childCols.length - 1];
      for (let c = leftCol; c <= rightCol; c++) {
        if (!childCols.includes(c)) this.setAt(childRow, c, new WireTop());
      }
    };

    let startCol = 0;
    for (const hijo of root.listaHijos) {
      place(hijo, startCol, 0);
      startCol += widths.get(hijo.id) ?? 1;
    }
  }

  // ── render: matriz → DOM ──────────────────────────────────────────────────

  render({ container = "#igm-board" } = {}) {
    const root = typeof container === "string"
      ? document.querySelector(container)
      : container;
    if (!root) { console.error("Organigram: contenedor no encontrado", container); return; }

    const mat  = this.matiz;
    root.innerHTML = "";
    root.className = "igm-board igm-organigram";

    const rows = mat.length;
    const cols = mat.reduce((m, r) => Math.max(m, r?.length ?? 0), 0);
    root.style.gridTemplateColumns = `repeat(${cols}, var(--igm-cell-w, 210px))`;

    const has = (obj, k) => !!(obj && (obj[k] === true || obj[k] === 1));

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell   = this.getAt(y, x);
        const cellEl = document.createElement("div");
        cellEl.className = "igm-cell";
        root.appendChild(cellEl);

        if (cell instanceof Chart) {
          this._renderChart(cellEl, cell, root, has);
        } else if (cell instanceof WireTop) {
          const wire = document.createElement("div");
          wire.className = "igm-wire-top";
          cellEl.appendChild(wire);
        }
      }
    }
  }

  _renderChart(cellEl, chart, board, has) {
    const color = CHART_BG[chart.chartType] ?? "#888";

    // ── box ───────────────────────────────────────────────────────────────────
    const box = document.createElement("div");
    box.className   = `igm-box igm-box-${chart.chartType}`;
    box.dataset.id  = String(chart.id);
    box.draggable   = true;
    box.style.setProperty("--chart-color", color);
    if (chart.collapsed) box.classList.add("igm-collapsed");
    cellEl.appendChild(box);

    // header
    const header = document.createElement("div");
    header.className = "igm-box-header";
    header.style.backgroundColor = color;

    const badge = document.createElement("span");
    badge.className   = "igm-type-badge";
    badge.textContent = CHART_LABEL[chart.chartType] ?? chart.chartType;
    header.appendChild(badge);

    const btnCollapse = document.createElement("button");
    btnCollapse.className   = "igm-btn igm-btn-collapse";
    btnCollapse.textContent = chart.collapsed ? "▼" : "▲";
    btnCollapse.addEventListener("click", () => {
      chart.collapsed = !chart.collapsed;
      box.classList.toggle("igm-collapsed", chart.collapsed);
      btnCollapse.textContent = chart.collapsed ? "▼" : "▲";
      board.dispatchEvent(new CustomEvent("igm-collapse"));
    });
    header.appendChild(btnCollapse);

    const btnDel = document.createElement("button");
    btnDel.className   = "igm-btn igm-btn-del";
    btnDel.dataset.id  = String(chart.id);
    btnDel.textContent = "×";
    header.appendChild(btnDel);

    box.appendChild(header);

    // title
    const titleEl = document.createElement("div");
    titleEl.className   = "igm-box-title";
    titleEl.textContent = chart.label;
    box.appendChild(titleEl);

    // body
    const bodyEl = document.createElement("div");
    bodyEl.className = "igm-box-body";
    bodyEl.appendChild(this._renderBody(chart));
    box.appendChild(bodyEl);

    // edges (conectores)
    if (has(chart, "up"))    this._addEdge(cellEl, "up");
    if (has(chart, "down"))  this._addEdge(cellEl, "down");
    if (has(chart, "left"))  this._addEdge(cellEl, "left");
    if (has(chart, "right")) this._addEdge(cellEl, "right");

    // botones "+"
    if (!has(chart, "down"))  this._addBtn(cellEl, "down",  chart, board);
    if (!has(chart, "right")) this._addBtn(cellEl, "right", chart, board);
  }

  _renderBody(chart) {
    const wrap = document.createElement("div");
    wrap.className = "igm-body-content";

    if (chart.chartType === CHART_TYPE.CATEGORY && chart.model) {
      const attrs = chart.model.attributes ?? [];
      if (attrs.length === 0) {
        wrap.appendChild(empty("Sin atributos"));
      } else {
        attrs.forEach(attr => {
          const pill = document.createElement("span");
          pill.className   = `igm-pill ${attr.is_static ? "igm-pill-static" : "igm-pill-dynamic"}`;
          pill.textContent = `${attr.key}: ${attr.name}`;
          pill.title       = attr.data_type;
          wrap.appendChild(pill);
        });
      }
    } else if (chart.chartType === CHART_TYPE.PRODUCT && chart.model) {
      const m = chart.model;
      [["cod", m.code], ["marca", m.brand], ["precio", m.price != null ? `$${m.price}` : null]]
        .filter(([, v]) => v != null && v !== "")
        .forEach(([label, value]) => {
          const row = document.createElement("div");
          row.className = "igm-field-row";
          row.innerHTML = `<span class="igm-field-label">${label}</span><span class="igm-field-value">${value}</span>`;
          wrap.appendChild(row);
        });
    } else if (chart.chartType === CHART_TYPE.VARIANT && chart.model) {
      const impls = chart.model.attribute_implementations ?? [];
      if (impls.length === 0) {
        wrap.appendChild(empty("Sin implementaciones"));
      } else {
        impls.forEach(impl => {
          const pill = document.createElement("span");
          pill.className   = "igm-pill igm-pill-impl";
          pill.textContent = `${impl.attribute?.key ?? "?"}: ${impl.value}`;
          wrap.appendChild(pill);
        });
      }
    }

    return wrap;
  }

  _addEdge(parent, dir) {
    const e = document.createElement("div");
    e.className = `igm-edge igm-edge-${dir}`;
    parent.appendChild(e);
  }

  _addBtn(cellEl, dir, chart, board) {
    const btn = document.createElement("button");
    btn.className   = `igm-add-btn igm-add-${dir}`;
    btn.textContent = "+";
    btn.dataset.id  = String(chart.id);
    btn.dataset.dir = dir;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      board.dispatchEvent(new CustomEvent("igm-add-chart", {
        bubbles: true,
        detail: { fromId: chart.id, dir },
      }));
    });
    cellEl.appendChild(btn);
  }
}

function empty(text) {
  const s = document.createElement("span");
  s.className   = "igm-body-empty";
  s.textContent = text;
  return s;
}
