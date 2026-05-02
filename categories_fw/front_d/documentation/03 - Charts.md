# Charts

Archivo: `charts.js`

Define el nodo visual del árbol: la clase `Chart` y sus constantes de tipo, color y etiqueta. Es el equivalente de `Carta` en Diagramer, pero con semántica de dominio.

---

## Constantes

### `CHART_TYPE`

```js
CHART_TYPE.CATEGORY  // "category"
CHART_TYPE.PRODUCT   // "product"
CHART_TYPE.VARIANT   // "variant"
```

Hay también el tipo implícito `"root"` que usa el nodo raíz virtual del Handler; nunca se renderiza.

### `CHART_BG`

Color de fondo del header de cada carta.

```js
CHART_BG.category  // "#f97316"  naranja
CHART_BG.product   // "#3b82f6"  azul
CHART_BG.variant   // "#8b5cf6"  violeta
```

### `CHART_LABEL`

Texto visible del badge de tipo.

```js
CHART_LABEL.category  // "Categoría"
CHART_LABEL.product   // "Producto"
CHART_LABEL.variant   // "Variante"
```

---

## Clase `Chart`

```js
new Chart({ id, idParent, chartType, model, collapsed })
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `number` | Identificador único dentro del árbol |
| `idParent` | `number\|null` | `null` solo en el nodo raíz virtual |
| `chartType` | `string` | `"category"`, `"product"`, `"variant"` o `"root"` |
| `model` | `object\|null` | Objeto de dominio asociado (Category, Product, Variant, o plano) |
| `collapsed` | `bool` | Si el body de la carta está colapsado |
| `listaHijos` | `Chart[]` | Hijos directos en el árbol |

### Flags de dibujo de conectores

Asignados por `Organigram.toMatrix()`. No modificar manualmente.

| Flag | Valor | Qué dibuja |
|---|---|---|
| `up` | `0\|1` | Línea vertical desde `top:0` de la celda hasta la carta |
| `down` | `0\|1` | Línea vertical desde la carta hasta `bottom:0` de la celda |
| `left` | `0\|1` | Barra horizontal en `top:0` desde el centro hacia la izquierda |
| `right` | `0\|1` | Barra horizontal en `top:0` desde el centro hacia la derecha |

### `get label()`

Getter que retorna el texto del título según el tipo:

```js
category → model.name
product  → model.title ?? model.code
variant  → "Variante #<id>"
```

### `addChild(child)`

Agrega un hijo y actualiza los flags de conexión:
- Si es el primer hijo → activa `this.down = 1`
- Si ya había hijos → activa `child.left = 1` y `right = 1` en el último hijo anterior
- Si `this` no es el root → activa `child.up = 1`

> Los flags `left`/`right` son **preliminares**. `Organigram.toMatrix()` los sobreescribe correctamente después de calcular la matriz completa.

---

## Relación entre Chart y los modelos de dominio

Cada `Chart` lleva una referencia `model` al objeto de dominio correspondiente:

| `chartType` | `model` esperado |
|---|---|
| `"category"` | `{ name, id, attributes[] }` (Category o plano) |
| `"product"` | `{ code, title, price, brand, description, id }` (Product o plano) |
| `"variant"` | `{ attribute_implementations[], id }` (Variant o plano) |
| `"root"` | `null` |

En el MVP, `model` puede ser tanto una instancia de clase (`Category`, `Product`, `Variant`) como un objeto plano equivalente. El render solo lee propiedades, no llama métodos del dominio.
