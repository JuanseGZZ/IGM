# Referencia de API

Base URL: `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

Todos los endpoints aceptan y retornan `application/json`.

---

## GET /categories

Lista todas las categorías en orden plano. El frontend ensambla el árbol en cliente.

**Response:** `CategoryOut[]`
```json
[
  {
    "id": 1,
    "name": "Electrónica",
    "father_id": null,
    "attributes": [
      { "id": 3, "key": "garantia", "name": "Garantía", "data_type": "text", "is_static": true, "enum_values": [] }
    ]
  }
]
```

---

## GET /attributes

Lista todos los atributos del sistema.

**Response:** `AttributeOut[]`
```json
[
  { "id": 1, "key": "color", "name": "Color", "data_type": "enum", "is_static": false, "enum_values": ["rojo", "azul"] }
]
```

---

## GET /products

Lista productos. Se puede filtrar por categoría.

**Query params:**

| Param | Tipo | Descripción |
|---|---|---|
| `category_id` | `int` (opcional) | Filtra por categoría |

**Response:** `ProductOut[]` (sin variantes, solo datos básicos)

---

## GET /products/{id}

Detalle completo de un producto con implementaciones y variantes.

**Response:** `ProductOut`
```json
{
  "id": 10,
  "code": "NB001",
  "title": "Notebook X",
  "price": 999.99,
  "description": "...",
  "brand": "Marca",
  "category_id": 4,
  "attributes_implementations": [
    { "id": 1, "attribute": { "id": 3, "key": "garantia", ... }, "value": "1 año" }
  ],
  "variants": [
    {
      "id": 5,
      "attribute_implementations": [
        { "id": 2, "attribute": { "id": 7, "key": "color", ... }, "value": "negro" }
      ]
    }
  ]
}
```

---

## POST /categories

Crea una nueva categoría.

**Body:** `CreateCategoryRequest`
```json
{
  "name": "Notebooks",
  "father_id": 1,
  "attribute_ids": [3, 7]
}
```

- `father_id`: opcional (`null` = raíz)
- `attribute_ids`: lista de IDs de atributos a asociar inicialmente

**Response:** `CategoryOut`  
**Errores:** 404 si el padre o algún atributo no existe; 400 si viola ciclo o exclusividad.

---

## POST /attributes

Crea un nuevo atributo.

**Body:** `CreateAttributeRequest`
```json
{
  "key": "talle",
  "name": "Talle",
  "data_type": "enum",
  "is_static": false,
  "enum_values": ["S", "M", "L", "XL"]
}
```

- `enum_values` solo se usa si `data_type == "enum"`; ignorado en otro caso.

**Response:** `AttributeOut`

---

## POST /products

Crea un nuevo producto (sin implementaciones ni variantes).

**Body:** `CreateProductRequest`
```json
{
  "code": "NB001",
  "title": "Notebook X",
  "price": 999.99,
  "description": "Descripción opcional",
  "brand": "Marca",
  "category_id": 4
}
```

**Response:** `ProductOut`  
**Errores:** 404 si la categoría no existe; 400 si la categoría ya tiene subcategorías.

---

## DELETE /categories/{id}

Elimina una categoría y todas sus relaciones (cascade en DB).

**Response:** `{ "status": "ok" }`  
**Errores:** 404 si no existe.

---

## DELETE /attributes/{id}

Elimina un atributo global.

**Response:** `{ "status": "ok" }`  
**Errores:** 404 si no existe.

---

## DELETE /products/{id}

Elimina un producto y todas sus variantes.

**Response:** `{ "status": "ok" }`  
**Errores:** 404 si no existe.

---

## PATCH /categories/{id}/father — E1/E2/E3

Cambia (o quita) el padre de una categoría. Usa patrón dos fases.

Ver [eventos.md](eventos.md) para ejemplos completos de cada caso.

**Body:** `ChangeFatherRequest`
```json
{
  "new_father_id": 5,
  "resolution": null
}
```

- `new_father_id: null` = quitar padre (E3)
- `resolution: null` = Fase 1 (solo calcula impacto)

**Response:** `ImpactResponse | SuccessResponse`

---

## POST /categories/{id}/attributes/{attr_id} — E4

Agrega un atributo a una categoría. Usa patrón dos fases.

**Body:** `AddAttributeRequest`
```json
{ "resolution": null }
```

**Response:** `ImpactResponse | SuccessResponse`

---

## DELETE /categories/{id}/attributes/{attr_id} — E5

Elimina un atributo de una categoría. Usa patrón dos fases.

**Body:** `RemoveAttributeRequest`
```json
{ "resolution": null }
```

**Response:** `ImpactResponse | SuccessResponse`

---

## PATCH /products/{id}/category/{new_cat_id} — E6

Mueve un producto a otra categoría. Usa patrón dos fases con contrato distinto.

Ver [eventos.md](eventos.md) para el ejemplo completo.

**Body:** `ChangeCategoryRequest`
```json
{ "resolution": null }
```

**Response:** `ChangeCategoryImpactResponse | SuccessResponse`

---

## POST /products/{id}/variants — E7a

Agrega una variante al producto. Sin patrón dos fases.

**Body:** `AddVariantRequest`
```json
{
  "attribute_implementations": [
    { "attr_id": 5, "value": "rojo" },
    { "attr_id": 6, "value": "M" }
  ]
}
```

**Response:** `SuccessResponse`  
**Errores:** 400 si la variante es incompleta o duplicada.

---

## DELETE /products/{id}/variants/{variant_id} — E7b

Elimina una variante.

**Response:** `SuccessResponse`  
**Errores:** 404 si la variante no existe; 400 si no pertenece al producto.

---

## Schemas de respuesta comunes

### ImpactResponse
```json
{
  "status": "impact_pending",
  "message": "...",
  "impact": [
    {
      "attrs": [{ "id": 1, "key": "color", "name": "Color" }],
      "products": [{ "id": 7, "code": "C007", "title": "Camisa" }]
    }
  ]
}
```

### SuccessResponse
```json
{ "status": "ok" }
```

### ChangeCategoryImpactResponse
```json
{
  "status": "impact_pending",
  "message": "...",
  "to_add": [{ "id": 4, "key": "garantia", "name": "Garantía" }],
  "to_remove": [{ "id": 1, "key": "ram", "name": "RAM" }]
}
```
