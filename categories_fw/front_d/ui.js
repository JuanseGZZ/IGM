// ── Gestor dialog ──────────────────────────────────────────────────────────────

export function showGestorDialog({
  title,
  description  = "",
  inputs       = [],
  deletions    = [],
  confirmLabel = "Confirmar",
  onConfirm,
  onCancel,
}) {
  const overlay    = document.getElementById("igm-gestor-overlay");
  // Mover al final de body garantiza que quede por encima de cualquier otro overlay,
  // independientemente del orden de creación.
  document.body.appendChild(overlay);

  const titleEl    = document.getElementById("igm-gestor-title");
  const descEl     = document.getElementById("igm-gestor-desc");
  const deletionEl = document.getElementById("igm-gestor-deletions");
  const inputsEl   = document.getElementById("igm-gestor-inputs");

  titleEl.textContent = title;
  descEl.textContent  = description;

  deletionEl.innerHTML = "";
  if (deletions.length > 0) {
    const ul = document.createElement("ul");
    ul.className = "igm-gestor-del-list";
    deletions.forEach(({ label }) => {
      const li = document.createElement("li");
      li.textContent = label;
      ul.appendChild(li);
    });
    deletionEl.appendChild(ul);
    deletionEl.classList.remove("igm-hidden");
  } else {
    deletionEl.classList.add("igm-hidden");
  }

  inputsEl.innerHTML = "";
  const inputRefs = [];
  if (inputs.length > 0) {
    inputs.forEach((spec, idx) => {
      const group = document.createElement("div");
      group.className = "igm-gestor-input-group";
      const lbl = document.createElement("label");
      lbl.textContent = spec.label;
      lbl.htmlFor     = `igm-gin-${idx}`;
      group.appendChild(lbl);
      let el;
      if (spec.dataType === "boolean") {
        el = document.createElement("input");
        el.type = "checkbox";
        el.id   = `igm-gin-${idx}`;
      } else if (spec.dataType === "enum" && spec.options?.length > 0) {
        el    = document.createElement("select");
        el.id = `igm-gin-${idx}`;
        spec.options.forEach(v => {
          const opt = document.createElement("option");
          opt.value = opt.textContent = v;
          el.appendChild(opt);
        });
      } else {
        el             = document.createElement("input");
        el.type        = spec.dataType === "number" ? "number" : "text";
        el.id          = `igm-gin-${idx}`;
        el.placeholder = spec.hint ?? "";
      }
      group.appendChild(el);
      inputsEl.appendChild(group);
      inputRefs.push({ spec, el });
    });
    inputsEl.classList.remove("igm-hidden");
  } else {
    inputsEl.classList.add("igm-hidden");
  }

  const actionsDiv = overlay.querySelector(".igm-modal-actions");
  const oldConfirm = document.getElementById("igm-gestor-confirm");
  const oldCancel  = document.getElementById("igm-gestor-cancel");
  const newConfirm = oldConfirm.cloneNode(true);
  const newCancel  = oldCancel.cloneNode(true);
  newConfirm.textContent = confirmLabel;
  actionsDiv.replaceChild(newConfirm, oldConfirm);
  actionsDiv.replaceChild(newCancel,  oldCancel);

  let handled = false;
  const resolve = (confirmed) => {
    if (handled) return;
    handled = true;
    overlay.classList.add("igm-hidden");
    if (confirmed) {
      const filled = inputRefs.map(({ spec, el }) => ({
        ...spec,
        value: el.type === "checkbox" ? el.checked : el.value,
      }));
      onConfirm?.(filled);
    } else {
      onCancel?.();
    }
  };

  newConfirm.addEventListener("click", () => resolve(true));
  newCancel.addEventListener("click",  () => resolve(false));
  overlay.addEventListener("click", (ev) => { if (ev.target === overlay) resolve(false); }, { once: true });

  overlay.classList.remove("igm-hidden");
  if (inputRefs.length > 0) inputRefs[0].el.focus();
}

// ── Zoom & pan ────────────────────────────────────────────────────────────────

export function initZoom() {
  const board          = document.querySelector("#igm-board");
  const boardContainer = document.querySelector("#igm-board-container");

  let zoomLevel = 1.0;
  const ZOOM_STEP = 0.03;
  const ZOOM_MIN  = 0.2;
  const ZOOM_MAX  = 3.0;

  function applyZoom(z) {
    zoomLevel        = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, +z.toFixed(2)));
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

  function zoomAroundCenter(newZ) {
    if (!boardContainer) { applyZoom(newZ); return; }
    const cx = boardContainer.scrollLeft + boardContainer.clientWidth  / 2;
    const cy = boardContainer.scrollTop  + boardContainer.clientHeight / 2;
    const bx = cx / zoomLevel;
    const by = cy / zoomLevel;
    applyZoom(newZ);
    boardContainer.scrollLeft = bx * zoomLevel - boardContainer.clientWidth  / 2;
    boardContainer.scrollTop  = by * zoomLevel - boardContainer.clientHeight / 2;
  }

  document.querySelectorAll("[data-igm='zoom-in']").forEach(b =>
    b.addEventListener("click", () => zoomAroundCenter(zoomLevel + ZOOM_STEP)));
  document.querySelectorAll("[data-igm='zoom-out']").forEach(b =>
    b.addEventListener("click", () => zoomAroundCenter(zoomLevel - ZOOM_STEP)));
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
}

export function showMenu(anchorEl, opciones, onSelect) {
  document.querySelectorAll(".igm-floating-menu").forEach(m => m.remove());

  const menu = document.createElement("ul");
  menu.className = "igm-menu-dropdown igm-floating-menu";
  menu.style.display = "block";

  for (const { value, label } of opciones) {
    const li  = document.createElement("li");
    const btn = document.createElement("button");
    btn.type        = "button";
    btn.textContent = label;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      menu.remove();
      onSelect(value);
    });
    li.appendChild(btn);
    menu.appendChild(li);
  }

  const rect = anchorEl.getBoundingClientRect();
  menu.style.left = `${rect.left}px`;
  menu.style.top  = `${rect.bottom + 6}px`;
  document.body.appendChild(menu);

  const close = (e) => {
    if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener("click", close); }
  };
  setTimeout(() => document.addEventListener("click", close), 0);
}
