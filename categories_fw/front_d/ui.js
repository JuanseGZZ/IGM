// ── Gestor dialog ──────────────────────────────────────────────────────────────

function createGestorModal() {
  const overlay = document.createElement("div");
  overlay.id        = "igm-gestor-overlay";
  overlay.className = "igm-modal-overlay igm-hidden";

  const modal = document.createElement("div");
  modal.id        = "igm-gestor-modal";
  modal.className = "igm-modal";
  modal.innerHTML = `
    <h3 id="igm-gestor-title"></h3>
    <p  id="igm-gestor-desc"  class="igm-gestor-desc"></p>
    <div id="igm-gestor-deletions" class="igm-gestor-section igm-hidden"></div>
    <div id="igm-gestor-inputs"    class="igm-gestor-section igm-hidden"></div>
    <div class="igm-modal-actions">
      <button id="igm-gestor-cancel"  class="igm-btn-secondary">Cancelar</button>
      <button id="igm-gestor-confirm" class="igm-btn-primary">Confirmar</button>
    </div>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}

// Muestra el dialog del Gestor.
// inputs:    [{ attr, label, dataType, options, hint, productId? }]
// deletions: [{ label }]
// onConfirm(filledValues) — filledValues: [{ ...inputSpec, value }]
export function showGestorDialog({
  title,
  description = "",
  inputs      = [],
  deletions   = [],
  confirmLabel = "Confirmar",
  onConfirm,
  onCancel,
}) {
  const overlay    = document.getElementById("igm-gestor-overlay");
  const titleEl    = document.getElementById("igm-gestor-title");
  const descEl     = document.getElementById("igm-gestor-desc");
  const deletionEl = document.getElementById("igm-gestor-deletions");
  const inputsEl   = document.getElementById("igm-gestor-inputs");

  titleEl.textContent = title;
  descEl.textContent  = description;

  // Sección de eliminaciones
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

  // Sección de inputs aditivos
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
        el      = document.createElement("input");
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

  // Reemplazar botones para limpiar listeners viejos
  const actionsDiv  = overlay.querySelector(".igm-modal-actions");
  const oldConfirm  = document.getElementById("igm-gestor-confirm");
  const oldCancel   = document.getElementById("igm-gestor-cancel");
  const newConfirm  = oldConfirm.cloneNode(true);
  const newCancel   = oldCancel.cloneNode(true);
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

// ── Creación del modal ─────────────────────────────────────────────────────────

function createModal() {
  const overlay = document.createElement("div");
  overlay.id        = "igm-modal-overlay";
  overlay.className = "igm-modal-overlay igm-hidden";

  const modal = document.createElement("div");
  modal.id        = "igm-modal";
  modal.className = "igm-modal";

  // título dinámico
  const title = document.createElement("h3");
  title.id = "igm-modal-title";
  modal.appendChild(title);

  // ── Sección: Category ─────────────────────────────────────────────────────
  const secCat = document.createElement("div");
  secCat.id        = "igm-sec-category";
  secCat.className = "igm-modal-section";
  secCat.innerHTML = `
    <label for="igm-cat-name">Nombre</label>
    <input id="igm-cat-name" type="text" placeholder="Nombre de la categoría" />

    <div class="igm-attr-manager">
      <h4>Atributos</h4>
      <div id="igm-attr-list" class="igm-attr-list"></div>

      <div class="igm-attr-add-form">
        <div>
          <label>key</label>
          <input id="igm-attr-key" type="text" placeholder="ej: color" />
        </div>
        <div>
          <label>nombre</label>
          <input id="igm-attr-name-inp" type="text" placeholder="ej: Color" />
        </div>
        <div>
          <label>tipo</label>
          <select id="igm-attr-dtype">
            <option value="text">text</option>
            <option value="number">number</option>
            <option value="boolean">boolean</option>
            <option value="enum">enum</option>
          </select>
        </div>
        <div>
          <label>es estático</label>
          <select id="igm-attr-static">
            <option value="false">No (variante)</option>
            <option value="true">Sí (producto)</option>
          </select>
        </div>
        <div class="igm-attr-add-full">
          <button id="igm-attr-add-btn" class="igm-attr-add-btn">+ Agregar atributo</button>
        </div>
      </div>
    </div>
  `;
  modal.appendChild(secCat);

  // ── Sección: Product ──────────────────────────────────────────────────────
  const secProd = document.createElement("div");
  secProd.id        = "igm-sec-product";
  secProd.className = "igm-modal-section";
  secProd.innerHTML = `
    <label for="igm-prod-title">Título</label>
    <input id="igm-prod-title" type="text" placeholder="Nombre del producto" />
    <label for="igm-prod-code">Código (SKU)</label>
    <input id="igm-prod-code" type="text" placeholder="ABC-001" />
    <label for="igm-prod-price">Precio</label>
    <input id="igm-prod-price" type="number" placeholder="0.00" min="0" step="0.01" />
    <label for="igm-prod-brand">Marca</label>
    <input id="igm-prod-brand" type="text" placeholder="Marca" />
    <label for="igm-prod-desc">Descripción</label>
    <textarea id="igm-prod-desc" rows="3" placeholder="Descripción opcional"></textarea>
  `;
  modal.appendChild(secProd);

  // ── Sección: Variant ──────────────────────────────────────────────────────
  const secVar = document.createElement("div");
  secVar.id        = "igm-sec-variant";
  secVar.className = "igm-modal-section";
  secVar.innerHTML = `
    <p style="font-size:13px;color:#666;margin:0 0 12px;">
      Las implementaciones de atributos de la variante se gestionan
      a través de la integración con el dominio.
    </p>
    <div id="igm-var-impls"></div>
  `;
  modal.appendChild(secVar);

  // ── Acciones ──────────────────────────────────────────────────────────────
  const actions = document.createElement("div");
  actions.className = "igm-modal-actions";
  actions.innerHTML = `
    <button id="igm-modal-cancel" class="igm-btn-secondary">Cancelar</button>
    <button id="igm-modal-save"   class="igm-btn-primary">Guardar</button>
  `;
  modal.appendChild(actions);

  overlay.appendChild(modal);
  document.body.appendChild(overlay);
}

// ── API pública ────────────────────────────────────────────────────────────────

export function initUI() {
  createGestorModal();
  createModal();
}

// Muestra un menú flotante de opciones anclado a anchorEl.
// opciones: [{ value, label }]
// onSelect(value) se llama al elegir.
export function showMenu(anchorEl, opciones, onSelect) {
  // limpiar menús anteriores
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
