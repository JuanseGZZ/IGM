# API — IGM Catalog

## Descripción general

La API actúa como puerta de entrada entre el front (que arma y edita el árbol visualmente) y el modelo de negocio (`models.py`) que valida todas las reglas.

El flujo principal es de reemplazo total: el front envía el árbol completo, la API lo valida construyéndolo con el modelo, y si es válido lo persiste. Si no es válido, retorna el error y la ubicación exacta dentro del árbol, sin tocar la DB.

---

## Arquitectura

```
Front  ──POST /catalog──▶  api.py  ──▶  service.py  ──▶  models.py  (validación)
                                     └──▶  repository.py  ──▶  SQLite   (persistencia)

Front  ──GET /catalog───▶  api.py  ──▶  service.py  ──▶  repository.py  ──▶  SQLite
```

- **`api.py`** — FastAPI. Define endpoints y schemas Pydantic. No tiene lógica de negocio.
- **`service.py`** — Orquestador. Construye los objetos del modelo en memoria, delega validación al modelo, y llama al repositorio si todo es válido.
- **`repository.py`** — Acceso a SQLite. Solo sabe leer y escribir. No valida reglas.
- **`models.py`** — Fuente de verdad de todas las reglas de negocio. La API no reimplementa ninguna regla.

---

## Endpoints

### `GET /catalog`

Retorna el estado actual del catálogo (atributos + árbol completo).

**Response `200`:**
```json
{
  "attributes": [
    {
      "id": 1,
      "key": "color",
      "name": "Color",
      "data_type": "enum",
      "is_static": false,
      "enum_values": ["Rojo", "Azul", "Verde"]
    }
  ],
  "tree": {
    "id": 1,
    "name": "Catálogo",
    "attribute_ids": [],
    "subcategories": [
      {
        "id": 2,
        "name": "Ropa",
        "attribute_ids": [1, 2],
        "subcategories": [...],
        "products": []
      }
    ],
    "products": []
  }
}
```

Si la DB está vacía, `tree` es `null` y `attributes` es `[]`.

---

### `POST /catalog`

Recibe el árbol completo + atributos, valida todo con el modelo, y si es válido reemplaza el estado persistido.

**Request body:** mismo formato que el response de `GET /catalog`.

**Response `200` — válido:**
```json
{ "valid": true }
```

**Response `422` — inválido:**
```json
{
  "valid": false,
  "error": "[raíz → categoría 'Ropa' → producto 'REM001' → variante id=3] Variante invalida — faltan: ['talle']"
}
```

Cuando hay error, **no se modifica nada** en la DB.

---

## Formato JSON del árbol

### Referencia de atributos

- Los atributos se mandan **una sola vez** en la lista `attributes` a nivel raíz del payload.
- Las **categorías** referencian sus atributos por ID: `"attribute_ids": [1, 2]`.
- Las **implementaciones** (en productos y variantes) referencian el atributo por `key`: `"attribute_key": "color"`.

### Producto
```json
{
  "id": 1,
  "code": "REM001",
  "title": "Remera Básica",
  "price": 1500.0,
  "description": "Algodón 100%",
  "brand": "Nike",
  "attributes_implementations": [
    { "attribute_key": "material", "value": "Algodón" }
  ],
  "variants": [
    {
      "id": 1,
      "attribute_implementations": [
        { "attribute_key": "color", "value": "Rojo" },
        { "attribute_key": "talle", "value": "M" }
      ]
    }
  ]
}
```

### Nodos con `id: null`

Se aceptan nodos sin ID (nuevos). SQLite asigna el ID automáticamente. El ID aparece en el próximo `GET /catalog`.

---

## Flujo de validación (POST)

1. Se construye el registro de atributos desde `payload.attributes`.
2. Se recorre el árbol **de arriba hacia abajo**, construyendo objetos del modelo:
   - `Category` → se vincula con `add_subcategory` (valida R1, R3).
   - `Product` → se agrega con `add_product` (valida R2, R13).
   - `Variant` → se agrega con `add_variant` (valida R13b, R14, R15).
3. Si cualquier método del modelo lanza `ValueError` → se captura, se anota la ubicación en el árbol, y se retorna el error. **Nada se persiste.**
4. Si todo el árbol se construye sin errores → `repository.save_full_state()` reemplaza la DB de forma atómica (dentro de una transacción).

---

## Esquema de la DB (SQLite)

```
attributes           (id, key, name, data_type, is_static)
attribute_enum_values(id, attribute_id → attributes, value)
categories           (id, name, father_category_id → categories)
category_attributes  (category_id → categories, attribute_id → attributes)
products             (id, code, title, price, description, brand, category_id → categories)
variants             (id, product_id → products)
attribute_implementations (id, attribute_id → attributes, value,
                           product_id → products | NULL,
                           variant_id → variants  | NULL)
```

Una `attribute_implementation` pertenece a un producto (estático) O a una variante (dinámico), nunca a ambos.

---

## Reglas de negocio de la API

**A1** — El POST es siempre un reemplazo total del estado. No hay PATCHes parciales. El front envía el árbol completo y la API lo evalúa como un todo.

**A2** — La validación es atómica: si cualquier nodo del árbol falla, no se persiste nada. La DB queda en el estado anterior.

**A3** — El orden de construcción es top-down (raíz → hojas). Los errores se detectan en el primer nodo que falla y se retornan inmediatamente, con la ruta exacta dentro del árbol.

**A4** — La API no revalida reglas propias. Toda validación de negocio (exclusividad, ciclos, completitud, unicidad de variantes) la ejecuta el modelo (`models.py`). La API solo captura los `ValueError` que el modelo lanza.

**A5** — Los atributos del payload se toman como fuente de verdad. Si el ID de un atributo ya existe en DB pero con datos distintos (name, data_type, is_static), el nuevo estado reemplaza al anterior al persistir.

**A6** — Si `tree` es `null` en el GET (DB vacía), el front debe enviar un árbol válido en el primer POST para inicializar el estado.

---

## Dependencias

```
fastapi
uvicorn[standard]
```

SQLite viene incluido en Python (stdlib `sqlite3`). No se requieren dependencias externas de DB.

## Correr la API

```bash
uvicorn api:app --reload
```
