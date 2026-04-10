# Front Test APIs — Guía para el Frontend

> Este documento explica **qué prueba `test_api.js`**, qué contrato garantiza cada test, y qué debe esperar el frontend en cada llamada.  
> Es un complemento de `interfaces.md` — donde están los schemas completos — enfocado en los casos concretos validados y verificados contra la DB real.

---

## Índice

1. [Cómo correr los tests](#1-cómo-correr-los-tests)
2. [Infraestructura necesaria](#2-infraestructura-necesaria)
3. [Estructura del archivo de tests](#3-estructura-del-archivo-de-tests)
4. [Sección 1 — Attributes (tests 1.1 – 1.9)](#4-sección-1--attributes)
5. [Sección 2 — Categories (tests 2.1 – 2.7)](#5-sección-2--categories)
6. [Sección 3 — Products (tests 3.1 – 3.13)](#6-sección-3--products)
7. [Sección 4 — Flujos con impacto (tests 4.1 – 4.4)](#7-sección-4--flujos-con-impacto)
8. [Sección 5 — Limpieza](#8-sección-5--limpieza)
9. [Contratos verificados por los tests](#9-contratos-verificados-por-los-tests)
10. [Notas de implementación relevantes para el frontend](#10-notas-de-implementación-relevantes-para-el-frontend)

---

## 1. Cómo correr los tests

```bash
# 1. Levantar el server (desde la raíz del repo)
uvicorn server_apis:app --reload --app-dir TestingConcepts/app --port 8001

# 2. En otra terminal, correr los tests
~/.nvm/versions/node/v24.14.1/bin/node TestingConcepts/test_api.js
```

**Resultado esperado:**
```
RESULTADO: 90/90 tests pasaron
```

El archivo no tiene dependencias externas — usa `fetch` nativo de Node >= 18.

---

## 2. Infraestructura necesaria

| Componente | Detalle |
|---|---|
| **Server** | FastAPI en `http://localhost:8001` |
| **DB** | PostgreSQL — container `postgres-productos`, DB `productos` |
| **Credenciales DB** | user: `postgres`, password: `13adsASD21.` |
| **Node** | `~/.nvm/versions/node/v24.14.1/bin/node` (v24) |
| **Python venv** | `TestingConcepts/.venv` |

---

## 3. Estructura del archivo de tests

```
test_api.js
│
├── helpers
│   ├── req(method, path, body)   → { status, data }   — fetch wrapper
│   ├── assert(label, cond, got)  → imprime ✓ o ✗
│   └── section(title)            → encabezado de sección
│
├── ids {}   — objeto global que acumula los IDs creados durante el run
│              (dynAttr, statAttr, cat, prod, variant1, variant2, dynAttr2, ...)
│
├── testAttributes()    — sección 1
├── testCategories()    — sección 2
├── testProducts()      — sección 3
├── testImpactFlows()   — sección 4
├── cleanup()           — sección 5
└── main()              — orquesta todo en secuencia
```

Los tests son **secuenciales** — cada sección depende de los IDs creados en la anterior. Si un test de creación falla, los siguientes pueden fallar en cascada.

---

## 4. Sección 1 — Attributes

### 1.1 `GET /attributes`

```
→  GET /attributes
←  200  [ { id, key, name, data_type, is_static, enum_values[] }, ... ]
```

**Qué verifica:** el endpoint responde y retorna un array (puede estar vacío).

---

### 1.2 `POST /attributes` — atributo enum dinámico

```
→  POST /attributes
   { "key": "talle_<ts>", "name": "Talle", "data_type": "enum",
     "is_static": false, "enum_values": ["S","M","L"] }

←  201  { "id": <int>, "key": "talle_<ts>", "name": "Talle",
          "data_type": "enum", "is_static": false,
          "enum_values": ["S","M","L"] }
```

**Qué verifica:**
- Código 201
- El objeto devuelto tiene `id` numérico
- `key` y `enum_values` coinciden exactamente con lo enviado

> El `key` lleva timestamp (`talle_<ts>`) para evitar colisiones entre runs.  
> El frontend debe usar keys únicos — la BD tiene `UNIQUE` en `key`.

---

### 1.3 `POST /attributes` — atributo text estático

```
→  POST /attributes
   { "key": "material_<ts>", "name": "Material",
     "data_type": "text", "is_static": true }

←  201  { "id": <int>, ..., "is_static": true, "enum_values": [] }
```

**Qué verifica:** `is_static: true` se persiste correctamente.  
Cuando el tipo no es `enum`, `enum_values` devuelve `[]`.

---

### 1.4 `GET /attributes/{id}`

```
→  GET /attributes/325
←  200  { "id": 325, ... }
```

**Qué verifica:** GET individual devuelve el objeto con el ID correcto.

---

### 1.5 `PATCH /attributes/{id}` — actualizar nombre

```
→  PATCH /attributes/325
   { "name": "Talle (actualizado)" }

←  200  { ..., "name": "Talle (actualizado)", ... }
```

**Qué verifica:** solo el campo `name` se actualiza. El resto queda intacto.  
Todos los campos del body son opcionales — se actualiza solo lo que se envía.

---

### 1.6 `PATCH /attributes/{id}` — reemplazar enum_values

```
→  PATCH /attributes/325
   { "enum_values": ["XS","S","M","L","XL"] }

←  200  { ..., "enum_values": ["XS","S","M","L","XL"] }
```

**Qué verifica:** `enum_values` es un **reemplazo total**, no un append.  
Si el frontend envía `["XS","S","M","L","XL"]` y antes había `["S","M","L"]`, el resultado final es `["XS","S","M","L","XL"]`.

---

### 1.7 `POST /attributes/{id}/enum-values` — agregar un valor

```
→  POST /attributes/325/enum-values
   { "value": "XXL" }

←  200  { ..., "enum_values": ["XS","S","M","L","XL","XXL"] }
```

**Qué verifica:** el valor se agrega al final de la lista existente.

---

### 1.8 `POST /attributes/{id}/enum-values` — duplicado → 400

```
→  POST /attributes/325/enum-values
   { "value": "XXL" }   ← ya existe

←  400  { "detail": "..." }
```

**Qué verifica:** regla de negocio — no se pueden tener valores duplicados.  
El frontend debe mostrar un mensaje de error cuando reciba 400 en este endpoint.

---

### 1.9 `GET /attributes/99999` — not found → 404

```
→  GET /attributes/99999
←  404  { "detail": "Atributo '99999' no encontrado" }
```

---

## 5. Sección 2 — Categories

### 2.1 `POST /categories` — crear categoría

```
→  POST /categories
   { "name": "TestCat_<ts>" }

←  201  { "id": <int>, "name": "TestCat_<ts>",
          "attributes": [], "products": [] }
```

**Qué verifica:** la categoría recién creada tiene arrays vacíos de atributos y productos.

---

### 2.2 `GET /categories`

```
→  GET /categories
←  200  [ { "id", "name", "attributes": [...], "products": [...] }, ... ]
```

**Qué verifica:** el endpoint lista todas las categorías y la categoría recién creada aparece en la lista.

> La respuesta incluye los objetos `attributes` y `products` completos, no solo IDs.

---

### 2.3 `GET /categories/{id}`

```
→  GET /categories/42
←  200  { "id": 42, "name": "...", "attributes": [...], "products": [...] }
```

---

### 2.4 `PATCH /categories/{id}` — actualizar nombre

```
→  PATCH /categories/42
   { "name": "TestCat_<ts>_v2" }

←  200  { "id": 42, "name": "TestCat_<ts>_v2", ... }
```

**Nota:** en categorías el body solo acepta `name`. No hay otros campos actualizables.

---

### 2.5 `POST /categories/{id}/static-attribute` — sin productos (sin impacto)

```
→  POST /categories/42/static-attribute
   { "attribute_id": 325 }

←  200  { "needs_implementations": false,
          "category": { "id": 42, "name": "...",
                        "attributes": [{ "id": 325, ... }],
                        "products": [] } }
```

**Qué verifica:**
- Cuando la categoría no tiene productos, agregar un atributo (estático o dinámico) no requiere implementations.
- La respuesta tiene `needs_implementations: false` y el objeto `category` completo con el atributo ya incluido.

---

### 2.6 `POST /categories/{id}/dynamic-attribute` — sin productos (sin impacto)

```
→  POST /categories/42/dynamic-attribute
   { "attribute_id": 330 }

←  200  { "needs_implementations": false,
          "category": { ..., "attributes": [{...}, { "id": 330, ... }] } }
```

**Qué verifica:** mismo patrón que el estático. Cuando no hay productos, no hay impacto.

---

### 2.7 `GET /categories/99999` — not found → 404

```
←  404  { "detail": "Categoría '99999' no encontrado" }
```

---

## 6. Sección 3 — Products

### 3.1 `POST /products` — crear producto

```
→  POST /products
   { "code": "TEST-<ts>", "title": "Remera Test", "price": 1500.0,
     "description": "Remera de algodón para testing",
     "brand": "TestBrand", "category_id": 42 }

←  201  { "id": <int>, "code": "TEST-<ts>", "title": "Remera Test",
          "price": 1500.0, "description": "...", "brand": "TestBrand",
          "category": { "id": 42, "name": "...", "attributes": [...] },
          "attributes": [],
          "attributes_implementations": [],
          "variants": [] }
```

**Qué verifica:**
- El campo `category_id` en el body se mapea al objeto `category` en la respuesta (no existe `category_id` top-level en la respuesta).
- `variants`, `attributes` y `attributes_implementations` empiezan vacíos.

> **Importante para el frontend:** la respuesta usa `category` (objeto completo), no `category_id`. Para leer el ID de la categoría del producto: `data.category.id`.

---

### 3.2 `GET /products`

```
←  200  [ { "id", "code", "title", "price", "description", "brand",
             "category": {...}, "attributes": [...],
             "attributes_implementations": [...], "variants": [...] }, ... ]
```

Cada producto en la lista viene completo con sus relaciones.

---

### 3.3 `GET /products/{id}`

```
←  200  { "id", "code", "title", "price", "description", "brand",
          "category": { "id", "name", "attributes": [...] },
          "attributes": [...],
          "attributes_implementations": [ { "id", "attribute": {...}, "value" }, ... ],
          "variants": [ { "id", "attribute_implementations": [...] }, ... ] }
```

---

### 3.4 `GET /products/by-code/{code}`

```
→  GET /products/by-code/TEST-1748800000000
←  200  { mismo schema que GET /products/{id} }
```

**Nota:** este endpoint debe ir antes de `/{prod_id}` en la definición de rutas para que FastAPI no intente parsear `"by-code"` como un entero.

---

### 3.5 `PATCH /products/{id}` — actualizar campos base

```
→  PATCH /products/10
   { "title": "Remera Test v2", "price": 1800.0 }

←  200  { ..., "title": "Remera Test v2", "price": 1800.0, ... }
```

Todos los campos son opcionales. Solo se actualizan los que se envían.  
Campos actualizables: `title`, `price`, `description`, `brand`, `category_id`.

---

### 3.6 `POST /products/{id}/implementations` — impl estática

```
→  POST /products/10/implementations
   { "attribute_id": 325, "value": "algodón 100%" }

←  200  { ..., "attributes_implementations": [
            { "id": <int>, "attribute": { "id": 325, ... }, "value": "algodón 100%" }
          ], ... }
```

**Qué verifica:**
- La impl aparece en `attributes_implementations` del producto devuelto.
- El objeto de la impl tiene `attribute` (objeto completo) y `value` (string).

> El atributo debe estar en la categoría del producto (o ser propio del producto). Si no está suscripto → 400.

---

### 3.7 `POST /products/{id}/dynamic-attribute` — sin variantes (sin impacto)

```
→  POST /products/10/dynamic-attribute
   { "attribute_id": 330 }

←  200  { "needs_implementations": false,
          "product": { ..., "attributes": [{ "id": 330, ... }], ... } }
```

Cuando el producto no tiene variantes todavía, agregar un atributo dinámico no requiere cubrirlas.

---

### 3.8 `POST /products/{id}/variants` — crear primera variante

```
→  POST /products/10/variants
   { "implementations": [
       { "attribute_id": 330, "value": "S" }
     ] }

←  200  { ..., "variants": [
            { "id": <int>, "attribute_implementations": [
                { "id": <int>, "attribute": { "id": 330, ... }, "value": "S" }
              ] }
          ] }
```

**Qué verifica:**
- `implementations` debe cubrir **exactamente** todos los atributos dinámicos del producto.
- La variante creada aparece en `variants` con sus `attribute_implementations`.

---

### 3.9 `POST /products/{id}/variants` — segunda variante

Mismo endpoint, mismo body pero con `"value": "M"`. El producto acumula variantes:
```
"variants": [ {id: v1, ...}, {id: v2, ...} ]
```

---

### 3.10 `POST /products/{id}/variants` — implementations vacías → error

```
→  POST /products/10/variants
   { "implementations": [] }

←  200  { "error": "implementations_invalid",
          "needed_attributes": [
            { "id": 330, "key": "talle_<ts>", "name": "Talle", ... }
          ] }
```

**Qué verifica:** cuando las implementations no cubren los atributos necesarios, la respuesta es `200` (no 4xx) con un body de error que incluye `needed_attributes`.

> **El frontend debe:** detectar `data.error === "implementations_invalid"` y mostrar al usuario qué atributos necesita completar (la lista viene en `needed_attributes`).

---

### 3.11 `GET /products/{id}` — estado completo con variantes

```
←  200  { ..., "variants": [
            { "id": v1, "attribute_implementations": [ {attr, value} ] },
            { "id": v2, "attribute_implementations": [ {attr, value} ] }
          ] }
```

**Qué verifica:** el producto tiene 2 variantes y cada variante tiene `attribute_implementations` con la impl del atributo dinámico.

---

### 3.12 `DELETE /products/{id}/variants/{variant_id}` — eliminar variante

```
→  DELETE /products/10/variants/v2
←  200  { ..., "variants": [ { id: v1, ... } ] }
```

Devuelve el producto con la variante eliminada. La variante restante permanece intacta.

---

### 3.13 `GET /products/by-code/NOEXISTE` → 404

```
←  404  { "detail": "Producto con código 'NOEXISTE' no encontrado" }
```

---

## 7. Sección 4 — Flujos con impacto

Esta sección verifica el **patrón de dos llamadas** para operaciones que afectan variantes o productos existentes.

### 4.1 Crear segundo atributo dinámico (`color`)

```
→  POST /attributes
   { "key": "color_<ts>", "name": "Color", "data_type": "enum",
     "is_static": false, "enum_values": ["rojo","azul","negro"] }
←  201  { "id": <int>, ... }
```

---

### 4.2 Primera llamada — `needs_implementations: true`

El producto ya tiene una variante (talle=S). Se intenta agregar el atributo `color` sin proveer valores.

```
→  POST /products/10/dynamic-attribute
   { "attribute_id": <color_id> }

←  200  { "needs_implementations": true,
          "impact": [ { "variant_id": <v1> } ] }
```

**Qué verifica:**
- `needs_implementations: true` aparece cuando hay variantes sin cubrir.
- `impact` lista los `variant_id` que necesitan valor para el nuevo atributo.
- **No se modifica nada** — es una consulta de impacto pura.

---

### 4.3 Segunda llamada — con `variant_options` completas

```
→  POST /products/10/dynamic-attribute
   { "attribute_id": <color_id>,
     "variant_options": [ { "variant_id": <v1>, "value": "rojo" } ] }

←  200  { "needs_implementations": false,
          "product": { ..., "variants": [
            { "id": <nuevo_v1>, "attribute_implementations": [
                { ..., "value": "S" },
                { ..., "value": "rojo" }
              ] }
          ] } }
```

**Qué verifica:**
- `needs_implementations: false` confirma que la operación completó.
- La variante ahora tiene **2 `attribute_implementations`** (talle + color).

> **Nota de implementación importante:** al guardar el producto, las variantes se **re-insertan** en la BD con nuevos IDs. El `variant_id` que tenía la variante antes puede haber cambiado. El frontend NO debe asumir que los IDs de variantes son estables entre operaciones de escritura sobre el producto.

---

### 4.4 `DELETE /categories/{id}/attributes/{attr_id}?del_opt=0`

```
→  DELETE /categories/42/attributes/325?del_opt=0

← 200  { "needs_decision": true,
         "impact": [ { "product_id": 10, "product_code": "TEST-<ts>" } ] }
     ó
   200  { "needs_decision": false, "category": {...} }
```

**Qué verifica:** el endpoint siempre devuelve `needs_decision` en la respuesta.  
Si el producto tiene una implementación del atributo estático, `needs_decision: true` e `impact` lista los afectados.

**Flujo completo que el frontend debe implementar:**
```
1. DELETE /categories/42/attributes/325?del_opt=0
   → needs_decision: true, impact: [{product_id: 10}]

2. Mostrar al usuario:
   "¿Qué hacemos con los productos que tienen implementaciones de este atributo?"
   [ Opción 1 ] Eliminar las implementaciones (del_opt=1)
   [ Opción 2 ] Migrar el atributo al producto (del_opt=2)

3. DELETE /categories/42/attributes/325?del_opt=1   (o del_opt=2)
   → needs_decision: false, category: {...}
```

---

## 8. Sección 5 — Limpieza

Los tests limpian todo lo que crearon en orden inverso de dependencias:

```
5.1  DELETE /products/{id}          ← cascadea variantes e impls
5.2  DELETE /categories/{id}        ← solo posible si no tiene productos
5.3  DELETE /attributes/<dynAttr>
5.4  DELETE /attributes/<statAttr>
5.5  DELETE /attributes/<dynAttr2>
```

**Reglas de borrado a tener en cuenta:**

| Delete | Requisito |
|---|---|
| `DELETE /products/{id}` | Ninguno — cascadea todo |
| `DELETE /categories/{id}` | La categoría no debe tener productos (FK RESTRICT) |
| `DELETE /attributes/{id}` | El atributo no debe tener `atr_implementation` apuntándole (FK RESTRICT) |

> Si se intenta borrar una categoría con productos → 400 (FK RESTRICT).  
> Si se intenta borrar un atributo referenciado → 400 (FK RESTRICT).

---

## 9. Contratos verificados por los tests

Esta tabla resume lo que los 90 tests garantizan que funciona en la API:

| # | Endpoint | Scenario | Resultado verificado |
|---|---|---|---|
| 1.1 | `GET /attributes` | Lista | 200 + array |
| 1.2 | `POST /attributes` | Enum dinámico | 201, id, key, enum_values |
| 1.3 | `POST /attributes` | Text estático | 201, is_static=true |
| 1.4 | `GET /attributes/{id}` | Existe | 200, id correcto |
| 1.5 | `PATCH /attributes/{id}` | Nombre | 200, name actualizado |
| 1.6 | `PATCH /attributes/{id}` | enum_values | 200, reemplazo total |
| 1.7 | `POST /attributes/{id}/enum-values` | Agregar | 200, valor en lista |
| 1.8 | `POST /attributes/{id}/enum-values` | Duplicado | 400 |
| 1.9 | `GET /attributes/99999` | No existe | 404 |
| 2.1 | `POST /categories` | Crear | 201, arrays vacíos |
| 2.2 | `GET /categories` | Lista | 200, categoría presente |
| 2.3 | `GET /categories/{id}` | Existe | 200, id correcto |
| 2.4 | `PATCH /categories/{id}` | Nombre | 200, actualizado |
| 2.5 | `POST /categories/{id}/static-attribute` | Sin productos | 200, needs_implementations=false |
| 2.6 | `POST /categories/{id}/dynamic-attribute` | Sin productos | 200, needs_implementations=false |
| 2.7 | `GET /categories/99999` | No existe | 404 |
| 3.1 | `POST /products` | Crear | 201, category es objeto no id |
| 3.2 | `GET /products` | Lista | 200, producto presente |
| 3.3 | `GET /products/{id}` | Completo | 200, category + impls + variants |
| 3.4 | `GET /products/by-code/{code}` | Existe | 200, code correcto |
| 3.5 | `PATCH /products/{id}` | Precio y título | 200, ambos actualizados |
| 3.6 | `POST /products/{id}/implementations` | Estática | 200, impl en array |
| 3.7 | `POST /products/{id}/dynamic-attribute` | Sin variantes | 200, needs_implementations=false |
| 3.8 | `POST /products/{id}/variants` | 1ra variante | 200, 1 variante |
| 3.9 | `POST /products/{id}/variants` | 2da variante | 200, 2 variantes |
| 3.10 | `POST /products/{id}/variants` | Impls vacías | 200, error + needed_attributes |
| 3.11 | `GET /products/{id}` | Con variantes | 200, variantes tienen impls |
| 3.12 | `DELETE /products/{id}/variants/{id}` | Eliminar | 200, 1 variante restante |
| 3.13 | `GET /products/by-code/NOEXISTE` | No existe | 404 |
| 4.1 | `POST /attributes` | Color enum | 201 |
| 4.2 | `POST /products/{id}/dynamic-attribute` | 1ra llamada con variantes | 200, needs_implementations=true, impact[] |
| 4.3 | `POST /products/{id}/dynamic-attribute` | 2da llamada con variant_options | 200, needs_implementations=false, variante con 2 impls |
| 4.4 | `DELETE /categories/{id}/attributes/{id}?del_opt=0` | Con impacto | 200, needs_decision presente |
| 5.1 | `DELETE /products/{id}` | Borrar | 200 |
| 5.2 | `DELETE /categories/{id}` | Borrar | 200 |
| 5.3-5 | `DELETE /attributes/{id}` | ×3 | 200 |

---

## 10. Notas de implementación relevantes para el frontend

### IDs de variantes no son estables

Cada vez que el producto se guarda, las variantes se **borran y re-insertan** con nuevos IDs. Esto significa:

```js
// ❌ NO hacer esto:
const variantId = product.variants[0].id;
// ... hacer alguna operación sobre el producto ...
fetch(`/products/${prodId}/variants/${variantId}`); // el ID puede no existir más

// ✅ SÍ hacer esto:
// Siempre refrescar el producto antes de usar IDs de variantes
const fresh = await fetch(`/products/${prodId}`).then(r => r.json());
const variantId = fresh.variants[0].id;
```

### La respuesta de producto usa `category` (objeto), no `category_id`

```js
// ❌ data.category_id   → undefined
// ✅ data.category.id   → número
```

### El error de variante inválida es 200, no 4xx

```js
const res = await fetch('/products/10/variants', { method: 'POST', body: ... });
const data = await res.json();

if (data.error === 'implementations_invalid') {
  // mostrar needed_attributes al usuario
  showAttributeForm(data.needed_attributes);
} else {
  // éxito: data es el producto completo
  updateProductState(data);
}
```

### El flujo de dos llamadas requiere UX de "confirmación"

Para operaciones con `needs_implementations` o `needs_decision`, el frontend necesita:

1. Llamada inicial → recibir el impacto
2. Mostrar un formulario o modal al usuario para que complete los valores
3. Segunda llamada → operación aplicada

```js
// Patrón genérico
async function addDynamicAttrToProduct(prodId, attrId, variantOptions = null) {
  const body = { attribute_id: attrId };
  if (variantOptions) body.variant_options = variantOptions;

  const res = await req('POST', `/products/${prodId}/dynamic-attribute`, body);

  if (res.data.needs_implementations) {
    // UI: pedir valores para res.data.impact (lista de variant_id)
    return { pending: true, impact: res.data.impact };
  }

  return { pending: false, product: res.data.product };
}
```

### `enum_values` en PATCH es reemplazo total

```js
// Si envías esto:
PATCH /attributes/5  { "enum_values": ["A","B"] }

// El resultado será exactamente ["A","B"] — no un merge con los existentes.
// Para agregar un solo valor sin borrar los demás, usar:
POST /attributes/5/enum-values  { "value": "C" }
```
