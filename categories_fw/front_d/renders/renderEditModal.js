// Renders para el modal de edición de nodos (category attr list + variant impls).
// Reciben el contenedor y los datos; los callbacks de negocio los provee events.js.

export function renderAttrList(container, attrs, onRemove) {
  container.innerHTML = "";
  if (attrs.length === 0) {
    const span = document.createElement("span");
    span.className   = "igm-body-empty";
    span.textContent = "Sin atributos";
    container.appendChild(span);
    return;
  }
  attrs.forEach((attr, idx) => {
    const item = document.createElement("div");
    item.className = "igm-attr-item";

    const info = document.createElement("div");
    info.className = "igm-attr-item-info";
    info.innerHTML =
      `<span class="igm-attr-item-key">${attr.key}</span>` +
      `<span class="igm-attr-item-meta">${attr.name}</span>` +
      `<span class="igm-attr-item-type">${attr.data_type}</span>` +
      (attr.is_static
        ? `<span class="igm-attr-item-type igm-attr-item-static">producto</span>`
        : `<span class="igm-attr-item-type igm-attr-item-dyn">variante</span>`);

    const removeBtn = document.createElement("button");
    removeBtn.className   = "igm-attr-remove";
    removeBtn.textContent = "×";
    removeBtn.title       = "Quitar atributo";
    removeBtn.addEventListener("click", () => onRemove(attr, idx));

    item.appendChild(info);
    item.appendChild(removeBtn);
    container.appendChild(item);
  });
}

export function renderImplsEditable(container, impls) {
  if (!container) return;
  container.innerHTML = "";
  if (!impls || impls.length === 0) {
    const span = document.createElement("span");
    span.className   = "igm-body-empty";
    span.textContent = "Sin implementaciones";
    container.appendChild(span);
    return;
  }
  impls.forEach((impl, idx) => {
    const attr = impl.attribute ?? {};
    const row  = document.createElement("div");
    row.className = "igm-impl-row";

    const label = document.createElement("label");
    label.className   = "igm-impl-label";
    label.textContent = attr.name ?? attr.key ?? "?";
    label.htmlFor     = `igm-impl-${idx}`;

    let input;
    if (attr.data_type === "boolean") {
      input         = document.createElement("input");
      input.type    = "checkbox";
      input.checked = impl.value === true || impl.value === "true";
    } else if (attr.data_type === "enum" && attr.enum_values?.length > 0) {
      input = document.createElement("select");
      attr.enum_values.forEach(v => {
        const opt = document.createElement("option");
        opt.value = opt.textContent = v;
        if (String(v) === String(impl.value)) opt.selected = true;
        input.appendChild(opt);
      });
    } else {
      input       = document.createElement("input");
      input.type  = attr.data_type === "number" ? "number" : "text";
      input.value = impl.value ?? "";
    }
    input.id              = `igm-impl-${idx}`;
    input.dataset.implIdx = idx;

    row.appendChild(label);
    row.appendChild(input);
    container.appendChild(row);
  });
}
