# API — Integración con el backend

Archivo: `api.js`

Módulo de comunicación entre el front (`events.js`) y la API REST del catálogo (`GET /catalog`, `POST /catalog`). Concentra la serialización, la deserialización y las llamadas `fetch`. No contiene lógica de negocio ni estado propio.

---

## Constante de base

```js
const API_BASE = "http://localhost:8000";
```

Punto de configuración único para la URL del backend.

---

## Funciones HTTP

### `saveCatalog(payload)`

```js
async function saveCatalog(payload) → { valid: true } | { valid: false, error: string }
```

- Hace `POST /catalog` con el payload serializado.
- Acepta respuesta `200` (válido) y `422` (inválido con detalle de error).
- Lanza `Error` para cualquier otro código HTTP.

---

### `fetchCatalog()`

```js
async function fetchCatalog() → { attributes: [...], tree: {...} | null }
```

- Hace `GET /catalog`.
- Retorna el estado completo del catálogo según lo define la API.
- Lanza `Error` si la respuesta no es `2xx`.

---

## Serialización

### `buildAPIPayload(handler, attrStore)`

Convierte el árbol de `Handler` y el `attrStore` al formato que espera `POST /catalog`:

```js
{
  attributes: [{ id, key, name, data_type, is_static, enum_values }],
  tree: { id, name, attribute_ids, subcategories, products }
}
```

**Reglas de mapeo:**

| Front (model plano) | API payload |
|---|---|
| `category.model.attributes[].id` | `attribute_ids: [id, ...]` |
| `product.model.attributes_implementations[].attribute.key` | `attributes_implementations[].attribute_key` |
| `variant.model.attribute_implementations[].attribute.key` | `attribute_implementations[].attribute_key` |
| `model.id === null` | `id: null` (el backend asigna el ID al persistir) |

Si hay más de una categoría raíz, se genera un nodo sintético `{ id: null, name: "Catálogo", ... }` que las envuelve como `subcategories`. Si hay exactamente una, se usa directamente como raíz.

---

## Deserialización

### `loadFromAPIData(handler, attrStore, data)`

Reconstruye el estado local desde la respuesta de `GET /catalog`:

1. Llama `handler.reset()` — borra el árbol y reinicia `lastId`.
2. Carga `data.attributes` directamente en `attrStore.attrs` y persiste con `attrStore._save()`.
3. Recorre `data.tree` top-down construyendo `Chart` con `handler.addNodeTo()`:
   - `attribute_ids` se resuelven a los objetos planos del `attrStore`.
   - `attribute_key` en implementaciones se resuelve a `{ key }` del `attrStore`; si no existe, queda como objeto `{ key: "..." }` para no perder el dato.
4. Los `id` del backend se guardan en `model.id` de cada nodo. Los IDs de chart (internos al front) son asignados secuencialmente por `addNodeTo`, independientes de los IDs del backend.

---

## Botones en el navbar

### `Save`

```
id="igm-save-btn"
```

1. Deshabilita el botón y muestra "Guardando…".
2. Llama `buildAPIPayload(handler, attrStore)`.
3. Llama `saveCatalog(payload)`.
4. `alert` con resultado:
   - `valid: true` → "Catálogo guardado correctamente."
   - `valid: false` → "Error de validación:\n{error}"
   - excepción → "Error al guardar:\n{message}"
5. Rehabilita el botón.

### `Bring Tree`

```
id="igm-bring-btn"
```

1. Deshabilita el botón y muestra "Cargando…".
2. Borra `localStorage["igm-catalog"]` e `localStorage["igm-attrs"]`.
3. Llama `fetchCatalog()`.
4. Si `tree === null` → alerta "La base de datos está vacía" y retorna.
5. Llama `loadFromAPIData(handler, attrStore, data)`.
6. Llama `handler.treeToMax()` y `handler.render()` (el wrap de render guarda en `catalogStore` automáticamente).
7. `alert` de éxito o de error.
8. Rehabilita el botón.

---

## Flujo completo Save → Bring Tree

```
[Usuario edita el árbol en el front]
          ↓
    click "Save"
          ↓
buildAPIPayload(handler, attrStore)
   → { attributes, tree }
          ↓
POST /catalog
   → { valid: true }    ← OK: la DB queda actualizada
   → { valid: false, error }   ← Error de validación (DB sin cambios)
          ↓
   alert con resultado

[Más tarde, o en otra sesión]
          ↓
    click "Bring Tree"
          ↓
localStorage.removeItem("igm-catalog")
localStorage.removeItem("igm-attrs")
          ↓
GET /catalog → { attributes, tree }
          ↓
loadFromAPIData(handler, attrStore, data)
          ↓
handler.treeToMax() + handler.render()
   → re-dibuja el canvas
   → catalogStore.save() (auto, por el wrap de render)
          ↓
   alert de éxito
```

---

## Dependencias de `api.js`

`api.js` no importa ningún otro módulo del proyecto. Recibe `handler` y `attrStore` como parámetros en las funciones de serialización/deserialización, manteniéndose agnóstico del estado global.
