# Organigrama

Archivo: `organigram.js`

Responsable exclusivamente de convertir el árbol de `Chart` en una **matriz 2D** (layout). La construcción DOM de cada carta fue extraída a `renders/renderBoard.js`.

---

## Marcadores de celda — `btandvoid.js`

| Clase | Qué representa |
|---|---|
| `Void` | Celda vacía, no se renderiza |
| `WireTop` | Cable horizontal en `top:0` para conectar hermanos no adyacentes |

---

## Clase `Organigram`

```js
new Organigram(root)
// this.nodoRaiz = root
// this.matiz    = []   ← matriz 2D: matiz[row][col]
```

---

## Algoritmo `toMatrix` — árbol → matriz 2D

Dos pasos: cálculo de anchos bottom-up → colocación top-down.

### Paso 1: `calcWidth` (bottom-up)

```js
hoja     → width = 1
interno  → width = suma de widths de hijos
```

```
     A             w(D)=1, w(E)=1
    / \             w(B)=2, w(C)=1
   B   C             w(A)=3
  / \
 D   E
```

### Paso 2: `place` (top-down)

```js
nodeCol = startCol + Math.floor((w - 1) / 2)
nodeRow = depth
```

**Fórmula clave**: `nodeCol = startCol + floor((w-1)/2)`

| Ancho | floor((w-1)/2) | Comportamiento |
|---|---|---|
| 1 | 0 | col = startCol |
| 2 | 0 | col = startCol (left-biased) |
| 3 | 1 | col = startCol + 1 (centrado) |
| 4 | 1 | col = startCol + 1 (left-biased) |

### Orden de operaciones crítico

```js
// 1. Colocar el nodo en la matriz
this.setAt(depth, nodeCol, node);

// 2. Llamar place() recursivamente en todos los hijos
for (const hijo of hijos) { place(hijo, cs, depth + 1); ... }

// 3. Asignar flags left/right DESPUÉS de la recursión
hijos[0].right = 1;
hijos[last].left = 1;
hijos[middle].left = hijos[middle].right = 1;
```

> Los flags `left`/`right` se asignan **después** de la recursión porque `place()` resetea `node.left = 0` y `node.right = 0` al inicio.

### WireTop — gaps entre hermanos no adyacentes

Cuando los subárboles de los hijos tienen ancho > 1, sus columnas centrales no son contiguas. Las columnas intermedias reciben un `WireTop`:

```js
for (let c = leftChildCol; c <= rightChildCol; c++) {
  if (!childCols.includes(c)) this.setAt(childRow, c, new WireTop());
}
```

### Ejemplo

```
Árbol:         Matriz (fila 0):          Matriz (fila 1):
    A          col:  0    1    2          [B ] [WT] [C ]
   / \               [ ] [ ] [A]
  B   C         Matriz (fila 2):
 / \   \         [D ] [E ] [F ]
D   E   F
```

---

## Flags de conexión

| Flag | Condición | Qué dibuja |
|---|---|---|
| `up = 1` | Cualquier nodo de depth > 0 | Línea vertical `top:0` → comienzo de la carta |
| `down = 1` | Nodo con hijos | Línea vertical desde la carta → `bottom:0` |
| `right = 1` | Primer hijo + hijos medios | Barra horizontal en `top:0` → derecha |
| `left = 1` | Último hijo + hijos medios | Barra horizontal en `top:0` → izquierda |

### Visualización T-bar

```
        [Padre]
           |          ← edge.down del padre
  ─────────┼─────     ← top:0 de la fila hijo
  |                |
[B]              [C]
↑                 ↑
right=1          left=1
```

- `edge.right` en B → línea desde el centro de B hacia la derecha
- `edge.left` en C → línea desde el centro de C hacia la izquierda
- `WireTop` en columnas intermedias → completa la barra horizontal
- `edge.up` de cada hijo → conecta la barra al comienzo de la carta

---

## Render `organigram.render()` — matriz → DOM

Para cada celda `(row, col)` de la matriz delega en `renders/renderBoard.js`:

```js
import { renderChart } from "./renders/renderBoard.js";

// en render():
if (cell instanceof Chart)   → renderChart(cellEl, cell, boardEl, has)
if (cell instanceof WireTop) → <div class="igm-wire-top">
if (cell instanceof Void)    → celda vacía (nada)
```

Ver [Renders](10%20-%20Renders.md#renderboardjs) para la estructura DOM completa que produce `renderChart`.

---

## Diferencias con Diagramer

| Aspecto | Diagramer | front_d |
|---|---|---|
| Nodo del árbol | `Carta` | `Chart` con `chartType` + `model` |
| Render separado | `renderOrganigram.js` | `renders/renderBoard.js` |
| Contenido de la carta | `TipoDescripcion`, `TipoVideo`… | Renderizado según `chartType` |
| Colores | Libres por nodo | Fijo por tipo (naranja/azul/violeta) |
| Color picker / shape picker | Sí | No (MVP) |
