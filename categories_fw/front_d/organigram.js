import { Chart } from "./charts.js";
import { Void, WireTop } from "./btandvoid.js";
import { renderChart } from "./renders/renderBoard.js";

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

  // ── toMatrix ───────────────────────────────────────────────────────────────

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
      const hijos = node.listaHijos ?? [];

      node.up    = depth > 0 ? 1 : 0;
      node.down  = hijos.length > 0 ? 1 : 0;
      node.left  = 0;
      node.right = 0;

      if (hijos.length === 0) {
        this.setAt(depth, startCol, node);
        return startCol;
      }

      // Colocar hijos primero para obtener sus columnas reales
      const childRow = depth + 1;
      let cs = startCol;
      const placedCols = hijos.map(hijo => {
        const col = place(hijo, cs, depth + 1);
        cs += widths.get(hijo.id) ?? 1;
        return col;
      });

      // Centrar el padre sobre el span real de sus hijos
      const leftCol  = placedCols[0];
      const rightCol = placedCols[placedCols.length - 1];
      const nodeCol  = Math.round((leftCol + rightCol) / 2);

      this.setAt(depth, nodeCol, node);

      if (hijos.length > 1) {
        hijos[0].right = 1;
        hijos[hijos.length - 1].left = 1;
        for (let i = 1; i < hijos.length - 1; i++) {
          hijos[i].left = 1; hijos[i].right = 1;
        }
      }

      for (let c = leftCol; c <= rightCol; c++) {
        if (!placedCols.includes(c)) this.setAt(childRow, c, new WireTop());
      }

      return nodeCol;
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
          renderChart(cellEl, cell, root, has);
        } else if (cell instanceof WireTop) {
          const wire = document.createElement("div");
          wire.className = "igm-wire-top";
          cellEl.appendChild(wire);
        }
      }
    }
  }
}
