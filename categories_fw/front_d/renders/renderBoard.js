/**
 * renders/renderBoard.js
 *
 * Construye el DOM de una celda del organigrama: carta (.igm-box),
 * conectores (.igm-edge-*) y botones de agregar (.igm-add-btn).
 *
 * Contrato: no importa handler, gestor ni stores.
 * Toda acción que cambia estado se delega a events.js vía el evento
 * "igm-add-chart" disparado sobre `board`.
 */

import { CHART_TYPE, CHART_BG, CHART_LABEL } from "../charts.js";

/**
 * Rellena `cellEl` con la carta del chart y sus decoraciones de celda.
 *
 * @param {HTMLElement} cellEl  - Celda del grid (.igm-cell) que recibirá el contenido.
 * @param {Chart}       chart   - Nodo del árbol visual a renderizar.
 * @param {HTMLElement} board   - #igm-board; receptor de eventos personalizados.
 * @param {Function}    has     - has(chart, dir) → bool; indica si el chart tiene
 *                                conector en esa dirección ("up"|"down"|"left"|"right").
 */
export function renderChart(cellEl, chart, board, has) {
  const color = CHART_BG[chart.chartType] ?? "#888";

  const box = document.createElement("div");
  box.className  = `igm-box igm-box-${chart.chartType}`;
  box.dataset.id = String(chart.id);
  box.draggable  = true;
  // expone el color como variable CSS para que reglas derivadas puedan usarlo
  box.style.setProperty("--chart-color", color);
  if (chart.collapsed) box.classList.add("igm-collapsed");
  cellEl.appendChild(box);

  // ── Header ───────────────────────────────────────────────────────────────────

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
    // events.js escucha este evento para persistir el estado en localStorage
    board.dispatchEvent(new CustomEvent("igm-collapse"));
  });
  header.appendChild(btnCollapse);

  // btnDel no dispara evento: events.js lo captura por delegación con .closest()
  const btnDel = document.createElement("button");
  btnDel.className   = "igm-btn igm-btn-del";
  btnDel.dataset.id  = String(chart.id);
  btnDel.textContent = "×";
  header.appendChild(btnDel);

  box.appendChild(header);

  // ── Título ───────────────────────────────────────────────────────────────────

  const titleEl = document.createElement("div");
  titleEl.className   = "igm-box-title";
  titleEl.textContent = chart.label;
  box.appendChild(titleEl);

  // ── Body ─────────────────────────────────────────────────────────────────────

  const bodyEl = document.createElement("div");
  bodyEl.className = "igm-box-body";
  bodyEl.appendChild(renderBody(chart));
  box.appendChild(bodyEl);

  // ── Conectores ───────────────────────────────────────────────────────────────
  // Los edges son divs absolutos dentro de .igm-cell; el padding-top/bottom de
  // la celda (--igm-pad-top / --igm-pad-bottom) define el espacio donde viven.

  if (has(chart, "up"))    addEdge(cellEl, "up");
  if (has(chart, "down"))  addEdge(cellEl, "down");
  if (has(chart, "left"))  addEdge(cellEl, "left");
  if (has(chart, "right")) addEdge(cellEl, "right");

  // ── Botones "+" ──────────────────────────────────────────────────────────────
  // Se muestran solo cuando no hay conector en esa dirección (= no hay nodo ahí).
  // Variantes no tienen botón "abajo": no pueden tener hijos.
  // Nodos raíz (idParent === 0) no tienen botón "derecha": el árbol parte de
  // una única categoría raíz; agregar hermanos en ese nivel está deshabilitado.

  if (!has(chart, "down") && chart.chartType !== CHART_TYPE.VARIANT)
    addBtn(cellEl, "down", chart, board);
  if (!has(chart, "right") && chart.idParent !== 0)
    addBtn(cellEl, "right", chart, board);
}

// ── Funciones internas ────────────────────────────────────────────────────────

/**
 * Construye el contenido del body según el tipo de chart.
 *
 * - category → pills de atributos (azul = estático, rosa = dinámico)
 * - product  → filas cod / marca / precio
 * - variant  → pills de implementaciones (key: valor)
 *
 * @param   {Chart}       chart
 * @returns {HTMLElement} div.igm-body-content
 */
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

/**
 * Agrega un conector visual (.igm-edge-{dir}) a la celda.
 *
 * @param {HTMLElement} parent - .igm-cell
 * @param {"up"|"down"|"left"|"right"} dir
 */
function addEdge(parent, dir) {
  const e = document.createElement("div");
  e.className = `igm-edge igm-edge-${dir}`;
  parent.appendChild(e);
}

/**
 * Agrega un botón "+" a la celda y lo conecta al evento "igm-add-chart".
 * events.js escucha ese evento en #igm-board para abrir el modal de creación.
 *
 * @param {HTMLElement} cellEl
 * @param {"down"|"right"} dir
 * @param {Chart}       chart
 * @param {HTMLElement} board
 */
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

/**
 * @param   {string}      text
 * @returns {HTMLElement} span.igm-body-empty
 */
function emptySpan(text) {
  const s = document.createElement("span");
  s.className   = "igm-body-empty";
  s.textContent = text;
  return s;
}
