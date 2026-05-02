// Render para el modal picker de atributos (agregar/quitar desde una categoría).
// pickerSelection: array de attrs actualmente seleccionados (copia local del estado).
// allAttrs: array completo del attrStore.
// containers: { haveStatic, haveDynamic, allStatic, allDynamic } — elementos DOM.
// callbacks: { onRemove(attr), onAdd(attr) } — notifican cambios al estado en events.js.

export function renderPicker(pickerSelection, allAttrs, containers, { onRemove, onAdd }) {
  const { haveStatic, haveDynamic, allStatic, allDynamic } = containers;

  const isSelected = (attr) => pickerSelection.some(a => a.key === attr.key);

  const makeItem = (attr, side) => {
    const item = document.createElement("div");
    item.className = "igm-picker-item";

    const info = document.createElement("div");
    info.className = "igm-picker-item-info";
    info.innerHTML =
      `<span class="igm-attr-item-key">${attr.key}</span>` +
      `<span class="igm-attr-item-meta">${attr.name}</span>` +
      `<span class="igm-attr-item-type">${attr.data_type}</span>` +
      (attr.data_type === "enum" && attr.enum_values?.length > 0
        ? `<span class="igm-attr-enum-hint">${attr.enum_values.length} opc.</span>` : "");

    item.appendChild(info);

    if (side === "have") {
      const removeBtn = document.createElement("button");
      removeBtn.textContent = "×";
      removeBtn.className   = "igm-attr-remove";
      removeBtn.addEventListener("click", () => onRemove(attr));
      item.appendChild(removeBtn);
    } else if (isSelected(attr)) {
      const badge = document.createElement("span");
      badge.textContent = "✓";
      badge.className   = "igm-picker-added-badge";
      item.appendChild(badge);
      item.classList.add("igm-picker-item-added");
    } else {
      const addBtn = document.createElement("button");
      addBtn.textContent = "+";
      addBtn.className   = "igm-picker-add-btn";
      addBtn.addEventListener("click", () => onAdd(attr));
      item.appendChild(addBtn);
    }
    return item;
  };

  const fillList = (el, attrs, side) => {
    el.innerHTML = "";
    if (attrs.length === 0) {
      const span = document.createElement("span");
      span.className   = "igm-body-empty";
      span.textContent = side === "all" ? "Sin atributos globales" : "Sin atributos";
      el.appendChild(span);
      return;
    }
    attrs.forEach(a => el.appendChild(makeItem(a, side)));
  };

  fillList(haveStatic,  pickerSelection.filter(a =>  a.is_static), "have");
  fillList(haveDynamic, pickerSelection.filter(a => !a.is_static), "have");
  fillList(allStatic,   allAttrs.filter(a =>  a.is_static),        "all");
  fillList(allDynamic,  allAttrs.filter(a => !a.is_static),        "all");
}
