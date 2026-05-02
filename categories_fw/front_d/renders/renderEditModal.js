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
        : `<span class="igm-attr-item-type igm-attr-item-dyn">categoría</span>`);

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

export function renderVariantImpls(container, model) {
  if (!container) return;
  container.innerHTML = "";
  const impls = model?.attribute_implementations ?? [];
  if (impls.length === 0) {
    container.textContent = "Esta variante no tiene implementaciones.";
    return;
  }
  impls.forEach(impl => {
    const row = document.createElement("div");
    row.className   = "igm-attr-item";
    row.textContent = `${impl.attribute?.key ?? "?"}: ${impl.value}`;
    container.appendChild(row);
  });
}
