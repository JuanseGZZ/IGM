# agregaciones.md — Cambiar padre de categoría

Todo lo que hay que agregar al frontFW para soportar `PATCH /categories/{id}/parent`.

---

## Resumen de la operación

El endpoint puede responder con tres flujos distintos en secuencia:

1. **Sin impacto** → retorna la categoría actualizada directamente.
2. **`needs_decision`** → el padre anterior tenía atributos que el nuevo no cubre (huérfanos). El usuario elige `del_opt=1` (inyectar en la categoría) o `del_opt=2` (borrar impls en productos).
3. **`needs_implementations`** → el nuevo padre tiene atributos que los descendientes no cubren todavía. El usuario completa los valores para cada producto/variante.

Estos dos últimos pueden encadenarse: primero `needs_decision`, después de resolverlo `needs_implementations`.

---

## 1. `categoryApi.js` — agregar método `changeParent`

```js
/**
 * PATCH /categories/{id}/parent
 *
 * Primera llamada (sin impacto esperado):
 *   body: { parent_id, del_opt: 0 }
 *
 * Si retorna needs_decision: segunda llamada con del_opt=1 o 2.
 * Si retorna needs_implementations: siguiente llamada con implementations.
 *
 * Respuesta posible A: { needs_decision: true, impact: [{attribute_key, attribute_name, is_static, affected_products:[{product_id, product_code}]}] }
 * Respuesta posible B: { needs_implementations: true, impact: [{attribute_key, attribute_name, is_static, products:[...]}] }
 * Respuesta posible C: CategoryDTO (la categoría actualizada, mismo formato que GET /categories/{id})
 */
changeParent(catId, body) {
  return request("PATCH", `/categories/${catId}/parent`, body);
},
```

`body` tiene este shape en cada llamada:

```js
// Primera (sondeo):
{ parent_id: 3, del_opt: 0 }

// Si needs_decision → reintento con del_opt elegido:
{ parent_id: 3, del_opt: 1 }
// o
{ parent_id: 3, del_opt: 2 }

// Si needs_implementations → reintento con implementations:
{
  parent_id: 3,
  del_opt: 1,                // el que se eligió antes (o 0 si no hubo decision)
  implementations: {
    "color":    [{ product_id: 1, variants: [{ variant_id: 10, value: "rojo" }] }],
    "material": [{ product_id: 1, value: "algodón" }],
  }
}
```

---

## 2. `formBuilder.js` — agregar `buildChangeParentDecisionForm` y `buildChangeParentImplForm`

### 2.1 `buildChangeParentDecisionForm`

Para cuando el server responde `needs_decision=true`. Muestra los atributos huérfanos con sus productos afectados y dos botones.

```js
/**
 * Formulario de decisión al cambiar padre de categoría.
 * Aparece cuando el padre anterior aportaba atributos que el nuevo no cubre.
 *
 * Muestra:
 *   [Título: "Atributos que quedarían sin cobertura"]
 *   Para cada atributo huérfano:
 *     [Nombre del atributo (tipo)]
 *     [Lista de productos afectados]
 *   [Botón: "Inyectar en la categoría"   (del_opt=1)]
 *   [Botón: "Eliminar implementaciones"  (del_opt=2)]
 *
 * @param {HTMLElement} container
 * @param {Array}       impact
 *   [{attribute_key, attribute_name, is_static, affected_products:[{product_id, product_code}]}]
 * @param {Function}    onDecision   (del_opt: 1|2) => void
 */
export function buildChangeParentDecisionForm(container, impact, onDecision) { ... }
```

CSS a usar (consistente con el resto):
- Wrapper: `igm-decision`
- Lista de atributos huérfanos: `igm-impact-list` / `igm-impact-item`
- Botón inyectar: `igm-btn igm-btn--warning`
- Botón eliminar: `igm-btn igm-btn--danger`

---

### 2.2 `buildChangeParentImplForm`

Para cuando el server responde `needs_implementations=true`. Puede tener atributos estáticos (piden valor por producto) y dinámicos (piden valor por variante), mezclados en el mismo formulario.

```js
/**
 * Formulario para completar implementaciones al cambiar padre de categoría.
 * El nuevo padre tiene atributos que los descendientes no cubren todavía.
 * Mezcla atributos estáticos (valor por producto) y dinámicos (valor por variante).
 *
 * Muestra por cada atributo en impact:
 *   [Título: nombre del atributo]
 *   [Hint: tipo / valores posibles]
 *   Si is_static=true:
 *     Para cada producto en products:
 *       [Label: código del producto]  [input/select]
 *   Si is_static=false:
 *     Para cada producto en products:
 *       [Label: código del producto]
 *       Para cada variante en producto.variants:
 *         [Label: Variante #id]  [input/select]
 * [Botón: Confirmar]
 *
 * @param {HTMLElement} container
 * @param {Array}       impact
 *   [
 *     {
 *       attribute_key:  string,
 *       attribute_name: string,
 *       is_static:      boolean,
 *       // si is_static=true:
 *       products: [{product_id, product_code}],
 *       // si is_static=false:
 *       products: [{product_id, product_code, variants:[{variant_id}]}],
 *     }
 *   ]
 * @param {Function} onSubmit
 *   onSubmit(implementations: {
 *     [attr_key]: [{product_id, value}]              // si is_static=true
 *                | [{product_id, variants:[{variant_id, value}]}]  // si is_static=false
 *   })
 */
export function buildChangeParentImplForm(container, impact, onSubmit) { ... }
```

El `onSubmit` recibe el dict `implementations` listo para meter en el body del PATCH.

Para construir los inputs, reusar `makeInput` (ya existe en formBuilder.js) con un `AttributeDTO` mínimo `{ data_type, enum_values, name }` construido desde el `attribute_key/name` del impact.

> **Nota:** `makeInput` y `parseValue` ya están en `formBuilder.js` pero no están exportados. Antes de usarlos desde esta función nueva, simplemente implementar la lógica inline o convertirlos a helpers exportados si se quiere reutilizarlos desde afuera.

---

## 3. `categoryService.js` — agregar `changeParent`

```js
/**
 * Cambia el padre de la categoría.
 *
 * Flujo automático de hasta dos rondas:
 *   Ronda 1 — sondeo (del_opt=0):
 *     a. Sin impacto         → resuelve con CategoryDTO.
 *     b. needs_decision      → renderiza buildChangeParentDecisionForm en container,
 *                              espera elección del usuario → ronda 2 con del_opt elegido.
 *     c. needs_implementations → renderiza buildChangeParentImplForm en container,
 *                              espera datos del usuario → ronda 2 con implementations.
 *
 *   Ronda 2 — puede volver a dar needs_implementations si había decision primero:
 *     a. Sin impacto         → resuelve con CategoryDTO.
 *     b. needs_implementations → renderiza buildChangeParentImplForm → ronda 3 final.
 *
 * @param {number}      catId
 * @param {number}      parentId
 * @param {HTMLElement} container   Div donde se renderizan los formularios si hay impacto
 * @returns {Promise<CategoryDTO>}
 */
async changeParent(catId, parentId, container) { ... }
```

### Pseudocódigo del flujo

```js
async changeParent(catId, parentId, container) {
  // Ronda 1: sondeo
  const { status, data } = await CategoryApi.changeParent(catId, {
    parent_id: parentId,
    del_opt: 0,
  });
  if (status === 400) throw new Error(data?.detail ?? "Error al cambiar padre");
  if (status === 404) throw new Error(data?.detail ?? "No encontrado");

  // Caso A: resuelto directo
  if (!data.needs_decision && !data.needs_implementations) {
    return CategoryDTO.fromJSON(data);
  }

  // Caso B: hay huérfanos del padre anterior → pedir decisión
  if (data.needs_decision) {
    const chosenOpt = await new Promise(resolve =>
      buildChangeParentDecisionForm(container, data.impact, resolve)
    );
    // Re-llamar con del_opt elegido
    const { status: s2, data: d2 } = await CategoryApi.changeParent(catId, {
      parent_id: parentId,
      del_opt: chosenOpt,
    });
    if (s2 === 400) throw new Error(d2?.detail ?? "Error");

    // Puede que ahora haya needs_implementations
    if (!d2.needs_implementations) {
      return CategoryDTO.fromJSON(d2);
    }
    // Caer en el bloque de implementations con del_opt ya resuelto
    return _resolveImplementations(catId, parentId, chosenOpt, d2.impact, container);
  }

  // Caso C: necesita implementations directo (sin huérfanos)
  return _resolveImplementations(catId, parentId, 0, data.impact, container);
}

async function _resolveImplementations(catId, parentId, delOpt, impact, container) {
  const implementations = await new Promise(resolve =>
    buildChangeParentImplForm(container, impact, resolve)
  );
  const { status, data } = await CategoryApi.changeParent(catId, {
    parent_id: parentId,
    del_opt: delOpt,
    implementations,
  });
  if (status === 400) throw new Error(data?.detail ?? "Implementaciones inválidas");
  return CategoryDTO.fromJSON(data);
}
```

---

## 4. `index.js` — no requiere cambio

`categoryApi.js` y `categoryService.js` ya están re-exportados desde `api/index.js` y `service/index.js` respectivamente. Los métodos nuevos quedan disponibles automáticamente.

`buildChangeParentDecisionForm` y `buildChangeParentImplForm` se exportan desde `formBuilder.js`. Si se quieren exponer desde el barrel `index.js`, agregar ahí:

```js
export { buildChangeParentDecisionForm, buildChangeParentImplForm } from "./service/formBuilder.js";
```

---

## 5. `CategoryDTO.js` — no requiere cambio

El servidor devuelve la categoría actualizada con el mismo shape que `GET /categories/{id}`. `CategoryDTO.fromJSON` ya maneja ese formato.

---

## 6. Uso desde HTML

```js
import { CategoryService } from "./frontFW/index.js";

const container = document.getElementById("form-area");

try {
  const cat = await CategoryService.changeParent(catId, newParentId, container);
  console.log("Padre actualizado:", cat.name);
} catch (err) {
  console.error(err.message);
}
```

El container solo se toca si el servidor reporta impacto. Si no hay impacto, resuelve sin renderizar nada.

---

## 7. Tests a agregar en `test_framework.js`

### § 3.x — CategoryService.changeParent (a nivel API, sin DOM)

Como los otros two-call tests, testear a nivel `CategoryApi` directamente.

**Setup necesario:**
- Crear `cat_padre_a` (sin hijos, sin atributos)
- Crear `cat_padre_b` (sin hijos, sin atributos)
- Crear `cat_hijo` y asignarle `cat_padre_a` como padre vía `changeParent`

**Test sin impacto (caso simple):**

```js
// cat_hijo no tiene descendientes con productos → cambiar a cat_padre_b directo
CategoryApi.changeParent(hijoId, { parent_id: padreBId, del_opt: 0 })
// → CategoryDTO de cat_hijo con father_id actualizado
```
Verifica: `status 200`, no hay `needs_decision` ni `needs_implementations`, la categoría retornada tiene `id === hijoId`.

**Test con needs_decision (huérfanos del padre anterior):**

```js
// Setup: agregar un atributo a cat_padre_a (que cat_padre_b no tiene)
// y crear un producto en cat_hijo con implementación de ese atributo

// Primera llamada
CategoryApi.changeParent(hijoId, { parent_id: padreBId, del_opt: 0 })
// → { needs_decision: true, impact: [{attribute_key, affected_products:[...]}] }

// Segunda llamada (del_opt=1: inyectar en la categoría)
CategoryApi.changeParent(hijoId, { parent_id: padreBId, del_opt: 1 })
// → CategoryDTO o needs_implementations
```

**Cleanup:**
- Eliminar productos, luego `cat_hijo`, `cat_padre_a`, `cat_padre_b`.
- Eliminar atributos usados (después de eliminar los productos).

> Agregar los IDs creados a la tabla de `ids` global del test runner para el cleanup.
