# Handler

Archivo: `Handler.js`

Gestiona el árbol de `Chart`: CRUD, movimientos, serialización. Es la única capa que modifica el árbol directamente.

---

## Constructor

```js
const handler = new Handler()
// handler.root   = Chart({ id: 0, chartType: "root", model: null })
// handler.lastId = 0
// handler.layout = new Organigram(root)
```

El nodo raíz (`id: 0`) es virtual: no se renderiza y no puede eliminarse.

---

## API

### Búsqueda

```js
Handler.findNode(node, id)  // → Chart | null   (estático, DFS)
```

Busca en profundidad desde `node`. Se usa en todo el sistema para obtener un nodo a partir de su `id`.

---

### CRUD

#### `addNodeTo(parentId, chartType, model)` → `Chart | null`

Crea un nuevo `Chart` y lo agrega como hijo de `parentId`.

```js
handler.addNodeTo(0, "category", { name: "Ropa", attributes: [] })
handler.addNodeTo(1, "product",  { title: "Remera", code: "REM-01", price: 1200, brand: "X" })
```

- Incrementa `lastId` y lo asigna al nuevo chart.
- Retorna `null` si `parentId` no existe.

---

#### `deleteById(id)` → `bool`

Elimina el nodo y **todos sus hijos** (al quitarlo del padre se pierde la referencia al subárbol completo).

- Rechaza `id === 0` (no se puede eliminar el root).
- Actualiza `parent.down` después de eliminar.

#### `deleteByIdAndRefresh(id)` → `bool`

`deleteById` + `treeToMax()` + `render()`. Usado directamente desde `events.js`.

---

### Movimientos

#### `moveNode(fromId, toId)` → `bool`

Mueve `fromId` para que sea hijo de `toId`.

Validaciones:
- `fromId !== toId`
- `fromId` no es el root (`idParent !== null`)
- `toId` no es un descendiente de `fromId` (evita ciclo)

#### `moveNodeAfter(fromId, afterId)` → `bool`

Mueve `fromId` para quedar justo **después de** `afterId` entre los hijos del padre de `afterId` (movimiento de hermano).

Validaciones iguales a `moveNode` más: `afterId` no puede ser el root.

---

### Layout y render

```js
handler.treeToMax()                         // árbol → matriz
handler.render({ container: "#igm-board" }) // matriz → DOM
```

Siempre llamar `treeToMax()` antes de `render()` cuando el árbol cambia.

En `events.js`, `render` está **wrapeado** para auto-save:

```js
const _render = handler.render.bind(handler);
handler.render = (opts) => {
  _render(opts);
  localStorage.setItem("igm-catalog", handler.toJson());
};
```

---

### Serialización

#### `toJson()` → `string`

Serializa el árbol completo a JSON. El modelo se serializa según `chartType`:

```json
{
  "lastId": 5,
  "root": {
    "id": 0,
    "idParent": null,
    "chartType": "root",
    "model": null,
    "collapsed": false,
    "listaHijos": [
      {
        "id": 1,
        "chartType": "category",
        "model": { "name": "Ropa", "id": null, "attributes": [] },
        "listaHijos": [...]
      }
    ]
  }
}
```

#### `fromJson(json)` → `void`

Reconstruye el árbol desde el JSON. Los modelos se deserializan como **objetos planos** (no instancias de `Category`, `Product`, etc.). Suficiente para el render visual; la integración con el dominio completo queda pendiente.

#### `reset()` → `void`

Resetea el árbol al estado inicial (solo el nodo raíz vacío).

---

## Serialización de modelos — funciones privadas

```js
serModel(chartType, model)   // model → objeto plano JSON-safe
deserModel(chartType, data)  // objeto plano → modelo para el render
```

| chartType | Campos serializados |
|---|---|
| `"category"` | `name`, `id`, `attributes[]` (cada attr serializado con `to_json()`) |
| `"product"` | `code`, `title`, `price`, `description`, `brand`, `id` |
| `"variant"` | `id`, `attribute_implementations[]` |

---

## Limitación actual (MVP)

`fromJson` reconstruye modelos como objetos planos, no como instancias de `Category`/`Product`/`Variant`. Esto significa que los métodos del dominio (`get_full_attr_set`, `impact_on_*`, etc.) no están disponibles en los modelos restaurados desde localStorage.

Para integrar con el dominio completo, `deserModel` deberá instanciar las clases correctas y resolver las referencias cruzadas (ej: `Product.category` apunta a la instancia `Category` del nodo padre).
