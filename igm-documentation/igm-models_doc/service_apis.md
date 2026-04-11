# Service y APIs

> Documenta la capa de servicio (`service.py`) y la capa HTTP (`server_apis.py`).  
> Para la lógica de negocio de los modelos ver `acciones_reglas_negocio.md`.  
> Para el esquema de BD y repos ver `db_y_repos.md`.

---

## Índice

1. [Arquitectura](#1-arquitectura)
2. [Convenciones de respuesta](#2-convenciones-de-respuesta)
3. [AttributeService](#3-attributeservice)
4. [CategoryService](#4-categoryservice)
5. [ProductService](#5-productservice)
6. [Endpoints HTTP](#6-endpoints-http)
7. [Flujo de operaciones con impacto](#7-flujo-de-operaciones-con-impacto)

---

## 1. Arquitectura

```
HTTP request
    │
    ▼
server_apis.py   ← valida input con Pydantic, convierte errores a HTTP
    │
    ▼
service.py       ← carga modelos, aplica lógica de negocio, persiste cambios
    │
    ▼
*_repo.py        ← serializa/deserializa modelos contra la BD
    │
    ▼
models.py        ← lógica de dominio pura (en memoria)
```

**Regla de separación:**
- `server_apis.py` no toca repos ni modelos directamente.
- `service.py` no sabe nada de HTTP; solo trabaja con objetos Python y raises `ValueError`.
- Los repos no contienen lógica de negocio.

---

## 2. Convenciones de respuesta

### Respuestas HTTP

| Código | Cuándo |
|---|---|
| `200` | Operación exitosa |
| `201` | Recurso creado |
| `400` | Violación de regla de negocio (`ValueError` del service) |
| `404` | Entidad no encontrada |
| `422` | Body inválido (Pydantic) |

### Operaciones con impacto

Cuando una operación requiere datos adicionales del cliente (implementaciones para productos o variantes afectadas), el endpoint retorna `200` con un body especial en vez de ejecutar el cambio:

```json
// necesita implementations → cliente las provee y reintenta
{
  "needs_implementations": true,
  "impact": [
    { "product_id": 1, "product_code": "REMERA-001", "variants": [{"variant_id": 10}, {"variant_id": 11}] }
  ]
}

// necesita decisión (del_attribute con del_opt=0) → cliente elige del_opt y reintenta
{
  "needs_decision": true,
  "impact": [
    { "product_id": 1, "product_code": "REMERA-001" }
  ]
}
```

Cuando la operación completó:

```json
{ "needs_implementations": false, "category": { ... } }
{ "needs_decision": false, "product": { ... } }
```

### Convención del service

Los métodos del service retornan:

| Retorno | Significado |
|---|---|
| Objeto del modelo | Éxito directo |
| `None` | Entidad no encontrada (la API convierte a 404) |
| `{"needs_implementations": True, "impact": [...]}` | Cliente debe proveer implementaciones |
| `{"needs_decision": True, "impact": [...]}` | Cliente debe elegir `del_opt` |
| `ValueError` | Regla de negocio violada (la API convierte a 400) |

---

## 3. AttributeService

### `create(key, name, data_type, is_static, enum_values=[]) → Attribute`

Crea y guarda un nuevo atributo.  
Si `enum_values` se provee, los agrega via `add_enum_value` (lanza `ValueError` si hay duplicados o el tipo no es enum).

### `get(attr_id) → Attribute | None`

Lee un atributo por id.

### `get_all() → list[Attribute]`

Lista todos los atributos.

### `update(attr_id, name=None, enum_values=None) → Attribute | None`

Actualiza `name` y/o reemplaza la lista completa de `enum_values`.  
`enum_values=None` → no modifica los valores actuales.  
`enum_values=[]` → borra todos los valores.

### `delete(attr_id) → bool`

Elimina el atributo. Falla con `ValueError` si hay `atr_implementation` que lo referencian (FK RESTRICT en la BD — hay que borrar los productos primero).

### `add_enum_value(attr_id, value) → Attribute | None`

Agrega un valor posible a un atributo enum. `ValueError` si el atributo no es de tipo enum o el valor ya existe.

---

## 4. CategoryService

### `create(name) → Category`

Crea y guarda una categoría sin atributos.

### `get(cat_id) → Category | None`

Lee la categoría completa: con sus atributos y sus productos directos (incluyendo variantes e implementaciones de cada producto).

### `get_all() → list[Category]`

Lista todas las categorías. Cada una incluye sus atributos y productos.

### `update_name(cat_id, name) → Category | None`

Actualiza solo el nombre.

### `change_parent(cat_id, parent_id, implementations=None, del_opt=0) → dict`

Cambia el padre de la categoría llamando a `Category.change_categorie_father`.

**Flujo:**
1. Carga `cat` y `new_parent`.
2. Convierte `implementations` del formato API al formato esperado por el modelo.
3. Llama `cat.change_categorie_father(new_parent, model_impls, del_opt)`.
4. Si el resultado no es vacío → determina el tipo de impacto y retorna el dict correspondiente.
5. Si es exitoso → guarda todos los productos del subárbol de `cat` (pueden tener nuevas implementaciones) y luego guarda la categoría.

**Tipos de impacto:**

| Retorno | Cuándo |
|---|---|
| `{"needs_decision": True, "impact": [...]}` | `del_opt=0` y hay atributos huérfanos del padre anterior |
| `{"needs_implementations": True, "impact": [...]}` | El nuevo padre tiene atributos que los descendientes no cubren |
| `{"category": Category}` | Éxito |

`impact` para `needs_decision`:
```python
[
  {
    "attribute_key": "color",
    "attribute_name": "Color",
    "is_static": False,
    "affected_products": [{"product_id": 1, "product_code": "REMERA-001"}]
  }
]
```

`impact` para `needs_implementations`:
```python
[
  {
    "attribute_key": "material",
    "attribute_name": "Material",
    "is_static": True,
    "products": [{"product_id": 1, "product_code": "REMERA-001"}]
  },
  {
    "attribute_key": "color",
    "attribute_name": "Color",
    "is_static": False,
    "products": [
      {"product_id": 1, "product_code": "REMERA-001", "variants": [{"variant_id": 10}]}
    ]
  }
]
```

`implementations` (formato API → se convierte internamente a tuplas para el modelo):
```python
{
  "material": [{"product_id": 1, "value": "algodón"}],
  "color":    [{"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]}]
}
```

### `delete(cat_id) → bool`

Elimina la categoría. La BD tiene `ON DELETE RESTRICT` en `product.category_id` — falla si hay productos asociados.

### `add_dynamic_attribute(cat_id, attr_id, product_variant_implementations=None) → dict`

Agrega atributo dinámico (`is_static=False`) a la categoría.

**Flujo:**
1. Carga categoría (con todos sus productos y variantes).
2. Llama `Category.add_dinamic_attribute(attr, implementations)`.
3. Si hay productos que necesitan valor → retorna `needs_implementations=True` con `impact`.
4. Si no hay impacto o se proveyeron implementations válidas → guarda productos afectados, guarda categoría, retorna `needs_implementations=False`.

`product_variant_implementations`:
```python
[
  {
    "product_id": 1,
    "variants": [
      {"variant_id": 10, "value": "rojo"},
      {"variant_id": 11, "value": "azul"}
    ]
  }
]
```

### `add_static_attribute(cat_id, attr_id, implementations=None) → dict`

Agrega atributo estático (`is_static=True`) a la categoría. Mismo flujo que `add_dynamic_attribute`.

`implementations`:
```python
[
  {"product_id": 1, "value": "algodón"},
  {"product_id": 2, "value": "poliéster"}
]
```

### `del_attribute(cat_id, attr_id, del_opt=0) → dict`

Elimina atributo de la categoría.

| `del_opt` | Efecto |
|---|---|
| `0` | Retorna `needs_decision=True` con los productos impactados, **sin modificar nada** |
| `1` | Elimina implementaciones huérfanas en productos (estáticas) y variantes (dinámicas) |
| `2` | Inyecta la definición del atributo directamente en cada producto afectado |

Internamente llama `del_attribute_check_family_impact` antes de `del_attribute` para saber qué productos guardar después.

### `add_product_to_category(cat_id, product_id) → Product`

Reasigna el producto a esta categoría actualizando `product.category_id` en la BD.  
`ValueError` si la categoría tiene subcategorías (no puede tener productos directos).

---

## 5. ProductService

### `create(code, title, price, description, brand, category_id) → Product`

Crea y guarda un producto. La categoría debe existir en la BD.

### `get(prod_id) → Product | None`

Lee producto completo: con categoría (incluyendo sus atributos), atributos propios, implementaciones estáticas y variantes.

### `get_by_code(code) → Product | None`

Lee producto por su código único.

### `get_all() → list[Product]`

Lista todos los productos.

### `update(prod_id, title, price, description, brand, category_id) → Product | None`

Actualiza campos base. Todos los parámetros son opcionales; solo modifica los que se proveen.  
Si `category_id` se pasa, carga la nueva categoría y la asigna.

### `delete(prod_id) → bool`

Elimina producto y limpia sus `atr_implementation` huérfanas (ver `ProductRepo.delete`).

### `add_dynamic_attribute(prod_id, attr_id, variant_options=None) → dict`

Agrega atributo dinámico al producto.

- Si el producto tiene variantes y `variant_options` es `None` → retorna `needs_implementations=True` con los IDs de variantes.
- Si `variant_options` no cubre exactamente todas las variantes → retorna `needs_implementations=True`.
- Si todo es válido → aplica implementaciones a variantes, guarda, retorna producto.

`variant_options`:
```python
[
  {"variant_id": 10, "value": "S"},
  {"variant_id": 11, "value": "M"}
]
```

### `add_implementation(prod_id, attr_id, value) → Product`

Agrega implementación de atributo estático al producto vía `add_product_implementation`.  
El atributo debe estar suscripto en la categoría del producto (o ser un atributo propio estático).  
`ValueError` si el tipo de valor es inválido, el atributo no está suscripto o la implementación ya existe.

### `del_own_attribute(prod_id, attr_key, del_opt=0) → dict`

Elimina atributo propio del producto (solo los que están en `product.attributes`, no los heredados de la categoría).

| `del_opt` | Efecto |
|---|---|
| `0` | Retorna `needs_decision=True` con las implementaciones o variantes afectadas |
| `1` | Elimina implementaciones huérfanas (estáticas o de variantes) |

`ValueError` si `attr_key` no está en `product.attributes`.

### `create_variant(prod_id, implementations) → dict`

Crea una variante del producto.

`implementations` debe cubrir **exactamente** todos los atributos dinámicos del producto (propios + heredados de la categoría).

- Si matchean → crea la variante, guarda, retorna el producto.
- Si no matchean → retorna `{"error": "implementations_invalid", "needed_attributes": [...]}`.

```python
implementations = [
  {"attribute_id": 5, "value": "rojo"},
  {"attribute_id": 6, "value": "M"}
]
```

### `del_variant(prod_id, variant_id) → Product`

Elimina variante del producto. `ValueError` si no existe.

---

## 6. Endpoints HTTP

### Attributes

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/attributes` | Lista todos los atributos |
| `GET` | `/attributes/{id}` | Obtiene un atributo |
| `POST` | `/attributes` | Crea atributo |
| `PATCH` | `/attributes/{id}` | Actualiza nombre y/o enum_values |
| `DELETE` | `/attributes/{id}` | Elimina atributo |
| `POST` | `/attributes/{id}/enum-values` | Agrega valor posible a un enum |

#### POST `/attributes` — body
```json
{
  "key": "color",
  "name": "Color",
  "data_type": "enum",
  "is_static": false,
  "enum_values": ["rojo", "azul", "verde"]
}
```

#### PATCH `/attributes/{id}` — body
```json
{
  "name": "Nuevo nombre",
  "enum_values": ["rojo", "azul", "verde", "amarillo"]
}
```
Todos los campos son opcionales. `enum_values` reemplaza la lista completa.

#### POST `/attributes/{id}/enum-values` — body
```json
{ "value": "violeta" }
```

---

### Categories

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/categories` | Lista todas las categorías (con atributos y productos) |
| `GET` | `/categories/{id}` | Obtiene una categoría |
| `POST` | `/categories` | Crea categoría |
| `PATCH` | `/categories/{id}` | Actualiza nombre |
| `PATCH` | `/categories/{id}/parent` | Cambia el padre de la categoría |
| `DELETE` | `/categories/{id}` | Elimina categoría |
| `POST` | `/categories/{id}/dynamic-attribute` | Agrega atributo dinámico |
| `POST` | `/categories/{id}/static-attribute` | Agrega atributo estático |
| `DELETE` | `/categories/{id}/attributes/{attr_id}` | Elimina atributo (`?del_opt=0`) |
| `POST` | `/categories/{id}/products/{product_id}` | Reasigna producto a esta categoría |

#### PATCH `/categories/{id}/parent`

Primera llamada (del_opt=0, sin implementations):
```json
{ "parent_id": 3 }
```
Respuesta si hay huérfanos del padre anterior:
```json
{
  "needs_decision": true,
  "impact": [
    {
      "attribute_key": "peso",
      "attribute_name": "Peso",
      "is_static": true,
      "affected_products": [{"product_id": 1, "product_code": "REMERA-001"}]
    }
  ]
}
```
Segunda llamada (eligiendo del_opt):
```json
{ "parent_id": 3, "del_opt": 1 }
```
Respuesta si el nuevo padre tiene atributos sin implementations:
```json
{
  "needs_implementations": true,
  "impact": [
    {
      "attribute_key": "color",
      "attribute_name": "Color",
      "is_static": false,
      "products": [
        {"product_id": 1, "product_code": "REMERA-001", "variants": [{"variant_id": 10}]}
      ]
    }
  ]
}
```
Llamada final con implementations:
```json
{
  "parent_id": 3,
  "del_opt": 1,
  "implementations": {
    "color": [
      {"product_id": 1, "variants": [{"variant_id": 10, "value": "rojo"}]}
    ]
  }
}
```
Respuesta exitosa: la categoría actualizada (mismo formato que `GET /categories/{id}`).

| `del_opt` | Efecto sobre atributos huérfanos del padre anterior |
|---|---|
| `0` (default) | Retorna `needs_decision=true` sin modificar nada |
| `1` | Inyecta los atributos huérfanos en la propia categoría |
| `2` | Elimina las implementaciones huérfanas de los productos afectados |

---

#### POST `/categories/{id}/dynamic-attribute`

Primera llamada (sin implementations):
```json
{ "attribute_id": 5 }
```
Respuesta si hay impacto:
```json
{
  "needs_implementations": true,
  "impact": [
    {
      "product_id": 1,
      "product_code": "REMERA-001",
      "variants": [{"variant_id": 10}, {"variant_id": 11}]
    }
  ]
}
```

Segunda llamada (con implementations):
```json
{
  "attribute_id": 5,
  "implementations": [
    {
      "product_id": 1,
      "variants": [
        {"variant_id": 10, "value": "rojo"},
        {"variant_id": 11, "value": "azul"}
      ]
    }
  ]
}
```
Respuesta exitosa:
```json
{ "needs_implementations": false, "category": { ... } }
```

#### POST `/categories/{id}/static-attribute`

```json
{
  "attribute_id": 3,
  "implementations": [
    {"product_id": 1, "value": "algodón"},
    {"product_id": 2, "value": "poliéster"}
  ]
}
```

#### DELETE `/categories/{id}/attributes/{attr_id}?del_opt=0`

| Query param | Efecto |
|---|---|
| `del_opt=0` (default) | Retorna `needs_decision=true` con impacto si hay productos afectados |
| `del_opt=1` | Elimina implementaciones huérfanas |
| `del_opt=2` | Inyecta atributo en productos afectados |

---

### Products

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/products` | Lista todos los productos |
| `GET` | `/products/{id}` | Obtiene un producto |
| `GET` | `/products/by-code/{code}` | Obtiene producto por código |
| `POST` | `/products` | Crea producto |
| `PATCH` | `/products/{id}` | Actualiza campos base |
| `DELETE` | `/products/{id}` | Elimina producto |
| `POST` | `/products/{id}/dynamic-attribute` | Agrega atributo dinámico |
| `POST` | `/products/{id}/implementations` | Agrega implementación estática |
| `DELETE` | `/products/{id}/attributes/{attr_key}` | Elimina atributo propio (`?del_opt=0`) |
| `POST` | `/products/{id}/variants` | Crea variante |
| `DELETE` | `/products/{id}/variants/{variant_id}` | Elimina variante |

#### POST `/products` — body
```json
{
  "code": "REMERA-001",
  "title": "Remera básica",
  "price": 1500.00,
  "description": "Remera de algodón",
  "brand": "MiMarca",
  "category_id": 2
}
```

#### PATCH `/products/{id}` — body
Todos los campos opcionales:
```json
{
  "title": "Remera básica V2",
  "price": 1800.00,
  "category_id": 3
}
```

#### POST `/products/{id}/dynamic-attribute`

Misma lógica de dos llamadas que en categoría:
```json
// primera llamada
{ "attribute_id": 5 }

// si hay variantes → needs_implementations=true con impact=[{"variant_id": 10}, ...]

// segunda llamada
{
  "attribute_id": 5,
  "variant_options": [
    {"variant_id": 10, "value": "S"},
    {"variant_id": 11, "value": "M"}
  ]
}
```

#### POST `/products/{id}/implementations` — body
```json
{ "attribute_id": 3, "value": "algodón" }
```

#### DELETE `/products/{id}/attributes/{attr_key}?del_opt=0`

Igual que en categoría: `del_opt=0` reporta, `del_opt=1` elimina implementaciones.

#### POST `/products/{id}/variants` — body
```json
{
  "implementations": [
    {"attribute_id": 5, "value": "rojo"},
    {"attribute_id": 6, "value": "M"}
  ]
}
```
Si implementations inválidas:
```json
{
  "error": "implementations_invalid",
  "needed_attributes": [ { "key": "color", ... }, { "key": "talle", ... } ]
}
```

---

## 7. Flujo de operaciones con impacto

Las operaciones que pueden afectar productos/variantes ya existentes siguen este patrón:

```
Cliente                          Server
  │                                 │
  │──── POST /op (sin impls) ──────►│
  │                                 │  load → check impact
  │◄─── needs_implementations=true ─│  (sin guardar nada)
  │     impact: [{product_id, ...}] │
  │                                 │
  │  [UI: pide valores al usuario]  │
  │                                 │
  │──── POST /op (con impls) ──────►│
  │                                 │  load → apply → save
  │◄─── needs_implementations=false─│
  │     data: {category/product}    │
```

**Operaciones con este patrón:**

| Operación | Necesita implementations cuando... |
|---|---|
| `POST /categories/{id}/dynamic-attribute` | Hay productos con variantes que no tienen el atributo |
| `POST /categories/{id}/static-attribute` | Hay productos que no tienen el atributo |
| `POST /products/{id}/dynamic-attribute` | El producto tiene variantes |

**Operaciones con `needs_decision`:**

| Operación | Necesita decisión cuando... |
|---|---|
| `DELETE /categories/{id}/attributes/{attr_id}?del_opt=0` | Hay productos que quedarían sin cobertura del atributo |
| `DELETE /products/{id}/attributes/{attr_key}?del_opt=0` | Hay implementaciones huérfanas |
| `PATCH /categories/{id}/parent` (del_opt=0) | El padre anterior aportaba atributos que el nuevo padre no cubre |

> **Nota:** `PATCH /categories/{id}/parent` puede encadenar los dos patrones en secuencia: primero `needs_decision` (atributos huérfanos del padre anterior) y luego `needs_implementations` (atributos nuevos del nuevo padre que necesitan valores). El cliente resuelve uno por llamada.

El cliente elige `del_opt` (1 o 2) y reintenta con el query param correspondiente.
