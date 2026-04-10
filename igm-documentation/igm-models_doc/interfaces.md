# Interfaces y Contratos de API — IGM

> Este documento centraliza **todas las estructuras de datos** (entrada y salida) del sistema IGM.  
> Está orientado a que un agente LLM pueda diseñar el frontend con información completa de qué envía y qué recibe en cada operación.  
> Para lógica de negocio interna ver `acciones_reglas_negocio.md`. Para DB y repos ver `db_y_repos.md`. Para detalle de servicios ver `service_apis.md`.

---

## Índice

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [Entidades del sistema de negocio](#2-entidades-del-sistema-de-negocio)
   - [Customer](#21-customer)
   - [Plan](#22-plan)
   - [Subscription](#23-subscription)
   - [Shop](#24-shop)
   - [Product (simple)](#25-product-simple)
   - [Client](#26-client)
   - [Order](#27-order)
   - [Line](#28-line)
   - [JWT](#29-jwt)
3. [Endpoints del sistema de negocio](#3-endpoints-del-sistema-de-negocio)
4. [Auth — flujo de tokens JWT](#4-auth--flujo-de-tokens-jwt)
5. [Entidades del catálogo de productos](#5-entidades-del-catálogo-de-productos)
   - [Attribute](#51-attribute)
   - [Category](#52-category)
   - [Product (complejo)](#53-product-complejo)
   - [Variant](#54-variant)
   - [AttributeImplementation](#55-attributeimplementation)
6. [Endpoints del catálogo de productos](#6-endpoints-del-catálogo-de-productos)
   - [Attributes](#61-attributes)
   - [Categories](#62-categories)
   - [Products (catálogo)](#63-products-catálogo)
7. [Convenciones de respuesta](#7-convenciones-de-respuesta)
8. [Patrones de respuesta especiales](#8-patrones-de-respuesta-especiales)

---

## 1. Arquitectura del sistema

El sistema tiene **dos capas**:

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA DE NEGOCIO (implementada en back_igm/core/)           │
│                                                             │
│  Customer ──► Subscription ──► Shop                        │
│                                    ├── Products (simples)  │
│                                    ├── Clients             │
│                                    │       └── Orders      │
│                                    │               └── Lines│
│                                    └── (JWT por usuario)   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  CAPA DE CATÁLOGO DE PRODUCTOS (documentada, en desarrollo) │
│                                                             │
│  Category ──► Products (ricos)                             │
│      │            ├── Attributes (estáticos)               │
│      │            ├── AttributeImplementations             │
│      └── Attributes     └── Variants                       │
│          (dinámicos)         └── AttributeImplementations  │
└─────────────────────────────────────────────────────────────┘
```

**Flujo HTTP:**
```
Request → API (FastAPI / Pydantic) → Service → Repository → DB (PostgreSQL)
```

---

## 2. Entidades del sistema de negocio

### 2.1 Customer

El **dueño del negocio** que se suscribe a IGM y administra una tienda (Shop).

```json
{
  "id": 1,
  "name": "Juan",
  "surname": "Pérez",
  "email": "juan@mail.com",
  "mp_associated": 123456,
  "subscription": [ /* array de Subscription */ ],
  "jwt": {
    "at": "<access_token>",
    "rt": "<refresh_token>"
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK, auto-generado |
| `name` | `string` | Nombre |
| `surname` | `string` | Apellido |
| `email` | `string` | Email único |
| `mp_associated` | `int` | ID cuenta Mercado Pago asociada |
| `subscription` | `Subscription[]` | Suscripciones activas/históricas |
| `jwt` | `JWT` | Par de tokens de sesión |

**Tabla DB:** `customers`

---

### 2.2 Plan

Plan de suscripción disponible en IGM.

```json
{
  "id": "plan_basico",
  "name": "Básico",
  "upTo": 100,
  "downTo": 0,
  "costPerProducts": 500
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | PK |
| `name` | `string` | Nombre del plan |
| `upTo` | `int` | Límite superior de productos |
| `downTo` | `int` | Límite inferior de productos |
| `costPerProducts` | `int` | Costo por producto (en la moneda del sistema) |

**Tabla DB:** `plans` (columnas: `up_to`, `down_to`, `cost_per_products` en snake_case)

---

### 2.3 Subscription

Vincula un `Customer` con un `Plan` y una `Shop`. Una suscripción = una tienda activa.

```json
{
  "id": "sub_abc123",
  "shop": { /* objeto Shop */ },
  "plan": { /* objeto Plan */ },
  "cantProducts": 47,
  "state": 1,
  "until_date": "2025-12-31T23:59:59Z"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | PK |
| `shop` | `Shop` | Tienda asociada (objeto completo) |
| `plan` | `Plan` | Plan contratado (objeto completo) |
| `cantProducts` | `int` | Cantidad de productos actuales en la tienda |
| `state` | `int` | `0` = waiting, `1` = paid, `2` = expired |
| `until_date` | `datetime` | Fecha de vencimiento (ISO 8601 con timezone) |

> **Nota:** `state` se guarda como índice entero y se mapea en la app a `STATE = ["waiting", "paid", "expired"]`.

**Tabla DB:** `subscriptions` (columnas: `cant_products`, `until_date`, `state` TEXT con CHECK)

---

### 2.4 Shop

La tienda que administra el `Customer`.

```json
{
  "id": "shop_xyz",
  "name": "Mi Tienda Online",
  "products": [ /* array de Product */ ],
  "clients": [ /* array de Client */ ]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | PK |
| `name` | `string` | Nombre de la tienda |
| `products` | `Product[]` | Productos del catálogo |
| `clients` | `Client[]` | Clientes registrados en la tienda |

**Tabla DB:** `shops`

---

### 2.5 Product (simple)

El producto básico de la tienda (sin atributos ni variantes).

```json
{
  "id": "prod_001",
  "title": "Remera Azul Talle M",
  "price": 1500.00,
  "description": "Remera de algodón 100%",
  "image_url": "https://cdn.example.com/remera-azul.jpg"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | PK |
| `title` | `string` | Nombre del producto |
| `price` | `float` | Precio (NUMERIC 12,2, ≥ 0) |
| `description` | `string` | Descripción |
| `image_url` | `string` | URL de imagen |

**Tabla DB:** `products` (tiene además `shop_id` FK)

---

### 2.6 Client

El **comprador** que usa la tienda de un Customer.

```json
{
  "id": 1,
  "name": "María García",
  "email": "maria@mail.com",
  "orders": [ /* array de Order */ ],
  "jwt": {
    "at": "<access_token>",
    "rt": "<refresh_token>"
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK, BIGSERIAL auto-generado |
| `name` | `string` | Nombre completo |
| `email` | `string` | Email único |
| `orders` | `Order[]` | Historial de pedidos |
| `jwt` | `JWT` | Par de tokens de sesión |

**Tabla DB:** `clients` (tiene además `shop_id` FK)

---

### 2.7 Order

Pedido creado por un `Client`.

```json
{
  "id": "order_20240101_abc",
  "client_email": "maria@mail.com",
  "client_id": 1,
  "status": "pending",
  "lines": [ /* array de Line */ ],
  "currency": "ARS"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `string` | PK |
| `client_email` | `string` | Email del cliente |
| `client_id` | `int` | FK → Client |
| `status` | `string` | `"pending"` \| `"paid"` \| `"canceled"` \| `"expired"` |
| `lines` | `Line[]` | Líneas del pedido |
| `currency` | `string` | `"ARS"` \| `"USD"` |

**Tabla DB:** `orders`

---

### 2.8 Line

Una línea dentro de un pedido (producto + cantidad).

```json
{
  "id": 1,
  "product": { /* objeto Product */ },
  "quantity": 3
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK, BIGSERIAL |
| `product` | `Product` | Producto (objeto completo) |
| `quantity` | `int` | Cantidad (> 0) |

**Tabla DB:** `order_lines` (UNIQUE en `order_id + product_id` — si se agrega el mismo producto, se suma quantity)

---

### 2.9 JWT

Par de tokens de autenticación. Se incluye dentro de `Customer` y `Client`.

```json
{
  "at": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImsxIn0...",
  "rt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImsxIn0..."
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `at` | `string` | Access Token (JWT firmado HS256) |
| `rt` | `string` | Refresh Token (JWT firmado HS256) |

**Payload del Access Token:**
```json
{
  "sub": "usuario@mail.com",
  "rango": "client",
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900,
  "kid": "k1",
  "jti": "a1b2c3d4"
}
```

| Campo | Descripción |
|---|---|
| `sub` | Email del usuario |
| `rango` | `"client"` (comprador) o `"customer"` (dueño de tienda) |
| `type` | `"access"` |
| `exp` | Expiración: `iat + 900s` (15 min) |

**TTL:** AT = 15 minutos · RT = 7 días  
**Tabla DB:** `jwts` (1-1 con customer O con client, no ambos)

---

## 3. Endpoints del sistema de negocio

> Los endpoints actuales son stubs en desarrollo. Esta tabla muestra la interfaz esperada basada en los modelos implementados.

### `/api/users` — Usuarios genéricos (stub)

| Método | Path | Body entrada | Respuesta |
|---|---|---|---|
| `GET` | `/api/users/` | — | `User[]` |
| `GET` | `/api/users/{id}` | — | `User` o 404 |
| `POST` | `/api/users/` | `{ id, name, email }` | `User` |

> **Nota:** Estos endpoints son placeholders. Los endpoints de Customer y Client deberían tener su propia ruta.

### `/api/products` — Productos (stub)

| Método | Path | Body entrada | Respuesta |
|---|---|---|---|
| `GET` | `/api/products/` | — | `Product[]` |
| `GET` | `/api/products/{id}` | — | `Product` o 404 |
| `POST` | `/api/products/` | `{ id, name, price }` | `Product` |

### Auth — JwtCRUD

| Operación | Entrada | Salida |
|---|---|---|
| **Issue** (login) | `user: string, rango: string` | `{ at: string, rt: string }` |
| **Validate** (verificar AT) | `access_token: string` | Payload del token o error |
| **Refresh** (rotar tokens) | `user: string, refresh_token: string` | `{ at: string, rt: string }` nuevo |
| **Revoke** (logout) | `user: string` | vacío |

### Order Lines — operaciones especiales

| Operación | Entrada | Salida |
|---|---|---|
| **Upsert line** | `order_id, product_id, quantity` | Fila actualizada o creada |
| **List by order** | `order_id, limit=200, offset=0` | `Line[]` |

### Queries adicionales

| CRUD | Operación extra | Parámetros |
|---|---|---|
| `CrudOrders` | `list_by_client` | `client_id, limit=50, offset=0` |
| `CrudClients` | `list_by_shop` | `shop_id, limit=50, offset=0` |
| `CrudProducts` | `list_by_shop` | `shop_id, limit=50, offset=0` |
| `CrudSubscriptions` | `list_by_customer` | `customer_id, limit=50, offset=0` |
| `CrudSubscriptions` | `get_by_shop` | `shop_id` |

---

## 4. Auth — flujo de tokens JWT

```
Cliente                                Servidor
  │                                       │
  │──── POST /auth/login ────────────────►│
  │     { email, password }               │  valida credencial
  │◄─── { at, rt } ─────────────────────-│  issue(user, rango)
  │                                       │
  │  [guarda at y rt en storage]          │
  │                                       │
  │──── GET /api/resource ───────────────►│
  │     Authorization: Bearer <at>        │  validate(at) → payload
  │◄─── data ────────────────────────────│
  │                                       │
  │  [at expira a los 15 min]             │
  │                                       │
  │──── POST /auth/refresh ─────────────►│
  │     { user: email, refresh_token: rt }│  refresh(user, rt) → nuevo par
  │◄─── { at, rt } (nuevos) ────────────│  rota AT + RT
  │                                       │
  │  [logout]                             │
  │──── POST /auth/logout ──────────────►│
  │     { user: email }                   │  revoke(user) → borra sesión
  │◄─── ok ─────────────────────────────│
```

**Rangos posibles:**
- `"customer"` — dueño de tienda (puede gestionar shop, productos, clientes)
- `"client"` — comprador (puede ver productos y hacer pedidos)

---

## 5. Entidades del catálogo de productos

> Sistema más rico para gestión de catálogos con atributos personalizables y variantes.

### 5.1 Attribute

Definición de un atributo (característica) que puede tener un producto o variante.

```json
{
  "id": 5,
  "key": "color",
  "name": "Color",
  "data_type": "enum",
  "is_static": false,
  "enum_values": ["rojo", "azul", "verde", "negro"]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK auto-generado |
| `key` | `string` | Identificador único (ej: `"color"`, `"peso"`) |
| `name` | `string` | Nombre legible |
| `data_type` | `string` | `"text"` \| `"number"` \| `"boolean"` \| `"enum"` |
| `is_static` | `bool` | `true` = atributo de producto / `false` = atributo de variante |
| `enum_values` | `string[]` | Solo si `data_type == "enum"`. Valores posibles |

**Tabla DB:** `atribute` + `enum_values`

---

### 5.2 Category

Categoría que agrupa productos y puede tener atributos compartidos.

```json
{
  "id": 2,
  "name": "Ropa",
  "attributes": [
    { /* Attribute */ }
  ],
  "products": [
    { /* Product (complejo) */ }
  ]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK auto-generado |
| `name` | `string` | Nombre de la categoría |
| `attributes` | `Attribute[]` | Atributos definidos en esta categoría (heredables) |
| `products` | `Product[]` | Productos directamente en esta categoría |

> **Regla:** una categoría no puede tener subcategorías y productos al mismo tiempo.  
> El árbol padre-hijo **no se persiste en DB** — solo existe en memoria.

**Tabla DB:** `category` + `category_atributes` (join table)

---

### 5.3 Product (complejo)

Producto del catálogo con atributos, implementaciones y variantes.

```json
{
  "id": 1,
  "code": "REMERA-001",
  "title": "Remera básica",
  "price": 1500.00,
  "description": "Remera de algodón 100%",
  "brand": "MiMarca",
  "category_id": 2,
  "category": { /* Category (con sus atributos) */ },
  "attributes": [
    { /* Attribute (propios del producto, dinámicos) */ }
  ],
  "attributes_implementations": [
    { /* AttributeImplementation (atributos estáticos implementados) */ }
  ],
  "variants": [
    { /* Variant */ }
  ]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK auto-generado |
| `code` | `string` | Código único (ej: `"REMERA-001"`) |
| `title` | `string` | Título |
| `price` | `float` | Precio |
| `description` | `string` | Descripción |
| `brand` | `string` | Marca |
| `category_id` | `int` | FK → Category |
| `category` | `Category` | Categoría con sus atributos |
| `attributes` | `Attribute[]` | Atributos **propios** del producto (dinámicos) |
| `attributes_implementations` | `AttributeImplementation[]` | Valores de atributos **estáticos** |
| `variants` | `Variant[]` | Variantes del producto |

**Tabla DB:** `product` + `products_atributes` (join) + `product_implementation` + `atr_implementation`

---

### 5.4 Variant

Una combinación específica de atributos dinámicos de un producto (ej: color Rojo + talle M).

```json
{
  "id": 10,
  "attribute_implementations": [
    { /* AttributeImplementation */ }
  ]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK auto-generado |
| `attribute_implementations` | `AttributeImplementation[]` | Valores de los atributos dinámicos |

> El código de variante (`REMERA-001-v1`, etc.) lo genera el repo, no el modelo.

**Tabla DB:** `variant` + `variant_implementation` + `atr_implementation`

---

### 5.5 AttributeImplementation

Un valor concreto de un atributo sobre un producto o variante.

```json
{
  "id": 55,
  "attribute": { /* Attribute */ },
  "value": "rojo"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int` | PK (el de `atr_implementation` en DB) |
| `attribute` | `Attribute` | El atributo que se implementa |
| `value` | `string` | Valor (siempre string, la app castea según `data_type`) |

**Tabla DB:** `atr_implementation`

---

## 6. Endpoints del catálogo de productos

### Convención de códigos HTTP

| Código | Cuándo |
|---|---|
| `200` | Operación exitosa |
| `201` | Recurso creado |
| `400` | Violación de regla de negocio |
| `404` | Entidad no encontrada |
| `422` | Body inválido (Pydantic) |

---

### 6.1 Attributes

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/attributes` | Lista todos los atributos |
| `GET` | `/attributes/{id}` | Obtiene un atributo |
| `POST` | `/attributes` | Crea atributo |
| `PATCH` | `/attributes/{id}` | Actualiza nombre y/o enum_values |
| `DELETE` | `/attributes/{id}` | Elimina atributo |
| `POST` | `/attributes/{id}/enum-values` | Agrega valor a un atributo enum |

#### POST `/attributes` — crear atributo

**Request body:**
```json
{
  "key": "color",
  "name": "Color",
  "data_type": "enum",
  "is_static": false,
  "enum_values": ["rojo", "azul", "verde"]
}
```

| Campo | Obligatorio | Descripción |
|---|---|---|
| `key` | sí | Identificador único |
| `name` | sí | Nombre legible |
| `data_type` | sí | `"text"` \| `"number"` \| `"boolean"` \| `"enum"` |
| `is_static` | sí | `true` = estático (producto), `false` = dinámico (variante) |
| `enum_values` | no | Solo si `data_type == "enum"` |

**Respuesta 201:**
```json
{ /* Attribute completo */ }
```

---

#### PATCH `/attributes/{id}` — actualizar atributo

**Request body (todos opcionales):**
```json
{
  "name": "Nuevo nombre",
  "enum_values": ["rojo", "azul", "amarillo"]
}
```

> `enum_values` **reemplaza la lista completa** (no hace merge).  
> `enum_values: []` borra todos los valores.

**Respuesta 200:**
```json
{ /* Attribute actualizado */ }
```

---

#### POST `/attributes/{id}/enum-values` — agregar valor enum

**Request body:**
```json
{ "value": "violeta" }
```

**Respuesta 200:**
```json
{ /* Attribute con el nuevo valor agregado */ }
```

---

### 6.2 Categories

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/categories` | Lista todas las categorías (con atributos y productos) |
| `GET` | `/categories/{id}` | Obtiene una categoría completa |
| `POST` | `/categories` | Crea categoría |
| `PATCH` | `/categories/{id}` | Actualiza nombre |
| `DELETE` | `/categories/{id}` | Elimina categoría |
| `POST` | `/categories/{id}/dynamic-attribute` | Agrega atributo dinámico a la categoría |
| `POST` | `/categories/{id}/static-attribute` | Agrega atributo estático a la categoría |
| `DELETE` | `/categories/{id}/attributes/{attr_id}` | Elimina atributo de la categoría |
| `POST` | `/categories/{id}/products/{product_id}` | Reasigna producto a esta categoría |

---

#### POST `/categories` — crear categoría

**Request body:**
```json
{ "name": "Ropa" }
```

**Respuesta 201:**
```json
{ "id": 2, "name": "Ropa", "attributes": [], "products": [] }
```

---

#### PATCH `/categories/{id}` — actualizar nombre

**Request body:**
```json
{ "name": "Ropa y Calzado" }
```

**Respuesta 200:** `Category` actualizada.

---

#### POST `/categories/{id}/dynamic-attribute` — agregar atributo dinámico

Flujo de **dos llamadas** cuando hay productos con variantes existentes.

**Primera llamada (sin implementations):**
```json
{ "attribute_id": 5 }
```

**Respuesta si hay productos impactados (200):**
```json
{
  "needs_implementations": true,
  "impact": [
    {
      "product_id": 1,
      "product_code": "REMERA-001",
      "variants": [
        { "variant_id": 10 },
        { "variant_id": 11 }
      ]
    }
  ]
}
```
> El frontend debe pedir al usuario los valores para cada variante de cada producto afectado.

**Segunda llamada (con implementations):**
```json
{
  "attribute_id": 5,
  "implementations": [
    {
      "product_id": 1,
      "variants": [
        { "variant_id": 10, "value": "rojo" },
        { "variant_id": 11, "value": "azul" }
      ]
    }
  ]
}
```

**Respuesta exitosa (200):**
```json
{
  "needs_implementations": false,
  "category": { /* Category completa */ }
}
```

---

#### POST `/categories/{id}/static-attribute` — agregar atributo estático

Similar al dinámico pero el impacto es a nivel producto (no variante).

**Primera llamada (sin implementations):**
```json
{ "attribute_id": 3 }
```

**Respuesta si hay productos impactados:**
```json
{
  "needs_implementations": true,
  "impact": [
    { "product_id": 1, "product_code": "REMERA-001" },
    { "product_id": 2, "product_code": "PANTALON-001" }
  ]
}
```

**Segunda llamada (con implementations):**
```json
{
  "attribute_id": 3,
  "implementations": [
    { "product_id": 1, "value": "algodón" },
    { "product_id": 2, "value": "poliéster" }
  ]
}
```

**Respuesta exitosa:**
```json
{
  "needs_implementations": false,
  "category": { /* Category completa */ }
}
```

---

#### DELETE `/categories/{id}/attributes/{attr_id}?del_opt=0` — eliminar atributo de categoría

**Query param `del_opt`:**

| Valor | Efecto |
|---|---|
| `0` (default) | Solo reporta el impacto, no modifica nada |
| `1` | Elimina implementaciones huérfanas en productos afectados |
| `2` | Inyecta el atributo directamente en cada producto afectado (migra el atributo al producto) |

**Respuesta con `del_opt=0` si hay impacto (200):**
```json
{
  "needs_decision": true,
  "impact": [
    { "product_id": 1, "product_code": "REMERA-001" }
  ]
}
```
> El frontend muestra las opciones al usuario, que elige `del_opt=1` o `del_opt=2` y reintenta.

**Respuesta exitosa (200):**
```json
{
  "needs_decision": false,
  "category": { /* Category actualizada */ }
}
```

---

### 6.3 Products (catálogo)

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/products` | Lista todos los productos |
| `GET` | `/products/{id}` | Obtiene un producto completo |
| `GET` | `/products/by-code/{code}` | Obtiene producto por código |
| `POST` | `/products` | Crea producto |
| `PATCH` | `/products/{id}` | Actualiza campos base |
| `DELETE` | `/products/{id}` | Elimina producto |
| `POST` | `/products/{id}/dynamic-attribute` | Agrega atributo dinámico al producto |
| `POST` | `/products/{id}/implementations` | Agrega implementación de atributo estático |
| `DELETE` | `/products/{id}/attributes/{attr_key}` | Elimina atributo propio del producto |
| `POST` | `/products/{id}/variants` | Crea variante del producto |
| `DELETE` | `/products/{id}/variants/{variant_id}` | Elimina variante |

---

#### POST `/products` — crear producto

**Request body:**
```json
{
  "code": "REMERA-001",
  "title": "Remera básica",
  "price": 1500.00,
  "description": "Remera de algodón 100%",
  "brand": "MiMarca",
  "category_id": 2
}
```

| Campo | Obligatorio | Descripción |
|---|---|---|
| `code` | sí | Código único del producto |
| `title` | sí | Título |
| `price` | sí | Precio (≥ 0) |
| `description` | sí | Descripción |
| `brand` | sí | Marca |
| `category_id` | sí | FK → Category (debe existir) |

**Respuesta 201:** `Product` completo.

---

#### PATCH `/products/{id}` — actualizar producto

**Request body (todos opcionales):**
```json
{
  "title": "Remera básica V2",
  "price": 1800.00,
  "description": "Nueva descripción",
  "brand": "OtraMarca",
  "category_id": 3
}
```

**Respuesta 200:** `Product` actualizado.

---

#### POST `/products/{id}/dynamic-attribute` — agregar atributo dinámico al producto

Mismo patrón de dos llamadas que en categoría.

**Primera llamada:**
```json
{ "attribute_id": 5 }
```

**Si hay variantes y falta cubrir (200):**
```json
{
  "needs_implementations": true,
  "impact": [
    { "variant_id": 10 },
    { "variant_id": 11 }
  ]
}
```

**Segunda llamada:**
```json
{
  "attribute_id": 5,
  "variant_options": [
    { "variant_id": 10, "value": "S" },
    { "variant_id": 11, "value": "M" }
  ]
}
```

**Respuesta exitosa:**
```json
{
  "needs_implementations": false,
  "product": { /* Product completo */ }
}
```

---

#### POST `/products/{id}/implementations` — agregar implementación estática

**Request body:**
```json
{ "attribute_id": 3, "value": "algodón" }
```

**Respuesta 200:** `Product` actualizado.

---

#### DELETE `/products/{id}/attributes/{attr_key}?del_opt=0` — eliminar atributo propio

**Query param `del_opt`:**

| Valor | Efecto |
|---|---|
| `0` (default) | Reporta implementaciones o variantes afectadas, sin modificar |
| `1` | Elimina el atributo y sus implementaciones huérfanas |

**Respuesta con `del_opt=0` si hay impacto:**
```json
{
  "needs_decision": true,
  "impact": [ /* lista de implementaciones o variantes afectadas */ ]
}
```

---

#### POST `/products/{id}/variants` — crear variante

**Request body:**
```json
{
  "implementations": [
    { "attribute_id": 5, "value": "rojo" },
    { "attribute_id": 6, "value": "M" }
  ]
}
```

> Debe cubrir **exactamente** todos los atributos dinámicos del producto (propios + heredados de la categoría).

**Respuesta exitosa (201):** `Product` con la nueva variante incluida.

**Respuesta si implementations inválidas (400):**
```json
{
  "error": "implementations_invalid",
  "needed_attributes": [
    { "key": "color", "name": "Color", "data_type": "enum", "enum_values": ["rojo", "azul"] },
    { "key": "talle", "name": "Talle", "data_type": "enum", "enum_values": ["S", "M", "L"] }
  ]
}
```

---

## 7. Convenciones de respuesta

### Respuestas de éxito

Todos los endpoints de entidad individual retornan el objeto completo (con sus relaciones cargadas):

```json
// GET /products/1
{
  "id": 1,
  "code": "REMERA-001",
  "title": "Remera básica",
  "price": 1500.00,
  "description": "Remera de algodón 100%",
  "brand": "MiMarca",
  "category_id": 2,
  "category": {
    "id": 2,
    "name": "Ropa",
    "attributes": [ /* Attribute[] */ ]
  },
  "attributes": [ /* Attribute[] propios dinámicos */ ],
  "attributes_implementations": [ /* AttributeImplementation[] estáticos */ ],
  "variants": [
    {
      "id": 10,
      "attribute_implementations": [
        { "id": 55, "attribute": { /* Attribute */ }, "value": "rojo" },
        { "id": 56, "attribute": { /* Attribute */ }, "value": "M" }
      ]
    }
  ]
}
```

### Respuestas de error

```json
// 400 — regla de negocio
{ "detail": "mensaje de error descriptivo" }

// 404 — no encontrado
{ "detail": "Product not found" }

// 422 — body inválido (Pydantic)
{
  "detail": [
    { "loc": ["body", "price"], "msg": "value is not a valid float", "type": "type_error.float" }
  ]
}
```

---

## 8. Patrones de respuesta especiales

### Patrón `needs_implementations` (operaciones que afectan variantes/productos existentes)

Se usa cuando agregar un atributo requiere valores para entidades ya existentes.

```
Frontend                              Backend
   │                                     │
   │── POST /op { attribute_id: 5 } ───►│ 1. Carga entidades
   │                                     │ 2. Detecta impacto
   │◄─ { needs_implementations: true,   │ (no modifica nada)
   │     impact: [{...}] } ─────────────│
   │                                     │
   │  [UI pide valores al usuario]       │
   │                                     │
   │── POST /op { attribute_id: 5,      │ 3. Aplica + guarda
   │    implementations: [...] } ───────►│
   │◄─ { needs_implementations: false,  │
   │     data: {...} } ─────────────────│
```

### Patrón `needs_decision` (eliminar atributo con posible impacto)

Se usa cuando borrar un atributo puede dejar productos sin cobertura.

```
Frontend                              Backend
   │                                     │
   │── DELETE /op?del_opt=0 ───────────►│ 1. Calcula impacto
   │◄─ { needs_decision: true,          │ (no modifica nada)
   │     impact: [{...}] } ─────────────│
   │                                     │
   │  [UI muestra opciones al usuario]   │
   │  [usuario elige: eliminar datos (1) │
   │   o migrar atributo al producto (2)]│
   │                                     │
   │── DELETE /op?del_opt=1 ───────────►│ 3. Aplica + guarda
   │◄─ { needs_decision: false,         │
   │     data: {...} } ─────────────────│
```

### Resumen de operaciones con impacto

| Endpoint | Patrón | Se activa cuando... |
|---|---|---|
| `POST /categories/{id}/dynamic-attribute` | `needs_implementations` | Hay productos con variantes sin el atributo |
| `POST /categories/{id}/static-attribute` | `needs_implementations` | Hay productos sin el atributo |
| `POST /products/{id}/dynamic-attribute` | `needs_implementations` | El producto tiene variantes |
| `DELETE /categories/{id}/attributes/{attr_id}?del_opt=0` | `needs_decision` | Hay productos que quedan sin cobertura |
| `DELETE /products/{id}/attributes/{attr_key}?del_opt=0` | `needs_decision` | Hay implementaciones huérfanas |
