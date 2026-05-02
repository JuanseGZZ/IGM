# Arquitectura General

`front_d` es una SPA sin framework. Todo el estado vive en un árbol de objetos `Chart` gestionado por `Handler`. El layout convierte ese árbol en una **matriz 2D** que el renderer convierte en un CSS Grid.

---

## Estructura de archivos

```
front_d/
├── index.html       ← HTML base: navbar + #igm-board-container + #igm-board
├── styles.css       ← estilos dark mode
├── models.js        ← modelos de dominio (Category, Product, Variant, Attribute…)
├── charts.js        ← Chart + CHART_TYPE + CHART_BG + CHART_LABEL
├── btandvoid.js     ← Void, WireTop (marcadores de celda)
├── organigram.js    ← Organigram: árbol → matriz 2D (solo layout)
├── Handler.js       ← CRUD + serialización
├── Gestor.js        ← árbol espejo de dominio, validaciones, análisis de impacto
├── ui.js            ← modal de edición, showMenu, showGestorDialog
├── events.js        ← entry point, wiring de todo
│
├── stores/
│   ├── attrStore.js    ← almacén global de atributos
│   └── catalogStore.js ← persistencia del árbol
│
└── renders/
    ├── renderBoard.js      ← DOM de cartas (extraído de organigram.js)
    ├── renderEditModal.js  ← DOM modal de edición
    ├── renderAttrsModal.js ← DOM modal CRUD de atributos
    └── renderAttrPicker.js ← DOM picker de atributos
```

---

## Separación de responsabilidades

| Capa | Archivo(s) | Responsabilidad |
|---|---|---|
| **Dominio** | `models.js` | Category, Product, Variant, Attribute con validaciones |
| **Nodo visual** | `charts.js` | Chart: nodo del árbol visual con tipo, modelo y flags |
| **Árbol** | `Handler.js` | CRUD sobre el árbol, serialización JSON |
| **Reglas de negocio** | `Gestor.js` | Árbol espejo, validaciones estructurales, análisis de impacto |
| **Layout** | `organigram.js` | Árbol → Matriz 2D |
| **Render DOM** | `renders/` | Matriz/datos → DOM (sin lógica de negocio) |
| **Persistencia** | `stores/` | Lectura/escritura en localStorage |
| **Eventos** | `events.js` | Conectar UI con Gestor + Handler; provee callbacks a los renders |
| **UI** | `ui.js` | Esqueletos de modales, menús flotantes, dialog del Gestor |
| **Estilo** | `styles.css` | Visual completo, dark mode |

---

## Principio de separación renders / lógica

Las funciones en `renders/` construyen DOM y reciben **callbacks** para cualquier acción que implique estado o negocio. Nunca importan `handler`, `gestor` ni `attrStore` directamente. Toda la lógica queda en `events.js`.

```
events.js                        renders/renderEditModal.js
──────────                       ──────────────────────────
renderAttrList(container,        ← export function renderAttrList(
  pendingAttrs,                       container, attrs, onRemove)
  (attr, idx) => {                {
    // lógica Gestor aquí          // solo construye DOM
    gestor.analyze...             }
    pendingAttrs.splice(...)
    refreshAttrList()
  }
)
```

---

## Flujo de vida de una operación (con Gestor)

```
Usuario interactúa
       ↓
events.js captura el evento
       ↓
gestor.checkAdd() / gestor.analyze*()
  ↓ blocked          ↓ flow !== "none"       ↓ flow === "none"
alert(reason)    showGestorDialog()      ──────────────────────────┐
                   ↓ onConfirm                                     │
                 (aplica implementaciones si additive)             │
                        ↓                                          │
              layoutActors[organigram].acción()  ←─────────────────┘
                        ↓
               Handler modifica el árbol de Charts
                        ↓
               handler.treeToMax()
                 → organigram.toMatrix(root)   árbol → matriz 2D
                        ↓
               handler.render({ container })
                 → organigram.render()
                 → renderChart() (renders/renderBoard.js)   matriz → DOM
                        ↓
               CSS Grid dibuja
                        ↓
               catalogStore.save(handler)   auto-save
```

---

## Flujo de vida de un render (sin cambios de estado)

```
handler.treeToMax()  →  organigram.toMatrix(root)  →  matriz 2D
handler.render()     →  organigram.render()
                     →  renderChart() por cada Chart  →  DOM
```

---

## Árbol de Charts

El árbol tiene un **nodo raíz virtual** (`id: 0, chartType: "root"`) que no se renderiza. Sus hijos directos son los nodos visibles en el canvas.

```
root (id:0, virtual)
├── Chart (category)   "Indumentaria"
│   ├── Chart (category)   "Remeras"
│   │   ├── Chart (product)  "Remera Básica"
│   │   │   ├── Chart (variant) Variante #4
│   │   │   └── Chart (variant) Variante #5
│   │   └── Chart (product)  "Remera Premium"
│   └── Chart (category)   "Pantalones"
└── Chart (category)   "Calzado"
```

---

## Inicialización (`events.js`)

```js
initUI();        // crea los 4 overlays de modales
attrStore.load();  // carga atributos globales de localStorage

const handler = new Handler();
const gestor  = new Gestor(handler);

// wrap render para auto-save
handler.render = (opts) => {
  _render(opts);
  catalogStore.save(handler);
};

catalogStore.load(handler);  // restaura árbol de localStorage si existe

handler.treeToMax();
handler.render({ container: "#igm-board" });
```

---

## HTML requerido

```html
<div id="igm-board-container">   <!-- contenedor scrolleable -->
  <div id="igm-board"></div>     <!-- grid del organigrama -->
</div>

<!-- botones del navbar -->
<button id="igm-add-root">+ Agregar</button>
<button id="igm-attrs-btn">Atributos</button>
<button data-igm="zoom-out">−</button>
<button data-igm="zoom-fit">fit</button>
<button data-igm="zoom-in">+</button>

<script type="module" src="./events.js"></script>
```
