# Sistema de Eventos

Archivo: `events.js`

Entry point de toda la lógica interactiva. Conecta la UI con `Gestor` y `Handler` siguiendo el patrón **layout actors** de Diagramer. El Gestor actúa como capa intermedia: todas las operaciones que modifican el árbol pasan por él antes de llegar al Handler.

---

## Layout Actors

```js
const layoutActors = {
  organigram: { add, addRoot, deleteNode, moveToChild, moveToSibling }
}
const currentLayout = "organigram"
```

Solo existe el modo `organigram`. La estructura de actors está preparada para agregar futuros modos sin tocar el resto del código.

### Métodos de cada actor

#### `add(base, dir, chartType, model)`

- `dir = "down"` → agrega como hijo de `base`
- `dir = "right"` → agrega como hermano (hijo del padre de `base`). Rechaza si `base` es el root.

Siempre termina con `treeToMax()` + `render()`.

#### `addRoot(chartType, model)`

Agrega un hijo directo al nodo root (`id: 0`).

#### `deleteNode(id)`

Llama `handler.deleteByIdAndRefresh(id)`.

#### `moveToChild(fromId, toId)`

Llama `handler.moveNode(fromId, toId)` + refresh.

#### `moveToSibling(fromId, afterId)`

Llama `handler.moveNodeAfter(fromId, afterId)` + refresh.

---

## Crear modelo por tipo — `createModel(chartType)`

Prompt nativo por tipo:

| Tipo | Prompts | Nota |
|---|---|---|
| `category` | nombre | — |
| `product` | título, código SKU, precio, marca | `attributes_implementations: []` incluido en el modelo para que el Gestor pueda rellenarlo |
| `variant` | ninguno | Las implementaciones se rellenan vía dialog del Gestor si hay atributos dinámicos |

Retorna `null` si el usuario cancela o deja el campo obligatorio vacío.

---

## Eventos del board

### `igm-add-chart`

Disparado por los botones `+` del render. Flujo completo:

```
1. gestor.checkAdd(parentId, chartType)   → blocked? alert y cortar
2. createModel(chartType)                 → prompts básicos
3. gestor.analyzeAddProduct/Variant()     → atributos faltantes?
4. showGestorDialog (si flow !== "none")  → usuario completa implementaciones
5. layoutActors.organigram.add(...)       → Handler + render
```

### `igm-collapse`

Guardado en localStorage sin re-renderizar.

### Click en `.igm-btn-del`

```
1. gestor.analyzeDelete(id)
2a. Si solo 1 nodo → confirm() simple
2b. Si hay cascade  → showGestorDialog con lista de deletions
3. layoutActors.organigram.deleteNode(id)
```

### Doble click en `.igm-box`

Abre el modal de edición del nodo.

### `#igm-add-root`

Muestra el menú de tipos, aplica `gestor.checkAdd(0, chartType)` y llama a `addRoot`.

---

## Modal de edición

El modal tiene tres **secciones** que se muestran/ocultan según el `chartType` del nodo editado:

### Sección Category

| Campo | ID | Descripción |
|---|---|---|
| Nombre | `#igm-cat-name` | Nombre de la categoría |
| Lista de atributos | `#igm-attr-list` | Muestra los atributos con botón × para quitar |
| Key | `#igm-attr-key` | Key del nuevo atributo |
| Nombre | `#igm-attr-name-inp` | Nombre visible del nuevo atributo |
| Tipo | `#igm-attr-dtype` | `text / number / boolean / enum` |
| Estático | `#igm-attr-static` | Si es de producto o de variante |
| Botón agregar | `#igm-attr-add-btn` | Analiza impacto con Gestor y agrega a `pendingAttrs` |

**Flujo del botón × (quitar atributo)**:
```
gestor.analyzeRemoveAttribute(editingChart.id, attr)
  → flow "destructive"  → showGestorDialog con lista de productos afectados
  → flow "none"         → quitar directamente de pendingAttrs
```

**Flujo del botón "Agregar atributo"**:
```
gestor.analyzeAddAttribute(editingChart.id, newAttr)
  → flow "additive"     → showGestorDialog con un input por cada producto afectado
                          onConfirm aplica implementaciones en model de cada producto
  → flow "none"         → agregar directamente a pendingAttrs
```

Los cambios se acumulan en `pendingAttrs[]` y solo se aplican al `chart.model` al hacer click en **Guardar**.

### Sección Product

| Campo | ID |
|---|---|
| Título | `#igm-prod-title` |
| Código SKU | `#igm-prod-code` |
| Precio | `#igm-prod-price` |
| Marca | `#igm-prod-brand` |
| Descripción | `#igm-prod-desc` |

### Sección Variant

Solo muestra las implementaciones actuales. La edición completa de implementaciones queda para una iteración futura.

---

## Drag & Drop

```js
let dragId   = null   // id del chart arrastrado
let dropZone = null   // "child" | "sibling"
const SIBLING_THRESHOLD = 0.65  // zona derecha del 35% = hermano
```

### Flujo

```
dragstart en .igm-box  → guarda dragId
dragover  en .igm-box  → calcula relX
  relX > 0.65          → drop-sibling highlight
  relX ≤ 0.65          → drop-child highlight
drop                   → gestor.analyzeMove(fromId, toId, mode)
                           → blocked?        alert(reason)
                           → flow !== "none" → showGestorDialog → moveToSibling | moveToChild
                           → flow "none"     → moveToSibling | moveToChild directamente
dragend                → limpia estado
```

### Highlights visuales

- `.drop-child`: outline azul + box-shadow
- `.drop-sibling`: borde derecho azul

---

## Zoom

```js
let zoomLevel = 1.0
const ZOOM_STEP = 0.1
const ZOOM_MIN  = 0.2
const ZOOM_MAX  = 3.0
```

### `applyZoom(z)`

Clampea entre `ZOOM_MIN` y `ZOOM_MAX`, aplica `board.style.zoom = zoomLevel`.

Usa la propiedad CSS `zoom` (no `transform: scale`) porque ajusta los scrollbars del contenedor automáticamente.

### `fitToScreen()`

Calcula el zoom para que todo el diagrama quepa en el viewport (máximo `1.0`, no hace zoom-in).

### Controles

| Selector | Acción |
|---|---|
| `[data-igm="zoom-in"]` | `applyZoom(+0.1)` |
| `[data-igm="zoom-out"]` | `applyZoom(-0.1)` |
| `[data-igm="zoom-fit"]` | `fitToScreen()` |
| `Ctrl + rueda del mouse` | Zoom centrado en el cursor |

---

## Pan con botón central del mouse

Al mantener presionado el botón del medio (`button === 1`) sobre el contenedor, se puede arrastrar el canvas en cualquier dirección. El cursor cambia a `grabbing` mientras está activo.

---

## Canvas virtual

`#igm-board` tiene `padding: 2000px` (definido en `.igm-board` de `styles.css`). Al iniciar, el scroll se posiciona en el origen del contenido compensando ese padding:

```js
boardContainer.scrollLeft = 2000 - 80;
boardContainer.scrollTop  = 2000 - 80;
```

---

## Persistencia

La gestión de localStorage está delegada a los stores en `stores/`:

```js
// auto-save en cada render
handler.render = (opts) => { _render(opts); catalogStore.save(handler); };

// al iniciar
catalogStore.load(handler);  // árbol del catálogo
attrStore.load();            // atributos globales
```

Ver [Stores](09%20-%20Stores.md) para la API completa de cada store.
