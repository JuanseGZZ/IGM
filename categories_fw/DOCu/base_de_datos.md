# Base de datos

SQLite embebido usando la stdlib `sqlite3` de Python. Sin ORM.

## Archivo

El archivo `categories.db` se crea automáticamente en el directorio raíz del proyecto al iniciar la aplicación (`uvicorn main:app`). Se puede borrar para empezar desde cero.

## Inicialización

`db_handler/db.py` expone:

- `get_connection()`: abre la conexión, activa `PRAGMA foreign_keys = ON` y configura `row_factory = sqlite3.Row` (acceso por nombre de columna).
- `init_db()`: ejecuta `schema.sql` completo. Se llama una vez en el evento `startup` de FastAPI.

---

## Esquema (8 tablas)

### attribute
Atributos globales del sistema.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Autoincremental |
| `key` | TEXT UNIQUE | Identificador único (`"color"`, `"talle"`) |
| `name` | TEXT | Nombre visible |
| `data_type` | TEXT | `"text"`, `"number"`, `"boolean"`, `"enum"` |
| `is_static` | INTEGER | `0` = dinámico, `1` = estático |

### enum_value
Valores posibles para atributos de tipo `enum`.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `attribute_id` | INTEGER FK → attribute | CASCADE DELETE |
| `value` | TEXT | |

UNIQUE(`attribute_id`, `value`)

### category
Nodos del árbol de categorías.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | |
| `father_id` | INTEGER FK → category | SET NULL al borrar el padre |

La auto-referencia `father_id` permite modelar la jerarquía en una sola tabla.

### category_attribute
Relación muchos-a-muchos entre categorías y atributos.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `category_id` | INTEGER FK → category | CASCADE DELETE |
| `attribute_id` | INTEGER FK → attribute | CASCADE DELETE |

UNIQUE(`category_id`, `attribute_id`) — un atributo no puede aparecer dos veces en la misma categoría.

### product

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `code` | TEXT UNIQUE | SKU |
| `title` | TEXT | |
| `price` | REAL | |
| `description` | TEXT | Nullable |
| `brand` | TEXT | Nullable |
| `category_id` | INTEGER FK → category | RESTRICT — no se puede borrar una categoría con productos |

### product_implementation
Una implementación de atributo **estático** por producto.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `product_id` | INTEGER FK → product | CASCADE DELETE |
| `attribute_id` | INTEGER FK → attribute | RESTRICT |
| `value` | TEXT | |

UNIQUE(`product_id`, `attribute_id`) — un producto implementa cada atributo una sola vez.

### variant
Variante de un producto (combinación de atributos dinámicos).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `product_id` | INTEGER FK → product | CASCADE DELETE |

### variant_implementation
Una implementación de atributo **dinámico** por variante.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | |
| `variant_id` | INTEGER FK → variant | CASCADE DELETE |
| `attribute_id` | INTEGER FK → attribute | RESTRICT |
| `value` | TEXT | |

UNIQUE(`variant_id`, `attribute_id`)

---

## Diagrama de relaciones

```
attribute ──< enum_value
attribute ──< category_attribute >── category ──< category (self-ref)
attribute ──< product_implementation >── product >── category
attribute ──< variant_implementation >── variant >── product
```

---

## Repositorios (`db_handler/repositories.py`)

### AttributeRepo
- `save(attr)`: INSERT o UPDATE + sincroniza `enum_value`
- `get(id)`: SELECT + carga `enum_values`
- `list_all()`: todos los atributos con sus enum_values
- `delete(id)`: DELETE CASCADE

### CategoryRepo
- `save(cat)`: INSERT o UPDATE + sincroniza `category_attribute`
- `get(id)`: llama a `load_tree()` y retorna el nodo
- `load_tree()`: **3 queries** — categorías, `category_attribute JOIN attribute`, `enum_value`; ensambla el árbol en memoria y retorna `{id: Category}`
- `delete(id)`: DELETE CASCADE

### ProductRepo
- `save(prod)`: INSERT o UPDATE producto + sincroniza `product_implementation` + delega a `VariantRepo`
- `get(id)`: `_load_product` con implementaciones y variantes
- `list_by_category(cat_id)`: productos de una categoría sin cargar variantes
- `list_all()`: todos los productos
- `delete(id)`: DELETE CASCADE

### VariantRepo
- `save(product_id, variant)`: INSERT variante + INSERT `variant_implementation`
- `get(id)`: SELECT variante + implementaciones
- `delete(id)`: DELETE CASCADE

---

## Notas importantes

- `CategoryRepo.load_tree()` carga todo el árbol completo en cada llamada. Para volúmenes grandes esto puede ser ineficiente; se puede agregar cache en memoria.
- Las foreign keys con `RESTRICT` en `product.category_id` impiden borrar una categoría que tenga productos directamente asociados. Hay que borrar los productos primero.
- `product_implementation` y `variant_implementation` son tablas **separadas** (no compartidas). Cada una tiene su propio `id` autoincremental.
