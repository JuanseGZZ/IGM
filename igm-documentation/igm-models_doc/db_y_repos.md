# Base de Datos y Repositorios

> Documenta la arquitectura de la BD, el mapeo modelo → tabla, el comportamiento de cada repo y las reglas de negocio que viven en la capa de persistencia.

---

## Índice

1. [Arquitectura de la base de datos](#1-arquitectura-de-la-base-de-datos)
2. [CrudBase — clase base de repos](#2-crudbase--clase-base-de-repos)
3. [AttributeRepo](#3-attributerepo)
4. [CategoryRepo](#4-categoryrepo)
5. [ProductRepo](#5-productrepo)
6. [Limitaciones conocidas](#6-limitaciones-conocidas)

---

## 1. Arquitectura de la base de datos

### Diagrama de relaciones

```
category ──────────────────────────── product
   │  └── category_atributes              │  └── products_atributes
   │           │                          │           │
   │           ▼                          │           ▼
   │        atribute ◄──────── atr_implementation ◄── product_implementation
   │           │  └── enum_values              ▲
   │                                           │
   └──────────────────── variant ──── variant_implementation
```

### Tablas

#### `category`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `name` | VARCHAR(255) | Nombre de la categoría |

> No tiene columna `parent_id`. El árbol padre-hijo vive **solo en memoria** — no se persiste en la BD.

---

#### `atribute`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `key` | VARCHAR(100) | Clave única del atributo |
| `name` | VARCHAR(255) | Nombre legible |
| `data_type` | VARCHAR(50) | `text`, `number`, `boolean`, `enum` |
| `is_static` | BOOLEAN | `true` = atributo de producto / `false` = atributo de variante |

---

#### `enum_values`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `atribute_id` | FK → `atribute` ON DELETE CASCADE | El atributo al que pertenece |
| `value` | VARCHAR(255) | Valor posible |

---

#### `category_atributes`
Tabla de unión categoría ↔ atributo.

| Columna | Tipo |
|---|---|
| `id` | SERIAL PK |
| `category_id` | FK → `category` ON DELETE CASCADE |
| `atribute_id` | FK → `atribute` ON DELETE CASCADE |

---

#### `product`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `code` | VARCHAR(100) UNIQUE | Código único del producto |
| `title` | VARCHAR(255) | Título |
| `price` | NUMERIC(12,2) | Precio |
| `description` | TEXT | Descripción |
| `brand` | VARCHAR(255) | Marca |
| `category_id` | FK → `category` ON DELETE RESTRICT | Categoría obligatoria |

---

#### `products_atributes`
Tabla de unión producto ↔ atributo propio (dinámicos propios del producto).

| Columna | Tipo |
|---|---|
| `id` | SERIAL PK |
| `product_id` | FK → `product` ON DELETE CASCADE |
| `atribute_id` | FK → `atribute` ON DELETE CASCADE |

---

#### `atr_implementation`
Celda concreta atributo + valor. La usan tanto `product_implementation` como `variant_implementation`.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `atribute_id` | FK → `atribute` ON DELETE RESTRICT | El atributo implementado |
| `value` | VARCHAR(255) | Valor como string; se castea en la app según `data_type` |

> **Sin CASCADE propio.** Cuando se elimina un producto o variante, las filas de `atr_implementation` quedan huérfanas si no se borran explícitamente. `ProductRepo.delete` maneja esto.

---

#### `product_implementation`
Une producto con su `atr_implementation` (atributos estáticos).

| Columna | Tipo |
|---|---|
| `id` | SERIAL PK |
| `product_id` | FK → `product` ON DELETE CASCADE |
| `atr_imp_id` | FK → `atr_implementation` ON DELETE CASCADE |

---

#### `variant`
| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador |
| `code` | VARCHAR(100) UNIQUE | Generado en el repo como `{product.code}-v{n}` |
| `product_id` | FK → `product` ON DELETE CASCADE | Producto al que pertenece |

> `code` y `product_id` existen en la BD pero el modelo `Variant` no los expone como campos.

---

#### `variant_implementation`
Une variante con su `atr_implementation` (atributos dinámicos).

| Columna | Tipo |
|---|---|
| `id` | SERIAL PK |
| `variant_id` | FK → `variant` ON DELETE CASCADE |
| `atr_imp_id` | FK → `atr_implementation` ON DELETE CASCADE |

---

### Flujo de cascada al borrar un producto

```
DELETE product
  → CASCADE: product_implementation, products_atributes, variant
               → CASCADE: variant_implementation
  ⚠ NO cascade: atr_implementation  ← debe borrarse manualmente (ProductRepo.delete)
```

---

## 2. CrudBase — clase base de repos

`CrudBase[T]` en `crud_base.py`. Todos los repos heredan de acá.

### Campos de clase a definir por el hijo

| Campo | Tipo | Descripción |
|---|---|---|
| `TABLE` | `str` | Nombre de la tabla en la BD |
| `MODEL_CLASS` | `Type[T]` | Clase del modelo para reconstruir objetos |

### Métodos

#### `save(obj: T) → T`
- Si `obj.id is None` → `INSERT ... RETURNING *` → retorna objeto reconstruido.
- Si `obj.id` tiene valor → `UPDATE ... WHERE id = ... RETURNING *`.
  - Si el UPDATE no encuentra la fila (0 rows) → hace `INSERT` con el id explícito.
- Hace `conn.commit()` al final.
- Retorna el objeto reconstruido desde la fila devuelta por `RETURNING *` via `_row_to_obj`.

#### `read(obj_id) → T | None`
- `SELECT * FROM {table} WHERE id = %s`.
- Retorna `None` si no existe.

#### `delete(obj_id) → bool`
- `DELETE FROM {table} WHERE id = %s`.
- Retorna `True` si se borró al menos una fila, `False` si no existía.

#### `bring_all() → list[T]`
- `SELECT * FROM {table}`.
- Retorna lista de todos los objetos reconstruidos.

#### `_obj_to_row(obj) → dict`
- Default: `vars(obj).copy()`. Cada repo lo sobreescribe para mapear solo los campos de la tabla.

#### `_row_to_obj(row) → T | None`
- Default: `MODEL_CLASS(**row)`. Cada repo lo sobreescribe para cargar relaciones.

---

## 3. AttributeRepo

Archivo: `attributes_repo.py`  
Tabla principal: `atribute`

### Mapeo `_obj_to_row`

```python
{ "id", "key", "name", "data_type", "is_static" }
```

`enum_values` **no** está en esta fila — se maneja por separado en `_save_enum_values`.

### Carga (`_row_to_obj`)

1. Construye `Attribute` con los 5 campos de la tabla.
2. Si `data_type == "enum"` → llama `_load_enum_values(attribute.id)` y puebla `attribute.enum_values`.

### `save(obj: Attribute) → Attribute`

Flujo extendido respecto a `CrudBase.save`:

1. Guarda una copia de `enum_values` original (el `super().save()` devuelve el objeto reconstruido sin ellos todavía).
2. Llama `super().save(obj)` → INSERT o UPDATE en `atribute`.
3. Restaura `enum_values` en el objeto devuelto.
4. Llama `_save_enum_values(saved)`:
   - `DELETE FROM enum_values WHERE atribute_id = %s` (borra todos los existentes).
   - Re-inserta los actuales.
5. `conn.commit()`.
6. Retorna `cls.read(saved.id)` — objeto fresco desde la BD con `enum_values` cargados.

### Reglas

- No se pueden guardar `enum_values` si el atributo no tiene `id` (debe existir en la BD primero).
- El `save` siempre reemplaza todos los `enum_values` existentes — no hace merge.
- `delete` usa el cascade de FK: al borrar `atribute`, se borran automáticamente sus `enum_values` y entradas en `category_atributes` y `products_atributes`.
  - **Bloqueo:** si hay `atr_implementation` que referencian este atributo, el DELETE falla con `ForeignKeyViolation` (FK con `ON DELETE RESTRICT`). Hay que borrar el producto antes.

---

## 4. CategoryRepo

Archivo: `category_repo.py`  
Tabla principal: `category`

### Mapeo `_obj_to_row`

```python
{ "id", "name" }
```

Solo se persisten estos dos campos. El árbol (`father_categorie`, `subcategories`) no tiene columnas en la BD.

### Carga (`_row_to_obj`)

1. Construye `Category(id, name, attributes=_load_attributes(id))`.
2. Llama `_load_products(category)` y agrega cada producto a `category.products` y `category._product_codes`.

#### `_load_attributes(category_id)`

Query:
```sql
SELECT a.id, a.key, a.name, a.data_type, a.is_static
FROM category_atributes ca
JOIN atribute a ON a.id = ca.atribute_id
WHERE ca.category_id = %s
ORDER BY ca.id
```

Para cada atributo `enum`, hace query adicional a `enum_values`.

#### `_load_products(category)`

Lazy import de `ProductRepo` para evitar circular import a nivel módulo.

Query:
```sql
SELECT id, code, title, price, description, brand, category_id
FROM product
WHERE category_id = %s
ORDER BY id
```

Llama `ProductRepo._row_to_obj(row)` para cada fila (carga completa con variantes e implementaciones), luego sobreescribe `product.category = category` para que el producto apunte al objeto categoría ya construido.

### `save(obj: Category) → Category`

1. `super().save(obj)` → INSERT o UPDATE en `category`.
2. `DELETE FROM category_atributes WHERE category_id = %s` (limpia la asociación actual).
3. Re-inserta todos los atributos actuales de `obj.attributes` en `category_atributes`.
   - Si algún atributo no tiene `id` → `ValueError`.
4. `conn.commit()`.
5. Retorna `cls.read(saved.id)`.

### Reglas

- `save` siempre reemplaza las asociaciones de atributos (no hace merge).
- Un atributo debe existir en la BD (tener `id`) antes de poder asociarse a una categoría.
- El campo `father_categorie` y la lista `subcategories` **no se persisten**. Son relaciones en memoria que se construyen a nivel servicio.
- `delete` con FK `ON DELETE RESTRICT` en `product.category_id`: no se puede borrar una categoría si tiene productos asociados.

---

## 5. ProductRepo

Archivo: `product_repo.py`  
Tabla principal: `product`

### Mapeo `_obj_to_row`

```python
{ "id", "code", "title", "price", "description", "brand", "category_id" }
```

`category_id` toma el valor de `obj.category.id` — la categoría debe existir en la BD.

### Carga (`_row_to_obj`)

1. `_load_category(row["category_id"])` → construye `Category` con sus `attributes`.
2. `_load_product_implementations(product_id)` → lista de `AttributeImplementation` estáticas.
3. `_load_product_attributes(product_id)` → atributos dinámicos propios del producto.
4. Construye `Product(...)` con todo lo anterior y `variants=[]`.
5. `_load_variants(product)` → completa `product.variants`.

#### `_load_category(category_id)`

```sql
SELECT id, name FROM category WHERE id = %s
```

Luego llama `_load_category_attributes(category_id)` para cargar los atributos de la categoría. Esto asegura que `product.category.get_attributes()` devuelva resultados correctos.

> Carga superficial: no incluye `father_categorie`, `subcategories` ni `products` de la categoría. Es suficiente para las operaciones del producto.

#### `_load_category_attributes(category_id)`

Misma query que `CategoryRepo._load_attributes`. Para cada atributo intenta `AttributeRepo.read` primero (para cargar `enum_values`), y si falla construye el objeto mínimo desde la fila.

#### `_load_product_implementations(product_id)`

```sql
SELECT ai.id AS implementation_id, ai.value,
       a.id AS attribute_id, a.key, a.name, a.data_type, a.is_static
FROM product_implementation pi
JOIN atr_implementation ai ON ai.id = pi.atr_imp_id
JOIN atribute a ON a.id = ai.atribute_id
WHERE pi.product_id = %s
ORDER BY pi.id
```

#### `_load_product_attributes(product_id)`

```sql
SELECT a.id, a.key, a.name, a.data_type, a.is_static
FROM products_atributes pa
JOIN atribute a ON a.id = pa.atribute_id
WHERE pa.product_id = %s
ORDER BY pa.id
```

#### `_load_variants(product)`

```sql
SELECT id, code, product_id FROM variant WHERE product_id = %s ORDER BY id
```

Para cada variante llama `_load_variant_implementations(variant_id)`:

```sql
SELECT ai.id AS implementation_id, ai.value,
       a.id AS attribute_id, a.key, a.name, a.data_type, a.is_static
FROM variant_implementation vi
JOIN atr_implementation ai ON ai.id = vi.atr_imp_id
JOIN atribute a ON a.id = ai.atribute_id
WHERE vi.variant_id = %s
ORDER BY ai.id
```

### `save(obj: Product) → Product`

1. `super().save(obj)` → INSERT o UPDATE en `product`. Retorna objeto con `id` y `code` asignados.
2. Actualiza `obj.id` y `obj.code` con los valores guardados.
3. `_save_product_attributes(obj)`:
   - Borra todas las entradas en `products_atributes` para este producto.
   - Re-inserta los atributos actuales de `obj.attributes`.
4. `_save_product_implementations(obj)`:
   - Lee los `atr_imp_id` actuales en `product_implementation`.
   - Borra `product_implementation` + los `atr_implementation` correspondientes.
   - Re-inserta cada `AttributeImplementation` en `atr_implementation` → `product_implementation`.
5. `_save_variants(obj)`:
   - Recolecta todos los `atr_imp_id` de variantes existentes.
   - Borra `variant` para este producto (cascadea `variant_implementation`).
   - Borra los `atr_implementation` recolectados.
   - Re-inserta cada variante con código `{product.code}-v{n}` y sus implementaciones.
6. `conn.commit()`.
7. Retorna `cls.read(saved.id)` — objeto fresco completo desde la BD.

### `delete(obj_id) → bool`

Override de `CrudBase.delete`. La BD no hace cascade sobre `atr_implementation` al borrar un producto, por lo que el repo lo maneja explícitamente:

1. Recolecta todos los `atr_imp_id` de `product_implementation` del producto.
2. Recolecta todos los `atr_imp_id` de `variant_implementation` (via `variant.product_id`).
3. Llama `super().delete(obj_id)` → `DELETE FROM product` (cascadea `product_implementation`, `products_atributes`, `variant` → `variant_implementation`).
4. Borra cada `atr_implementation` recolectada.
5. `conn.commit()`.

> Sin este override, borrar un producto dejaría filas huérfanas en `atr_implementation` que bloquearían futuros `AttributeRepo.delete`.

### `read_by_code(code: str) → Product | None`

```sql
SELECT id, code, title, price, description, brand, category_id
FROM product WHERE code = %s
```

Retorna el producto completo construido via `_row_to_obj`.

### Reglas

- La categoría del producto **debe existir en la BD** antes de guardar (se guarda `category_id`).
- Todos los atributos en `product.attributes` deben tener `id` antes de guardar.
- `save` siempre reemplaza variantes e implementaciones completas — no hace merge incremental.
- El código de variante lo genera el repo: `{product.code}-v1`, `{product.code}-v2`, etc. El modelo `Variant` no almacena este código.

---

## 6. Limitaciones conocidas

### `father_categorie` y `subcategories` no se persisten

La tabla `category` no tiene `parent_id`. El árbol de categorías es una estructura **solo en memoria**. Si se recarga una categoría desde la BD, `father_categorie` es `None` y `subcategories` es `[]`.

La construcción del árbol debe hacerse a nivel servicio ensamblando los nodos leídos de la BD.

### `_load_category` en `ProductRepo` es superficial

Al leer un producto, su `product.category` tiene `id`, `name` y `attributes`, pero **no** tiene `father_categorie`, `subcategories` ni `products`. Es suficiente para las operaciones del producto, pero no para operaciones que requieran el árbol completo.

### `atr_implementation` sin cascade automático

Las filas de `atr_implementation` no están conectadas directamente a `product` con `ON DELETE CASCADE`. El borrado correcto depende de `ProductRepo.delete`. Si se borra un producto directamente por SQL (sin pasar por el repo), quedan filas huérfanas.

### Variantes duplicadas no detectadas en el modelo

`Product.create_variant_by_implementations` no verifica si ya existe una variante con la misma combinación de valores (TODO pendiente en el modelo). El repo tampoco lo chequea — si se guarda un producto con variantes duplicadas, se insertan sin error.
