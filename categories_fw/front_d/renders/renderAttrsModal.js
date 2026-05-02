// Renders para el modal CRUD de atributos globales (navbar "Atributos").

export function renderAttrRows(listEl, attrs, onRemove) {
  listEl.innerHTML = "";
  if (attrs.length === 0) {
    const p = document.createElement("p");
    p.className   = "igm-body-empty";
    p.textContent = "Sin atributos. Creá uno con el formulario de abajo.";
    listEl.appendChild(p);
    return;
  }
  attrs.forEach(attr => {
    const row = document.createElement("div");
    row.className = "igm-attr-row";

    const info = document.createElement("div");
    info.className = "igm-attr-row-info";
    info.innerHTML =
      `<span class="igm-attr-item-key">${attr.key}</span>` +
      `<span class="igm-attr-item-meta">${attr.name}</span>` +
      `<span class="igm-attr-item-type">${attr.data_type}</span>` +
      `<span class="igm-attr-item-type ${attr.is_static ? "igm-attr-item-static" : "igm-attr-item-dyn"}">${attr.is_static ? "producto" : "categoría"}</span>` +
      (attr.data_type === "enum" && attr.enum_values.length > 0
        ? `<span class="igm-attr-enum-hint">[${attr.enum_values.join(", ")}]</span>`
        : "");

    const delBtn = document.createElement("button");
    delBtn.className   = "igm-attr-remove";
    delBtn.textContent = "×";
    delBtn.title       = "Eliminar atributo";
    delBtn.addEventListener("click", () => onRemove(attr));

    row.appendChild(info);
    row.appendChild(delBtn);
    listEl.appendChild(row);
  });
}

export function renderEnumValues(listEl, values, onRemoveIdx) {
  listEl.innerHTML = "";
  values.forEach((val, idx) => {
    const item = document.createElement("div");
    item.className = "igm-enum-item";

    const span = document.createElement("span");
    span.textContent = val;

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "×";
    removeBtn.className   = "igm-attr-remove";
    removeBtn.addEventListener("click", () => onRemoveIdx(idx));

    item.appendChild(span);
    item.appendChild(removeBtn);
    listEl.appendChild(item);
  });
}
