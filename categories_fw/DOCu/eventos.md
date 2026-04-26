# Eventos de negocio (E1 – E7)

Todos los eventos que pueden alterar la estructura del árbol o las implementaciones de productos usan un **patrón de dos fases**:

1. **Fase 1** — se envía la operación sin `resolution`. Si hay impacto, el backend retorna `{ "status": "impact_pending", ... }`.
2. **Fase 2** — el cliente reenvía la misma operación incluyendo `resolution` con las decisiones del usuario. Si la resolución cubre todo el impacto, el backend ejecuta y retorna `{ "status": "ok" }`.

Si no hay impacto, el backend ejecuta directamente en Fase 1 y retorna `{ "status": "ok" }`.

---

## E1 — Categoría gana padre (era raíz)

Cuando una categoría sin padre pasa a tener uno, los atributos del nuevo padre (y sus ancestros) bajan hacia los productos de la categoría, filtrados por lo que cada rama ya define.

**Endpoint:** `PATCH /categories/{id}/father`

**Fase 1:**
```json
{ "new_father_id": 5 }
```
```json
{
  "status": "impact_pending",
  "impact": [
    {
      "attrs": [{ "id": 3, "key": "garantia", "name": "Garantía" }],
      "products": [{ "id": 10, "code": "P001", "title": "Notebook X" }]
    }
  ]
}
```

**Fase 2:**
```json
{
  "new_father_id": 5,
  "resolution": [
    { "attr_ids": [3], "product_ids": [10], "action": "heredar" }
  ]
}
```
```json
{ "status": "ok" }
```

---

## E2 — Categoría cambia de padre

La categoría ya tenía padre y se mueve a otro. El impacto se calcula como la unión del impacto de salida (attrs que se pierden) y el de entrada (attrs que se ganan).

**Endpoint:** `PATCH /categories/{id}/father`

Mismo contrato que E1. La diferencia está en que `category.father_categorie` ya no es `None`.

---

## E3 — Categoría pierde padre (queda como raíz)

Los atributos heredados del padre actual se pierden y deben resolverse en los productos afectados.

**Endpoint:** `PATCH /categories/{id}/father`

**Fase 1:**
```json
{ "new_father_id": null }
```
```json
{
  "status": "impact_pending",
  "impact": [
    {
      "attrs": [{ "id": 2, "key": "color", "name": "Color" }],
      "products": [{ "id": 7, "code": "C007", "title": "Camisa Azul" }]
    }
  ]
}
```

---

## E4 — Categoría agrega atributo

Al agregar un atributo a una categoría, los productos de sus descendientes que no estén en una rama que ya define ese atributo deberán implementarlo (o eliminarse la referencia).

**Endpoint:** `POST /categories/{id}/attributes/{attr_id}`

**Fase 1:**
```json
{}
```
```json
{
  "status": "impact_pending",
  "impact": [
    {
      "attrs": [{ "id": 7, "key": "talle", "name": "Talle" }],
      "products": [
        { "id": 11, "code": "R011", "title": "Remera Básica" },
        { "id": 12, "code": "R012", "title": "Remera Premium" }
      ]
    }
  ]
}
```

**Fase 2:**
```json
{
  "resolution": [
    { "attr_ids": [7], "product_ids": [11], "action": "eliminar" },
    { "attr_ids": [7], "product_ids": [12], "action": "heredar" }
  ]
}
```

**Acciones disponibles:**

| Acción | Efecto |
|---|---|
| `"eliminar"` | Remueve las implementaciones de esos atributos en esos productos |
| `"heredar"` | Mantiene las implementaciones tal como están |

---

## E5 — Categoría elimina atributo

Simétrico a E4. Los productos afectados son los que están en ramas que no redefinen el atributo.

**Endpoint:** `DELETE /categories/{id}/attributes/{attr_id}`

Mismo contrato de dos fases que E4.

---

## E6 — Producto cambia de categoría

Al mover un producto a otra categoría, el conjunto de atributos estáticos requeridos puede cambiar. El impacto tiene dos partes:

- `to_remove`: attrs estáticos que la nueva categoría no requiere.
- `to_add`: attrs estáticos que la nueva categoría requiere y el producto no tiene.

**Endpoint:** `PATCH /products/{id}/category/{new_category_id}`

**Fase 1:**
```json
{}
```
```json
{
  "status": "impact_pending",
  "to_add": [{ "id": 4, "key": "garantia", "name": "Garantía" }],
  "to_remove": [{ "id": 1, "key": "ram", "name": "RAM" }]
}
```

**Fase 2:**
```json
{
  "resolution": {
    "remove_action": "eliminar",
    "new_implementations": [
      { "attr_id": 4, "value": "2 años" }
    ]
  }
}
```

- `remove_action`: `"eliminar"` o `"heredar"` (aplicado a todos los `to_remove`).
- `new_implementations`: un valor por cada atributo en `to_add` (obligatorio, el backend valida que cubra todos).

---

## E7a — Producto agrega variante

No usa patrón dos fases. El backend valida directamente:

1. **Completitud**: la variante debe implementar exactamente todos los atributos dinámicos requeridos por la categoría del producto.
2. **Unicidad**: no puede existir otra variante con la misma combinación `(attr.key, value)`.

**Endpoint:** `POST /products/{id}/variants`

```json
{
  "attribute_implementations": [
    { "attr_id": 5, "value": "rojo" },
    { "attr_id": 6, "value": "M" }
  ]
}
```

Retorna `{ "status": "ok" }` o HTTP 400 con el detalle del error.

---

## E7b — Producto elimina variante

**Endpoint:** `DELETE /products/{id}/variants/{variant_id}`

Sin body. Retorna `{ "status": "ok" }` o HTTP 404/400.

---

## Validaciones transversales

| Error | Código | Descripción |
|---|---|---|
| Entidad no encontrada | 404 | Categoría, producto, atributo o variante inexistente |
| Ciclo en el árbol | 400 | El nuevo padre es descendiente de la categoría |
| Hijos exclusivos | 400 | Intento de mezclar subcategorías con productos |
| Resolución incompleta | 200 `impact_pending` | La resolución no cubre todos los pares `(attr_id, product_id)` |
| Variante incompleta | 400 | Faltan o sobran atributos dinámicos |
| Variante duplicada | 400 | Ya existe una variante con esa combinación |
