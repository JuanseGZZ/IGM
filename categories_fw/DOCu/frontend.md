# Frontend

Dashboard web en Bootstrap 5 + Vanilla JS. No requiere build step ni dependencias npm.

**Acceso:** `http://localhost:8000/front/index.html`

Servido como archivos estáticos por FastAPI desde `front_new/`.

---

## Módulos JS

Los scripts se cargan en este orden en `index.html`:

```html
<script src="animations.js"></script>
<script src="api.js"></script>
<script src="render.js"></script>
<script src="service.js"></script>
<script src="events.js"></script>
```

Cada módulo expone un objeto global (`API`, `State`, `Service`, `Render`, `Events`, `Animations`).

---

### animations.js — `Animations`

Utilidades visuales. No contiene lógica de negocio.

| Método | Descripción |
|---|---|
| `toast(msg, type)` | Muestra una notificación en esquina inferior derecha. `type`: `"success"`, `"danger"`, `"warning"`, `"info"` |
| `spinner(show)` | Muestra/oculta el overlay de carga |
| `fadeIn(el)` | Aplica la clase `fade-in` a un elemento |
| `highlight(el)` | Aplica animación flash amarillo a un elemento (`impact-flash`) |
| `init()` | Inicializa el objeto Toast de Bootstrap |

---

### api.js — `API`

Capa de transporte HTTP. Todos los métodos llaman a `_req()` que:
1. Activa el spinner
2. Hace `fetch` con `Content-Type: application/json`
3. Lanza `Error` si `!res.ok`
4. Desactiva el spinner en el `finally`

```js
API.BASE = 'http://localhost:8000'
```

| Método | HTTP | Path |
|---|---|---|
| `categories()` | GET | `/categories` |
| `attributes()` | GET | `/attributes` |
| `products(catId?)` | GET | `/products[?category_id=...]` |
| `product(id)` | GET | `/products/{id}` |
| `createCategory(body)` | POST | `/categories` |
| `createAttribute(body)` | POST | `/attributes` |
| `updateAttribute(id, body)` | PATCH | `/attributes/{id}` |
| `createProduct(body)` | POST | `/products` |
| `deleteCategory(id)` | DELETE | `/categories/{id}` |
| `deleteAttribute(id)` | DELETE | `/attributes/{id}` |
| `deleteProduct(id)` | DELETE | `/products/{id}` |
| `changeFather(catId, body)` | PATCH | `/categories/{id}/father` |
| `addCatAttribute(catId, attrId, body)` | POST | `/categories/{id}/attributes/{attr_id}` |
| `removeCatAttribute(catId, attrId, body)` | DELETE | `/categories/{id}/attributes/{attr_id}` |
| `changeProductCat(prodId, newCatId, body)` | PATCH | `/products/{id}/category/{new_cat_id}` |
| `addVariant(prodId, body)` | POST | `/products/{id}/variants` |
| `removeVariant(prodId, varId)` | DELETE | `/products/{id}/variants/{var_id}` |

---

### service.js — `State` + `Service`

#### State (estado global)

```js
const State = {
  categories: [],   // lista plana de CategoryOut
  attributes: [],   // lista de AttributeOut
  catById:    {},   // { id: CategoryOut } con _children añadidos
  roots:      [],   // categorías sin padre
}
```

`_buildTree(cats)` convierte la lista plana en árbol en memoria añadiendo `_children: []` a cada nodo.

#### Service

Orquesta el **patrón dos fases** antes de delegar a `API`.

`_withImpact(phase1Call, phase2Call)` — helper genérico para E1-E5:
```
1. Llama phase1Call()
2. Si status != "impact_pending" → retorna el resultado directamente
3. Abre Render.impactModal() → await resolución del usuario
4. Si el usuario canceló → retorna null
5. Llama phase2Call(resolution)
6. Si sigue siendo impact_pending → toast de error, retorna null
7. Retorna el resultado final
```

| Método | Evento |
|---|---|
| `loadAll()` | Carga categorías y atributos, actualiza State |
| `changeFather(catId, newFatherId)` | E1/E2/E3 |
| `removeFather(catId)` | E3 |
| `addAttributeToCategory(catId, attrId)` | E4 |
| `removeAttributeFromCategory(catId, attrId)` | E5 |
| `changeProductCategory(prodId, newCatId)` | E6 (lógica propia, no usa `_withImpact`) |
| `createCategory/Attribute/Product(body)` | CRUD |
| `deleteCategory/Attribute/Product(id)` | CRUD |
| `addVariant(prodId, impls)` | E7a |
| `removeVariant(prodId, varId)` | E7b |

---

### render.js — `Render`

Renderiza HTML en el DOM. No hace llamadas HTTP.

| Método | Descripción |
|---|---|
| `tree()` | Renderiza el árbol completo en `#tree-container` |
| `_treeNode(cat)` | Genera el HTML recursivo de un nodo |
| `attributeList()` | Renderiza el panel derecho con la tabla de todos los atributos (editar/eliminar) |
| `categoryDetail(cat)` | Renderiza el panel derecho con detalle de categoría |
| `categoryChildren(cat, products)` | Completa la sección de hijos/productos en el detalle |
| `productDetail(prod)` | Renderiza el panel derecho con detalle de producto |
| `impactModal(impact, msg)` | **Devuelve una Promise** — muestra el modal E1-E5 y resuelve con la resolución del usuario (o `null` si cancela) |
| `e6Modal(toAdd, toRemove, msg)` | **Devuelve una Promise** — muestra el modal E6 y resuelve con `{ remove_action, new_implementations }` (o `null`) |
| `formModal(title, bodyHtml, onConfirm)` | Modal genérico para formularios CRUD |
| `placeholder(msg?)` | Muestra el estado vacío del panel derecho |

#### Modales basados en Promises

```js
// En service.js:
const resolution = await Render.impactModal(data.impact, data.message);
if (!resolution) return null;  // usuario canceló
```

Esto permite que el flujo de dos fases se escriba de forma lineal con `async/await`.

---

### events.js — `Events`

Manejadores de interacción del usuario. Es el punto de entrada de todos los clicks.

```js
document.addEventListener('DOMContentLoaded', () => Events.init());
```

| Método | Trigger |
|---|---|
| `init()` | DOMContentLoaded |
| `refresh()` | Botón refrescar |
| `selectCategory(catId)` | Click en nodo del árbol |
| `selectProduct(prodId)` | Click en producto de la lista |
| `loadCategoryChildren(cat)` | Automático al seleccionar categoría |
| `openChangeFather(catId)` | Botón "Cambiar padre" en detalle |
| `removeFather(catId)` | Botón "Quitar padre" en detalle |
| `addAttribute(catId, attrId)` | Dropdown "Agregar atributo" |
| `removeAttribute(catId, attrId)` | Botón × en badge de atributo |
| `openChangeCategory(prodId)` | Botón "Cambiar categoría" en detalle de producto |
| `openAddVariant(prodId)` | Botón "Agregar variante" |
| `removeVariant(prodId, varId)` | Botón "quitar" en tarjeta de variante |
| `openCreateCategory()` | Botón navbar |
| `openAttributeList()` | Botón "Atributos" en navbar — muestra panel de gestión |
| `openCreateAttribute()` | Botón "+ Nuevo atributo" dentro del panel de atributos |
| `editAttribute(attrId)` | Botón ✏ en fila de atributo — abre form modal prefillado |
| `deleteAttribute(attrId)` | Botón 🗑 en fila de atributo — pide confirmación y elimina |
| `openCreateProduct(preCatId?)` | Botón navbar o botón en lista de productos |
| `deleteCategory(catId)` | Botón papelera en detalle de categoría |
| `deleteProduct(prodId)` | Botón papelera en detalle de producto |

---

## Layout HTML

```
┌──────────────────────────────────────────────┐
│ Navbar: [+ Categoría] [+ Atributo] [+ Producto] [↺] │
├─────────────────┬────────────────────────────┤
│ col-md-3        │ col-md-9                   │
│ #tree-container │ #detail-panel              │
│ Árbol recursivo │ Detalle categoría/producto │
└─────────────────┴────────────────────────────┘
```

**Modales:**
- `#impact-modal` — resolución de impacto E1-E5 (un select "eliminar/heredar" por grupo)
- `#e6-modal` — resolución de cambio de categoría E6
- `#form-modal` — formularios CRUD genéricos

**Spinner:** `#global-spinner` — overlay fijo que cubre toda la pantalla durante requests HTTP.

**Toast:** `#app-toast` — notificaciones en esquina inferior derecha.
