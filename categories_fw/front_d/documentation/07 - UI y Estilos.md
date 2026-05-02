# UI y Estilos

Archivos: `ui.js`, `styles.css`

---

## `ui.js`

Tres responsabilidades: crear los modales, crear el dialog del Gestor y exponer `showMenu` + `showGestorDialog`.

### `initUI()`

Llamada al inicio de `events.js`. Crea los cuatro overlays e inyecta todos en `document.body`. No toca estilos (el CSS está en `styles.css`).

| Función de creación | Overlay generado | Propósito |
|---|---|---|
| `createGestorModal()` | `#igm-gestor-overlay` | Dialog de análisis de impacto |
| `createModal()` | `#igm-modal-overlay` | Modal de edición de nodos (doble click) |
| `createAttrsModal()` | `#igm-attrs-modal-overlay` | CRUD global de atributos (botón "Atributos") |
| `createAttrPickerModal()` | `#igm-picker-overlay` | Picker de atributos del store para categorías |

### `createModal()` (privada)

Crea dinámicamente el overlay + modal de edición con tres secciones internas:

```
#igm-modal-overlay
  #igm-modal
    #igm-modal-title          ← h3 con color dinámico según tipo
    #igm-sec-category         ← sección Category (oculta por default)
    #igm-sec-product          ← sección Product  (oculta por default)
    #igm-sec-variant          ← sección Variant  (oculta por default)
    .igm-modal-actions
      #igm-modal-cancel
      #igm-modal-save
```

Las secciones se muestran agregando/quitando la clase `.igm-active`.

### `createGestorModal()` (privada)

Crea el overlay del dialog del Gestor:

```
#igm-gestor-overlay
  #igm-gestor-modal
    #igm-gestor-title          ← título de la operación
    #igm-gestor-desc           ← descripción del impacto
    #igm-gestor-deletions      ← lista roja de cosas que se eliminarán (oculta si vacía)
    #igm-gestor-inputs         ← campos para implementar atributos (ocultos si vacíos)
    .igm-modal-actions
      #igm-gestor-cancel
      #igm-gestor-confirm      ← label dinámico según la operación
```

### `showGestorDialog({ title, description, inputs, deletions, confirmLabel, onConfirm, onCancel })`

Muestra el dialog del Gestor con el contenido apropiado según el flujo:

```js
showGestorDialog({
  title:        "Implementar atributos",
  description:  "Este producto hereda atributos estáticos:",
  inputs:       [{ attr, label, dataType, options, hint, productId }],
  deletions:    [{ label }],
  confirmLabel: "Crear producto",
  onConfirm:    (filledValues) => { /* filledValues = [{ ...inputSpec, value }] */ },
  onCancel:     () => {},
});
```

- Renderiza un `<input>` o `<select>` por cada ítem de `inputs` según `dataType`.
- La sección de `deletions` usa fondo rojo tenue para destacar lo que se pierde.
- Los botones se clonan en cada apertura para limpiar listeners viejos.
- Un flag interno `handled` evita que `onConfirm`/`onCancel` se llamen más de una vez.

### `showMenu(anchorEl, opciones, onSelect)`

Menú flotante posicionado debajo de `anchorEl`.

```js
showMenu(btn, [
  { value: "category", label: "Categoría" },
  { value: "product",  label: "Producto"  },
  { value: "variant",  label: "Variante"  },
], (value) => { /* ... */ });
```

- Elimina cualquier menú flotante anterior antes de crear uno nuevo.
- Se posiciona con `position: fixed` calculando `rect.left` y `rect.bottom + 6`.
- Se cierra al hacer click fuera (listener en `document`).

---

## `styles.css`

Dark mode nativo — no hay toggle ni media query.

### Variables CSS

```css
:root {
  --igm-cell-w:     210px;    /* ancho de cada celda del grid */
  --igm-edge-color: #3f3f46;  /* color de los conectores */
  --igm-edge-size:  2px;      /* grosor de los conectores */
  --igm-pad-top:    20px;     /* espacio sobre la carta (edge up) */
  --igm-pad-bottom: 20px;     /* espacio bajo la carta (edge down) */

  --bg-base:        #0e0e10;
  --bg-surface:     #18181b;  /* navbar, boxes, modal */
  --bg-elevated:    #27272a;  /* inputs, attr items */
  --bg-hover:       #3f3f46;  /* hover states */
  --border:         #3f3f46;
  --text-primary:   #f4f4f5;
  --text-secondary: #a1a1aa;
  --text-muted:     #71717a;
  --accent:         #3b82f6;
  --accent-hover:   #2563eb;
}
```

### Estructura visual de las cartas

```
.igm-cell                    posición relativa, padding top/bottom = 20px
  .igm-box                   carta: fondo surface, borde, sombra, draggable
    .igm-box-header          fondo coloreado por tipo (naranja/azul/violeta)
      .igm-type-badge        "CATEGORÍA" / "PRODUCTO" / "VARIANTE"
      .igm-btn-collapse      ▲ / ▼
      .igm-btn-del           ×
    .igm-box-title           nombre/título
    .igm-box-body            contenido según tipo
  .igm-edge-up/down/left/right   conectores absolutos
  .igm-add-btn.igm-add-down      botón + abajo
  .igm-add-btn.igm-add-right     botón + derecha
```

### Conectores (edges)

Los edges son `position: absolute` dentro de `.igm-cell`. El `padding-top: 20px` y `padding-bottom: 20px` de la celda crean el espacio donde viven los edges verticales:

```
top:0 ─── edge-up (20px) ─── [carta] ─── edge-down (20px) ─── bottom:0
```

Los edges horizontales (`left`/`right`) viven en `top:0` y se usan para el T-bar:

```
left:0 ──── edge-left (50%) ──── centro ──── edge-right (50%) ──── right:0
```

### Pills de atributos

| Clase | Color de fondo | Color de texto | Uso |
|---|---|---|---|
| `.igm-pill-static` | `#1e3a5f` | `#93c5fd` | Atributo estático (de producto) |
| `.igm-pill-dynamic` | `#4a1942` | `#f0abfc` | Atributo dinámico (de variante) |
| `.igm-pill-impl` | `#2e1d5e` | `#c4b5fd` | Implementación en variante |

### Colores de tipo de carta

| Tipo | Color header |
|---|---|
| Categoría | `#f97316` (naranja) |
| Producto | `#3b82f6` (azul) |
| Variante | `#8b5cf6` (violeta) |

### Fondo del canvas

Puntitos con `radial-gradient` sobre `#0e0e10`:

```css
background-image: radial-gradient(circle, #2e2e32 1px, transparent 1px);
background-size:  28px 28px;
background-color: var(--bg-base);
```

### Canvas virtual

`.igm-board` tiene `padding: 2000px` para permitir panear libremente. Al iniciar, el scroll se posiciona en `2000px - 80px` en ambos ejes para quedar cerca del contenido.

### Drag & drop visual

```css
.igm-box.drop-child   { outline: 2px solid var(--accent); ... }
.igm-box.drop-sibling { border-right: 3px solid var(--accent); }
```

### Modal dark

```css
.igm-modal {
  background: var(--bg-surface);   /* #18181b */
  border:     1px solid var(--border);
}
.igm-modal input, .igm-modal select, .igm-modal textarea {
  background: var(--bg-elevated);  /* #27272a */
  color:      var(--text-primary);
  border:     1px solid var(--border);
}
```
