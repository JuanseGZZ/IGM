// Render del board: construcción DOM de cada chart (carta) y sus conectores.
// Extraído de organigram.js para separar layout (matriz) de presentación (DOM).

import { CHART_TYPE, CHART_BG, CHART_LABEL } from "../charts.js";

export function renderChart(cellEl, chart, board, has) {
  const color = CHART_BG[chart.chartType] ?? "#888";

  const box = document.createElement("div");
  box.className  = `igm-box igm-box-${chart.chartType}`;
  box.dataset.id = String(chart.id);
  box.draggable  = true;
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
  bodyEl.appendChild(renderBody(chart));
  box.appendChild(bodyEl);

  // conectores
  if (has(chart, "up"))    addEdge(cellEl, "up");
  if (has(chart, "down"))  addEdge(cellEl, "down");
  if (has(chart, "left"))  addEdge(cellEl, "left");
  if (has(chart, "right")) addEdge(cellEl, "right");

  // botones "+"
  if (!has(chart, "down"))  addBtn(cellEl, "down",  chart, board);
  if (!has(chart, "right")) addBtn(cellEl, "right", chart, board);
}

function renderBody(chart) {
  const wrap = document.createElement("div");
  wrap.className = "igm-body-content";

  if (chart.chartType === CHART_TYPE.CATEGORY && chart.model) {
    const attrs = chart.model.attributes ?? [];
    if (attrs.length === 0) {
      wrap.appendChild(emptySpan("Sin atributos"));
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
      wrap.appendChild(emptySpan("Sin implementaciones"));
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

function addEdge(parent, dir) {
  const e = document.createElement("div");
  e.className = `igm-edge igm-edge-${dir}`;
  parent.appendChild(e);
}

function addBtn(cellEl, dir, chart, board) {
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

function emptySpan(text) {
  const s = document.createElement("span");
  s.className   = "igm-body-empty";
  s.textContent = text;
  return s;
}
