# Renders

Carpeta: `renders/`

Cuatro módulos de construcción DOM. Ninguno importa `handler`, `gestor` ni `attrStore` — reciben datos y callbacks, no tocan estado. Toda la lógica de negocio queda en `events.js`.

---

## Contrato general

```
render*(container, datos, callback(s))
         ↑           ↑         ↑
         DOM         estado    "qué hacer cuando el usuario actúa"
         (del caller) (del caller) (lógica en events.js)
```

---

## `renderBoard.js`

Construye el DOM completo de una carta del organigrama. Exportado y usado por `Organigram.render()`.

### `renderChart(cellEl, chart, board, has)`

Único export público. Crea dentro de `cellEl`:

```html
<div class="igm-box igm-box-{type}" data-id="{id}" draggable>
  <div class="igm-box-header" style="background-color:{color}">
    <span class="igm-type-badge">Categoría | Producto | Variante</span>
    <button class="igm-btn igm-btn-collapse">▲ / ▼</button>
    <button class="igm-btn igm-btn-del" data-id="{id}">×</button>
  </div>
  <div class="igm-box-title">{label}</div>
  <div class="igm-box-body">
    <!-- renderBody según chartType -->
  </div>
</div>

<!-- conectores según flags -->
<div class="igm-edge igm-edge-up/down/left/right"></div>

<!-- botones + si no hay edge -->
<button class="igm-add-btn igm-add-down/right" data-id="{id}">+</button>
```

### Contenido del body por tipo

| `chartType` | Qué renderiza |
|---|---|
| `category` | Pills por atributo: `key: nombre`. Color azul (`igm-pill-static`) o rosa (`igm-pill-dynamic`) según `is_static` |
| `product` | Filas `cod`, `marca`, `precio` con clases `igm-field-row` |
| `variant` | Pills de implementaciones `key: valor` con clase `igm-pill-impl` |

### Eventos emitidos

Los botones del render disparan eventos sobre `board` (el `#igm-board`):

| Botón | Evento | Detail |
|---|---|---|
| `igm-btn-collapse` | `igm-collapse` | — |
| `igm-add-btn` | `igm-add-chart` | `{ fromId, dir }` |

El botón `igm-btn-del` **no** emite evento: `events.js` lo captura por delegación con `.closest(".igm-btn-del")`.

### Funciones internas (no exportadas)

- `renderBody(chart)` — construye el `div.igm-body-content` según `chartType`
- `addEdge(parent, dir)` — agrega `div.igm-edge-{dir}`
- `addBtn(cellEl, dir, chart, board)` — agrega `button.igm-add-btn`
- `emptySpan(text)` — `span.igm-body-empty` para estados vacíos

---

## `renderEditModal.js`

Renders para el modal de edición de nodos (doble click sobre una carta).

### `renderAttrList(container, attrs, onRemove)`

Vacía `container` y renderiza la lista de atributos pendientes de una categoría.

```js
renderAttrList(attrListEl, pendingAttrs, (attr, idx) => {
  // callback en events.js:
  // gestor.analyzeRemoveAttribute(...) → showGestorDialog o splice directo
});
```

Cada ítem:
```html
<div class="igm-attr-item">
  <div class="igm-attr-item-info">
    <span class="igm-attr-item-key">{key}</span>
    <span class="igm-attr-item-meta">{name}</span>
    <span class="igm-attr-item-type">{data_type}</span>
    <span class="igm-attr-item-type igm-attr-item-static|igm-attr-item-dyn">
      producto | variante
    </span>
  </div>
  <button class="igm-attr-remove">×</button>
</div>
```

Si `attrs` está vacío → `span.igm-body-empty` con "Sin atributos".

### `renderVariantImpls(container, model)`

Renderiza las implementaciones de una variante en el modal de edición.

```js
renderVariantImpls(document.getElementById("igm-var-impls"), chart.model);
```

Sin callbacks — es solo lectura. Muestra `{attribute.key}: {value}` por cada impl, o texto de estado vacío.

---

## `renderAttrsModal.js`

Renders para el modal CRUD global de atributos (botón "Atributos" en el navbar).

### `renderAttrRows(listEl, attrs, onRemove)`

Lista completa de atributos del `attrStore`.

```js
renderAttrRows(
  document.getElementById("igm-attrs-list"),
  attrStore.attrs,
  (attr) => {
    // callback en events.js:
    // confirm → attrStore.remove → re-render
  },
);
```

Cada fila es un `.igm-attr-row` con key, nombre, tipo, badge producto/variante, hint de opciones enum, y botón ×.

Si `attrs` está vacío → `p.igm-body-empty` con instrucción.

### `renderEnumValues(listEl, values, onRemoveIdx)`

Lista de opciones de un enum durante la creación de un atributo.

```js
renderEnumValues(
  document.getElementById("igm-na-enum-list"),
  currentEnumValues,
  (idx) => { currentEnumValues.splice(idx, 1); refreshEnumValues(); },
);
```

Cada opción es un `.igm-enum-item` con el valor y un botón ×. La lista se re-renderiza completa en cada cambio.

---

## `renderAttrPicker.js`

Render del modal picker de atributos (botón "+ Agregar atributos" dentro del modal de categoría).

### `renderPicker(pickerSelection, allAttrs, containers, { onRemove, onAdd })`

Llena las cuatro listas del picker en una sola llamada.

```js
renderPicker(
  pickerSelection,       // array: atributos actualmente seleccionados (copia local)
  attrStore.attrs,       // array: todos los atributos globales
  {
    haveStatic:  document.getElementById("igm-picker-have-static"),
    haveDynamic: document.getElementById("igm-picker-have-dynamic"),
    allStatic:   document.getElementById("igm-picker-all-static"),
    allDynamic:  document.getElementById("igm-picker-all-dynamic"),
  },
  {
    onRemove: (attr) => { pickerSelection = pickerSelection.filter(...); renderPicker(); },
    onAdd:    (attr) => { pickerSelection.push({...attr}); renderPicker(); },
  },
);
```

### Distribución de las cuatro listas

| Lista | ID | Contenido |
|---|---|---|
| `haveStatic` | `#igm-picker-have-static` | Seleccionados con `is_static = true` |
| `haveDynamic` | `#igm-picker-have-dynamic` | Seleccionados con `is_static = false` |
| `allStatic` | `#igm-picker-all-static` | Todos los del store con `is_static = true` |
| `allDynamic` | `#igm-picker-all-dynamic` | Todos los del store con `is_static = false` |

### Comportamiento por lado

| Lado | Si no está seleccionado | Si está seleccionado |
|---|---|---|
| `"have"` (izquierda) | — (no aparece) | Ítem con botón × → llama `onRemove` |
| `"all"` (derecha) | Ítem con botón `+` → llama `onAdd` | Ítem con badge `✓` + clase `igm-picker-item-added` |

La lógica de diff (added/removed) y el análisis de impacto con Gestor ocurren en `events.js` al hacer click en Confirmar, no dentro de este render.

---

## Cómo agregar un render nuevo

1. Crear `renders/renderMiCosa.js` con funciones exportadas que reciben `(container, datos, callbacks)`.
2. Importarlo en el archivo que lo usa: `import { renderMiCosa } from "./renders/renderMiCosa.js"`.
3. Nunca importar `handler`, `gestor` ni stores dentro de `renders/`.
