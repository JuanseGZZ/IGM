# Gestor

Archivo: `Gestor.js`

Capa de reglas de negocio entre `events.js` y `Handler.js`. Mantiene un **árbol espejo** de objetos de dominio (`Category`, `Product`, `Variant`) construido desde el árbol de `Chart`, y expone métodos para validar o analizar cada operación visual antes de que llegue al Handler.

---

## Concepto central: árbol espejo

El árbol de `Chart` (en `Handler`) es la fuente de verdad del estado visual. El árbol espejo del Gestor es un derivado que se **reconstruye en cada análisis** desde el árbol de Charts. No persiste entre operaciones.

```
Árbol de Charts (Handler)           Árbol espejo (Gestor)
────────────────────────            ─────────────────────
Chart(category, model:plain)   →   Category({ name, attributes[] })
  Chart(product, model:plain)  →     Product({ category, ... })
    Chart(variant, model:plain)→       Variant({ impls[] })
```

Las instancias del espejo son objetos de dominio completos que tienen todos los métodos (`get_full_attr_set`, `compute_impact`, `impact_on_*`, etc.).

---

## Construcción del espejo — `buildMirror()`

Retorna `{ cats, prods, vars, catToId, prodToId }`:

| Map | Clave | Valor |
|---|---|---|
| `cats` | `chartId` | instancia `Category` |
| `prods` | `chartId` | instancia `Product` |
| `vars` | `chartId` | instancia `Variant` |
| `catToId` | instancia `Category` | `chartId` |
| `prodToId` | instancia `Product` | `chartId` |

Los mapas inversos (`catToId`, `prodToId`) permiten cruzar resultados de `compute_impact` (que devuelve instancias) de vuelta a IDs de chart para mostrarlos en la UI.

### Reglas del walk

```
chartType === "root"      → recorrer hijos, sin crear instancia
chartType === "category"  → new Category(); si parentCat existe, setear father_categorie
chartType === "product"   → new Product({ category: parentCat }); si no hay parentCat, skip
chartType === "variant"   → new Variant(); si no hay parentProd, skip
```

El espejo refleja el estado actual aunque viole reglas (ej.: una categoría con subcats y productos a la vez). Los métodos de impacto operan sobre lo que existe, no sobre lo que debería existir.

### `toAttr` — reconstrucción de Attribute desde objeto plano

El constructor de `Attribute` inicializa siempre `enum_values = []` y no acepta ese campo como parámetro. `toAttr` lo restaura manualmente después de construir la instancia:

```js
const attr = new Attribute({ key, name, data_type, is_static, id });
attr.enum_values = [...(a.enum_values ?? [])];
```

Esto es necesario para que `analyzeAddProduct`, `analyzeAddVariant` y `analyzeAddAttribute` puedan incluir correctamente las opciones del enum en los `inputs` del dialog.

---

## Formato de respuesta

Todos los métodos `analyze*` y `checkAdd` retornan:

```js
{
  ok:       bool,      // ¿puede continuar la operación?
  blocked:  bool,      // true = error duro, no se puede hacer
  reason:   string,    // mensaje si blocked === true
  flow:     "none" | "additive" | "destructive" | "mixed" | "blocked",
  inputs:   [...],     // ver abajo
  deletions:[...],     // ver abajo
}
```

**`inputs`** — inputs aditivos, uno por atributo×producto:
```js
{
  attr:      Attribute,  // instancia del atributo
  label:     string,     // texto a mostrar en el dialog
  dataType:  string,     // "text" | "number" | "boolean" | "enum"
  options:   string[],   // valores posibles si dataType === "enum"
  hint:      string,     // placeholder del input
  productId: number,     // chartId del producto destino (si aplica)
}
```

**`deletions`** — ítems destructivos, uno por cosa que se pierde:
```js
{
  label:     string,  // descripción legible
  productId: number,  // chartId del producto afectado (si aplica)
  attrKey:   string,  // key del atributo afectado (si aplica)
}
```

---

## API

### `checkAdd(parentChartId, chartType)` — validación estructural

Verifica si el tipo de chart puede agregarse bajo ese padre **antes** de crear el modelo.

| Regla | Blocked si... | Fuente |
|---|---|---|
| `category` | El padre no es `root` ni `category` | Gestor (topología visual) |
| `category` | El padre ya tiene hijos `product` | Dominio: `cat.can_add_subcategory()` |
| `product` | El padre no es `category` | Gestor (topología visual) |
| `product` | El padre ya tiene hijos `category` | Dominio: `cat.can_add_product()` |
| `variant` | El padre no es `product` | Gestor (topología visual) |

Las reglas topológicas las evalúa el Gestor directamente (son reglas del árbol visual, no del modelo de negocio). Las reglas de exclusividad se delegan al dominio mediante los predicados `can_add_subcategory()` / `can_add_product()` que retornan `string|null` sin lanzar excepciones.

---

### `analyzeAddProduct(parentCategoryChartId)`

Analiza agregar un producto a una categoría. Retorna los atributos **estáticos** heredados por el árbol de categorías que el producto deberá implementar.

```
flow: "none"     → la categoría no tiene atributos estáticos
flow: "additive" → hay atributos estáticos → inputs: uno por cada attr
```

Los atributos estáticos vienen de `category.get_full_attr_set()` filtrado por `is_static`.

---

### `analyzeAddVariant(parentProductChartId)`

Analiza agregar una variante a un producto. Retorna los atributos **dinámicos** heredados que la variante deberá implementar.

```
flow: "none"     → no hay atributos dinámicos en la cadena de categorías
flow: "additive" → hay atributos dinámicos → inputs: uno por cada attr
flow: "blocked"  → el padre no es un producto
```

Los atributos dinámicos vienen de `product.category.get_full_attr_set()` filtrado por `!is_static`.

---

### `analyzeAddAttribute(categoryChartId, attrPlain)`

Analiza agregar un atributo a una categoría (llamado desde el modal de edición, antes de confirmar).

**La lógica difiere según el tipo del atributo:**

- `is_static = true` (atributo de **producto**): usa `category.impact_on_add_attribute(attr)` para encontrar qué productos del subárbol deben implementar el valor ahora. Retorna `flow: "additive"` con un input por producto afectado.
- `is_static = false` (atributo de **variante**): busca variantes ya existentes en el subárbol. Si hay, retorna `flow: "additive"` con un input por variante (campo `variantId`). Si no hay variantes todavía, retorna `flow: "none"` — cuando el usuario cree una variante más adelante, `analyzeAddVariant` le pedirá los valores.

```
flow: "none"     → atributo estático sin productos, o dinámico sin variantes en el subárbol
flow: "additive" → atributo estático: inputs con productId, uno por producto afectado
                   atributo dinámico: inputs con variantId, uno por variante existente
```

Cada input incluye `productId` para que el confirm handler pueda guardar la implementación directamente en el modelo del chart producto.

---

### `analyzeRemoveAttribute(categoryChartId, attrPlain)`

Analiza quitar un atributo de una categoría. Busca qué productos en el subárbol tienen una implementación del atributo (por `attribute.key`).

```
flow: "none"        → ningún producto tiene implementación de ese atributo
flow: "destructive" → N productos afectados → deletions: uno por producto
```

Cada deletion incluye `productId` y `attrKey` para que el confirm handler pueda borrar las implementaciones correctas.

---

### `analyzeDelete(chartId)`

Recolecta todos los nodos que se eliminarían en cascada (el nodo y toda su descendencia).

```
flow: "destructive"
deletions: [{ label, type, id }] — uno por nodo eliminado
```

`events.js` usa este análisis para decidir si mostrar un `confirm()` simple (solo el nodo sin hijos) o el dialog del Gestor con la lista completa.

---

### `analyzeMove(fromChartId, toChartId, mode)`

```
mode: "child"   → fromChart pasará a ser hijo de toChart
mode: "sibling" → fromChart pasará a ser hijo del padre de toChart
```

**Paso 1 — Validación**:
- Ciclo: si `mode === "child"` y `toChart` es descendiente de `fromChart` → blocked
- Estructural: `checkAdd(effectiveParentId, fromChart.chartType)`

**Paso 2 — Análisis por tipo**:

| Tipo del nodo movido | Método de análisis |
|---|---|
| `category` | `_analyzeMoveCategory` → `impact_on_add/remove/change_father` |
| `product` | `_analyzeMoveProduct` → ver abajo |
| `variant` | Sin impacto (`flow: "none"`) |

**`_analyzeMoveProduct` — doble análisis**:

Cuando se mueve un producto a una nueva categoría se analizan dos capas por separado:

1. **Atributos estáticos** (implementaciones del producto) — vía `impact_on_change_category`:
   - Attrs estáticos que la nueva categoría requiere y el producto no tiene → `inputs` (aditivo)
   - Attrs estáticos que el producto tiene y la nueva categoría no requiere → `deletions` (destructivo)

2. **Atributos dinámicos** (implementaciones de las variantes hijas) — comparación por `key` entre los attrs dinámicos de la categoría actual y la nueva:
   - Keys dinámicos que las variantes implementan pero la nueva categoría no requiere → `deletions` con `variantId` (destructivo)
   - Attrs dinámicos que la nueva categoría requiere y las variantes actuales no tienen → `inputs` con `variantId` (aditivo)

La comparación dinámica se hace por `key` (no por identidad de `AttributeSet`) porque las instancias de `Attribute` vienen de dos mirrors distintos y sin `id` asignado no son comparables por referencia.

**Flows posibles**:

```
"none"        → sin impacto en atributos
"additive"    → attrs nuevos que producto/variantes deben implementar
"destructive" → implementaciones de producto/variante que se pierden
"mixed"       → ambos (ej: categoría cambia de padre, pierde unos attrs y gana otros)
"blocked"     → la operación no es válida estructuralmente
```

**Campos de `inputs` y `deletions` extendidos**:

```js
// Input de variante (nuevo campo variantId en vez de productId)
{ attr, label, dataType, options, hint, variantId: number }

// Deletion de variante
{ label, attrKey, variantId: number }
```

`applyAdditiveFilled` y `applyDestructiveDeletions` en `events.js` distinguen entre `productId` y `variantId` para aplicar el cambio en el nodo correcto.

---

## Tres flujos de UX

### Flujo aditivo

La operación requiere que el usuario complete implementaciones faltantes.

```
showGestorDialog({
  title:       "...",
  description: "Completá los valores:",
  inputs:      analysis.inputs,
  onConfirm: (filled) => {
    // filled = [{ ...inputSpec, value }]
    // guardar value en el model del producto correspondiente
    doAction();
  }
})
```

**Dónde ocurre**:
- Agregar producto a categoría con atributos estáticos
- Agregar variante a producto con atributos dinámicos (de variante)
- Agregar atributo **estático** a una categoría con productos en el subárbol
- Mover categoría/producto a nueva posición que incorpora atributos estáticos

---

### Flujo destructivo

La operación elimina cosas existentes. El usuario debe ver exactamente qué se borrará y confirmar.

```
showGestorDialog({
  title:        "Eliminar ...",
  description:  "Se eliminarán N elementos:",
  deletions:    analysis.deletions,
  confirmLabel: "Eliminar todo",
  onConfirm: () => doAction()
})
```

**Dónde ocurre**:
- Eliminar un nodo con descendientes
- Quitar atributo de una categoría cuando productos tienen esa implementación
- Mover categoría/producto perdiendo atributos

---

### Flujo mixto

La misma operación tiene parte aditiva y parte destructiva. El dialog muestra ambas secciones.

```
showGestorDialog({
  inputs:    analysis.inputs,    // sección aditiva
  deletions: analysis.deletions, // sección destructiva
  onConfirm: (filled) => {
    applyAdditiveFilled(filled);
    applyDestructiveDeletions(analysis.deletions);
    doAction();
  }
})
```

**Dónde ocurre**:
- Mover una categoría que pierde atributos de su padre anterior y gana atributos del nuevo

---

## Integración en `events.js`

```
igm-add-chart
  → gestor.checkAdd(parentId, chartType)         // ¿se puede?
  → createModel(chartType)                        // basic info (prompts)
  → gestor.analyzeAddProduct/AddVariant(parentId) // ¿qué falta?
  → showGestorDialog (si flow !== "none")
  → layoutActors.add(...)

delete button click
  → gestor.analyzeDelete(id)
  → confirm() simple (sin hijos) o showGestorDialog (con hijos)
  → layoutActors.deleteNode(id)

drag & drop
  → gestor.analyzeMove(fromId, toId, mode)
  → alert(reason) si blocked
  → showGestorDialog (si flow !== "none")
  → layoutActors.moveToChild/Sibling(...)

picker Confirmar (modal categoría)
  → diff added/removed entre pickerSelection y pendingAttrs
  → gestor.analyzeAddAttribute(editingChart.id, attr) por cada attr agregado
  → showGestorDialog (si flow === "additive")
  → pendingAttrs.push(attr)

attr × button (modal categoría)
  → gestor.analyzeRemoveAttribute(editingChart.id, attr)
  → showGestorDialog (si flow === "destructive")
  → pendingAttrs.splice(idx, 1)
```

---

## Limitaciones actuales (MVP)

- Los atributos estáticos en los modelos de productos se guardan como objetos planos (no instancias de `Attribute`). El campo `attributes_implementations` existe en el modelo pero no se usa en el render visual de las cartas producto.
- La variante no tiene render de implementaciones completo; solo muestra las que ya existen en el modelo.
- Para movimientos de categoría, el análisis aplica implementaciones aditivas en los productos pero no elimina automáticamente las destructivas del modelo (solo las borra si el usuario lo confirma explícitamente desde el dialog).
