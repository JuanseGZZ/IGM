# front_framework_test_documentation — Tests de frontFW

Documentación del archivo `TestingConcepts/test_framework.js`.
132 assertions, 0 fail, 0 skip en condiciones normales.

---

## Cómo correr

```bash
# 1. Levantar el servidor (desde TestingConcepts/app/)
uvicorn server_apis:app --port 8001

# 2. Correr el test (desde la raíz del repo)
node TestingConcepts/test_framework.js
```

**Prerrequisitos:**
- Servidor corriendo en `http://localhost:8001`
- PostgreSQL `postgres-productos` con DB `productos` activa
- `TestingConcepts/package.json` con `"type": "module"` (ya existe)

---

## Diseño del test runner

No usa ninguna librería externa. Todo es vanilla JS + Node fetch nativo (v18+).

```js
// Salida con colores ANSI
ok("label", condición, got?)   // ✓ verde / ✗ rojo + valor recibido
skip("label", razón)           // ● amarillo
section("Título")              // encabezado de sección en negrita

// Sufijo único por ejecución — evita conflictos de key en DB
const TS = Date.now().toString(36).toUpperCase();
// → cada run crea keys como tfw_mat_O1X2, tfw_col_O1X2, etc.
```

**Tabla de IDs globales** (se construyen durante el run y se usan en cleanup):

| Variable        | Contenido                                   |
|-----------------|---------------------------------------------|
| `ids.attrStat`  | ID del attribute estático text creado en §2 |
| `ids.attrEnum`  | ID del attribute enum dinámico creado en §2 |
| `ids.attrDyn`   | ID del attribute dinámico text creado en §2 |
| `ids.attrTmp`   | ID del attribute temporal creado en §5.3    |
| `ids.cat`       | ID de la categoría de prueba creada en §3   |
| `ids.prod`      | ID del producto de prueba creado en §4      |
| `ids.prodCode`  | `"TFW-{TS}"` — código único del producto    |
| `impactCatId`   | ID de la categoría del two-call §5.1        |
| `impactAttrId`  | ID del atributo del two-call §5.1           |

---

## § 1 — DTOs (unit tests sin servidor)

No requieren servidor. Testean la capa de modelos contra raw JSON estático.

### 1.1 AttributeDTO (7 assertions)

| Assertion | Verifica |
|-----------|----------|
| `fromJSON asigna campos` | `id`, `key`, `name` correctos tras `fromJSON` |
| `isEnum()` | `data_type="enum"` → `true` |
| `isDynamic()` | `is_static=false` → `true` |
| `isStatic()` | `is_static=false` → `false` |
| `enum_values correcto` | array con los valores correctos |
| `toJSON retorna objeto plano con id` | `toJSON()` incluye `id` y `key` |
| `is_static text` | atributo `is_static=true` → `isStatic()=true`, `isEnum()=false` |

### 1.2 AttributeImplementationDTO (5 assertions)

| Assertion | Verifica |
|-----------|----------|
| `fromJSON` | `id` y `value` correctos |
| `attribute es AttributeDTO` | el atributo anidado se mapea como instancia |
| `castValue enum → string` | `data_type="enum"` → string sin conversión |
| `castValue number → float` | `"3.14"` → `3.14` (parseFloat) |
| `castValue boolean → true` | `"true"` → `true` (boolean real) |

### 1.3 VariantDTO (6 assertions)

| Assertion | Verifica |
|-----------|----------|
| `fromJSON id` | `id` correcto |
| `implementations mapeadas` | array de `AttributeImplementationDTO` |
| `getValue('color')` | busca por key y devuelve valor casteado |
| `getValue('talle')` | funciona con text |
| `getValue key inexistente → null` | key que no existe → `null` |
| `toJSON incluye attribute_implementations` | array en el JSON plano |

### 1.4 CategoryDTO (6 assertions)

| Assertion | Verifica |
|-----------|----------|
| `fromJSON nombre` | `id` y `name` correctos |
| `attributes mapeados` | lista de `AttributeDTO` |
| `getDynamicAttributes()` | filtra `is_static=false` |
| `getStaticAttributes()` | filtra `is_static=true` |
| `products se guarda raw` | products sin mapear (evita import circular) |
| `null → null` | `fromJSON(null)` devuelve `null` |

### 1.5 ProductDTO (10 assertions)

| Assertion | Verifica |
|-----------|----------|
| `fromJSON campos base` | `id`, `code`, `price` correctos |
| `category es CategoryDTO` | `category` se mapea como instancia |
| `category.id accesible` | la API devuelve `category` como objeto, no `category_id` |
| `variants mapeadas` | lista de `VariantDTO` |
| `getAllDynamicAttributes() deduplica cat+own` | cat(talle) + own(coleccion) = 2, sin duplicar |
| `getAllStaticAttributes()` | solo material de la categoría |
| `getImplementation('material')` | busca por key del atributo |
| `getImplementation clave inexistente → null` | key que no existe |
| `variant.getValue('talle')` | acceso encadenado a valor de variante |
| `toJSON tiene todos los campos` | `code`, `category`, `variants` presentes |

---

## § 2 — AttributeService (14 assertions)

Tests de integración contra el servidor real.

### 2.1 create — text estático (4 assertions)
```js
AttributeService.create({ key: `tfw_mat_${TS}`, data_type: "text", is_static: true })
```
Verifica: retorna `AttributeDTO`, `id > 0`, `key` correcto, `isStatic()=true`.

### 2.2 create — enum dinámico (4 assertions)
```js
AttributeService.create({ key: `tfw_col_${TS}`, data_type: "enum", is_static: false,
                           enum_values: ["rojo", "azul"] })
```
Verifica: retorna `AttributeDTO`, `isEnum()`, `isDynamic()`, `enum_values.length === 2`.

### 2.3 create — dinámico text (2 assertions)
```js
AttributeService.create({ key: `tfw_tal_${TS}`, data_type: "text", is_static: false })
```
Verifica: retorna `AttributeDTO`, `isDynamic()`.

### 2.4 getAll (3 assertions)
Verifica: array, elementos son `AttributeDTO`, contiene el creado en 2.1.

### 2.5 getById (3 assertions)
Verifica: `AttributeDTO` por id, mismo id, id inexistente → `null`.

### 2.6 update (2 assertions)
```js
AttributeService.update(id, { name: "TFW Material v2" })
```
Verifica: retorna `AttributeDTO`, `name` actualizado.

### 2.7 addEnumValue (2 assertions)
```js
AttributeService.addEnumValue(id, "verde")
```
Verifica: retorna `AttributeDTO`, `enum_values` incluye `"verde"`.

---

## § 3 — CategoryService (14 assertions)

### 3.1 create (3 assertions)
```js
CategoryService.create("TFW Categoría Test")
```
Verifica: `CategoryDTO`, `id > 0`, `name` correcto.

### 3.2 getAll (3 assertions)
Verifica: array, elementos son `CategoryDTO`, contiene la creada en 3.1.

### 3.3 getById (3 assertions)
Verifica: `CategoryDTO`, mismo id, id inexistente → `null`.

### 3.4 updateName (2 assertions)
```js
CategoryService.updateName(id, "TFW Cat Actualizada")
```
Verifica: `CategoryDTO`, name actualizado.

### 3.5 addDynamicAttribute — sin impacto (3 assertions)
```js
CategoryService.addDynamicAttribute(catId, attrEnumId, null)
// null = sin container DOM, la categoría no tiene productos → no hay impacto
```
Verifica: `CategoryDTO`, atributo presente en `cat.attributes`, es dinámico.

> Precondición: la categoría no tiene productos → el server responde directamente sin pedir implementaciones.

### 3.6 addStaticAttribute — sin impacto (2 assertions)
```js
CategoryService.addStaticAttribute(catId, attrStatId, null)
```
Verifica: `CategoryDTO`, atributo estático presente.

---

## § 4 — ProductService (23 assertions)

### 4.1 create (6 assertions)
```js
ProductService.create({
  code: `TFW-${TS}`, title: "TFW Producto Test",
  price: 1234, description: "...", brand: "TestBrand",
  category_id: ids.cat,
})
```
Verifica: `ProductDTO`, `id > 0`, `code`, `price`, `category` es objeto (`CategoryDTO`), `category.id` correcto.

> **Nota:** el campo `category` es un objeto completo, NO `category_id`. Para leer el id: `prod.category.id`.

### 4.2 getAll (3 assertions)
Verifica: array, elementos son `ProductDTO`, contiene el creado.

### 4.3 getById (4 assertions)
Verifica: `ProductDTO`, mismo id, `variants` es array, id inexistente → `null`.

### 4.4 getByCode (3 assertions)
Verifica: `ProductDTO`, code correcto, code inexistente → `null`.

### 4.5 update (3 assertions)
```js
ProductService.update(id, { title: "TFW Producto Actualizado", price: 9999 })
```
Verifica: `ProductDTO`, title y price actualizados.

### 4.6 addImplementation — atributo estático (4 assertions)
```js
ProductService.addImplementation(prodId, attrStatId, "algodón")
```
Verifica: `ProductDTO`, `attributes_implementations.length > 0`, `getImplementation(key)` funciona, `castValue()` devuelve el string correcto.

### 4.7 addDynamicAttribute — sin impacto (2 assertions)
```js
ProductService.addDynamicAttribute(prodId, attrDynId, null)
// null = sin container; el producto no tiene variantes aún → sin impacto
```
Verifica: `ProductDTO`, atributo en `prod.attributes`.

### 4.8 createVariant — con implementations directas (4 assertions)
```js
ProductService.createVariant(prodId, [
  { attribute_id: attrDynId,  value: "L" },
  { attribute_id: attrEnumId, value: "rojo" },
], null)
```
Verifica: `ProductDTO`, `variants.length > 0`, variante con attrDyn=L presente, `variant.getValue(key)` devuelve `"L"`.

---

## § 5 — Two-call pattern (nivel API, sin DOM)

Los services manejan el two-call internamente con `buildDynamicImplForm` / `buildStaticImplForm` / `buildDecisionForm`. Como estas funciones usan DOM (no disponible en Node), los flujos de impacto se testean a **nivel API directamente**, replicando manualmente lo que haría el service.

### 5.1 Category addStaticAttribute con impacto (10 assertions)

**Setup:** crea una nueva categoría (`TFW Impact Cat`) y un nuevo atributo estático, luego mueve el producto de prueba (`ids.prod`) a esa categoría.

**Primera llamada:**
```js
CategoryApi.addStaticAttribute(impactCatId, { attribute_id: impactAttrId })
// → { needs_implementations: true, impact: [{ product_id, product_code }] }
```
Verifica: `status 200`, `needs_implementations=true`, `impact` es array con el producto.

**Segunda llamada:**
```js
CategoryApi.addStaticAttribute(impactCatId, {
  attribute_id: impactAttrId,
  implementations: [{ product_id, value: "valor-test" }],
})
// → { category: { id, attributes: [...] } }
```
Verifica: `status 200`, categoría devuelta con `id` correcto, atributo presente en `category.attributes`.

### 5.2 Category removeAttribute — needs_decision (5 assertions)

**Primera llamada:**
```js
CategoryApi.removeAttribute(impactCatId, impactAttrId, 0)
// del_opt=0 → detectar impacto sin eliminar
// → { needs_decision: true, impact: [{ product_id, product_code }] }
```
Verifica: `status 200`, `needs_decision=true`, `impact` con productos.

**Segunda llamada:**
```js
CategoryApi.removeAttribute(impactCatId, impactAttrId, 1)
// del_opt=1 → eliminar implementaciones huérfanas
// → { category: { attributes: [...sin el atributo...] } }
```
Verifica: `status 200`, atributo ya no está en `category.attributes`.

### 5.3 Product addDynamicAttribute — con variantes (two-call) (6 assertions)

**Setup:** crea un atributo temporal dinámico (`tfw_tmp_{TS}`). El producto de prueba ya tiene una variante (del test 4.8).

**Primera llamada:**
```js
ProductApi.addDynamicAttribute(prodId, { attribute_id: nAttrId })
// → { needs_implementations: true, impact: [{ variant_id }] }
```
Verifica: `status 200`, `needs_implementations=true`, `impact` contiene variantes.

**Segunda llamada:**
```js
ProductApi.addDynamicAttribute(prodId, {
  attribute_id: nAttrId,
  variant_options: [{ variant_id, value: "verano" }],
})
// → { product: { id, ... } }
```
Verifica: `status 200`, `product.id` correcto.

> El atributo temporal (`ids.attrTmp`) **no se elimina aquí** — se elimina en §6 Cleanup, DESPUÉS de eliminar el producto (que borra en cascada sus implementaciones).

### 5.4 Product createVariant — implementations_invalid (4 assertions)

Usa un **producto fresco** (`TFW-F54-{TS}`) para aislar este test del estado del producto principal.

```js
// Setup: crear producto, agregarle attrDyn
ProductApi.create({ code: `TFW-F54-${TS}`, category_id: ids.cat, ... })
ProductApi.addDynamicAttribute(freshProd, { attribute_id: attrDynId })

// Llamar createVariant con [] → debe detectar que faltan atributos
ProductApi.createVariant(freshProd, [])
// → HTTP 200 con { error: "implementations_invalid", needed_attributes: [...] }
```

Verifica: `status 200`, `error === "implementations_invalid"`, `needed_attributes` es array no vacío, los atributos se mapean correctamente a `AttributeDTO[]`.

> El server retorna `implementations_invalid` como HTTP 200 (no 400). El service detecta este campo y renderiza `buildVariantForm`. Los tests verifican que el frontend pueda mapear `needed_attributes` correctamente.

El producto fresco se elimina en el `finally` de este bloque.

---

## § 6 — Cleanup (8 assertions)

Elimina todos los datos creados durante el test en **orden secuencial** para respetar FK constraints:

| Paso | Elimina | Razón del orden |
|------|---------|-----------------|
| 1 | Variantes del producto | Antes de eliminar el producto |
| 2 | Producto | Libera FK de categorías |
| 3 | Categoría test | Sin productos |
| 4 | Categoría impact | Sin productos |
| 5 | Attr estático | Sin implementaciones (producto eliminado) |
| 6 | Attr enum | Sin implementaciones |
| 7 | Attr dinámico | Sin implementaciones |
| 8 | Attr temporal | Sin implementaciones (producto eliminado en paso 2) |

> **IMPORTANTE:** las promesas en la lista de cleanup son **lazy** (funciones `() => Promise`), no eager. Si fueran `[label, promise]` con la promise ya evaluada, todas correrían en paralelo y las categorías se intentarían borrar antes de que el producto fuera eliminado.

---

## Bugs del servidor descubiertos y corregidos

### InFailedSqlTransaction — psycopg deja transacción abierta en error

**Síntoma:** después de cualquier operación que falla con error de DB (ej: FK violation al intentar borrar un atributo con implementaciones), todas las requests siguientes devuelven 500 con `InFailedSqlTransaction`.

**Causa:** `crud_base.py` no llama `conn.rollback()` cuando un error de DB ocurre. La conexión psycopg queda en estado fallido y PostgreSQL ignora todos los comandos hasta que se haga un rollback.

**Fix aplicado en `server_apis.py`:**

```python
# Antes:
def _run(fn):
    try:
        return fn()
    except ValueError as e:
        _400(str(e))

# Después:
from config import conn

def _run(fn):
    try:
        return fn()
    except ValueError as e:
        conn.rollback()   # ← reset de la transacción también en 400
        _400(str(e))
    except Exception:
        conn.rollback()   # ← reset en cualquier error de DB
        raise
```

---

## Keys únicas por ejecución

Todos los atributos y el producto usan un sufijo `TS = Date.now().toString(36).toUpperCase()` para evitar conflictos de unique key en DB entre ejecuciones:

| Entidad | Key/Code |
|---------|---------|
| Attr estático | `tfw_mat_{TS}` |
| Attr enum dinámico | `tfw_col_{TS}` |
| Attr dinámico text | `tfw_tal_{TS}` |
| Attr temporal | `tfw_tmp_{TS}` |
| Attr de impacto | `tfw_imp_{TS}` |
| Producto principal | `TFW-{TS}` |
| Producto fresh (5.4) | `TFW-F54-{TS}` |

---

## Notas de implementación

| Nota | Detalle |
|------|---------|
| ES Module | El test usa `import` top-level. Requiere `TestingConcepts/package.json` con `"type": "module"` |
| DOM no disponible | Los tests de two-call se hacen a nivel API. Los métodos de service que usan `buildDynamicImplForm` (con `container` DOM) se pasan `null` cuando no hay impacto esperado |
| Atributo temporal y cleanup | `ids.attrTmp` se crea en §5.3 y se elimina en §6 DESPUÉS del producto, porque el producto tiene implementaciones del atributo. Borrarlo antes causaría FK violation |
| `implementations_invalid` como HTTP 200 | El server devuelve este error como 200, no 400. El `request()` helper no lo trata como error — retorna `{ status: 200, data: { error, needed_attributes } }` |
