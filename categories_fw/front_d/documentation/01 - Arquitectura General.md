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
├── organigram.js    ← Organigram: árbol → matriz + matriz → DOM
├── Handler.js       ← CRUD + serialización
├── ui.js            ← modal + showMenu
└── events.js        ← entry point, wiring de todo
```

---

## Separación de responsabilidades

| Capa | Archivo | Responsabilidad |
|---|---|---|
| **Dominio** | `models.js` | Category, Product, Variant, Attribute con validaciones |
| **Nodo visual** | `charts.js` | Chart: nodo del árbol visual con tipo, modelo y flags |
| **Árbol** | `Handler.js` | CRUD sobre el árbol, serialización JSON |
| **Layout** | `organigram.js` (primera mitad) | Árbol → Matriz 2D |
| **Render** | `organigram.js` (segunda mitad) | Matriz 2D → DOM |
| **Eventos** | `events.js` | Conectar UI con Handler |
| **UI** | `ui.js` | Modal, menús flotantes |
| **Estilo** | `styles.css` | Visual completo, dark mode |

---

## Flujo de vida de un render

```
Usuario interactúa
       ↓
events.js captura el evento
       ↓
layoutActors[organigram].acción()
       ↓
Handler modifica el árbol de Charts
       ↓
handler.treeToMax()
  → organigram.toMatrix(root)   árbol → matriz 2D
       ↓
handler.render({ container })
  → organigram.render()         matriz → DOM
       ↓
CSS Grid dibuja
       ↓
auto-save en localStorage
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
initUI();                          // crea modal, inyecta nada (CSS ya está en styles.css)

const handler = new Handler();

// wrap render para auto-save
handler.render = (opts) => {
  _render(opts);
  localStorage.setItem("igm-catalog", handler.toJson());
};

// restaurar estado guardado
const saved = localStorage.getItem("igm-catalog");
if (saved) handler.fromJson(saved);

handler.treeToMax();
handler.render({ container: "#igm-board" });
```

---

## HTML requerido

```html
<div id="igm-board-container">   <!-- contenedor scrolleable -->
  <div id="igm-board"></div>     <!-- grid del organigrama -->
</div>

<!-- botones opcionales del navbar -->
<button id="igm-add-root">+ Agregar</button>
<button data-igm="zoom-out">−</button>
<button data-igm="zoom-fit">fit</button>
<button data-igm="zoom-in">+</button>

<script type="module" src="./events.js"></script>
```
