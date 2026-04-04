# Product

> Entidad central del modelo. Representa un producto del catálogo con su información base, atributos estáticos implementados, atributos dinámicos y variantes.

## Propiedades

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador en base de datos |
| `code` | str | Código único del producto |
| `title` | str | Nombre del producto |
| `price` | float | Precio base |
| `description` | str | Descripción del producto |
| `brand` | str | Marca |
| `category` | Category | Categoría a la que pertenece (**obligatoria**) |
| `attributes_implementations` | list[AttributeImplementation] | Implementaciones de atributos **estáticos** (info fija del producto) |
| `_impl_keys` | set | Caché de keys de implementaciones estáticas |
| `attributes` | list[Attribute] | Atributos **dinámicos** propios del producto (complementan los de la categoría) |
| `_attribute_keys` | set | Caché de keys de atributos propios |
| `variants` | list[Variant] | Variantes del producto |

> ⚠️ Si no se pasa `category`, el constructor lanza `ValueError`.

## Caches internos

`_attribute_keys` e `_impl_keys` se mantienen sincronizados **manualmente** dentro de cada método. Modificar `attributes` o `attributes_implementations` directamente (sin usar los métodos de la clase) deja los caches desactualizados.

> Siempre usar los métodos oficiales para agregar o eliminar atributos e implementaciones.

---

## Métodos de lectura

### `is_attribute_in(attribute) → bool`
Verifica si el producto tiene un atributo propio (no incluye los de la categoría).

### `get_attributes() → list`
Retorna todos los atributos: propios + los de la categoría (recursivo hacia arriba).

### `get_attribute_keys() → set`
Keys propios + todos los de la categoría (recursivo). Más eficiente que `get_attributes()` para lookups.

### `get_needed_atributes_implementations(is_static=False) → set`
Retorna el conjunto de atributos que **deben tener implementación** en el producto (si `is_static=True`) o en sus variantes (si `is_static=False`).

---

## Métodos de atributos

### `add_dinamic_attribute(attribute, variant_options)`
Agrega un atributo **dinámico** al producto y aplica los valores a cada variante.
- `variant_options`: `[{"variant_id": id, "value": value}]`
- Verifica cobertura exacta: deben estar **todas** las variantes.
- Retorna `True` si exitoso, `False` si hay error de validación.

### `add_static_attribute(attribute, implementation)`
Agrega un atributo **estático** con su implementación al producto.
- Verifica tipo de dato y que el atributo esté suscripto en la categoría.

### `del_attribute(attribute, delete_opt=0)`
Elimina un atributo propio del producto con dos modos:
- `0` → Retorna lista de variantes/implementaciones afectadas sin eliminar
- `1` → Elimina el atributo y borra las implementaciones huérfanas

### `add_product_implementation(attribute_implementation)`
Verifica y agrega una implementación de atributo estático al producto.
- Valida tipo de dato y que el atributo esté suscripto en el producto o categoría.
- Lanza `ValueError` si la implementación ya existe para ese atributo.

---

## Métodos de variantes

### `create_variant_by_implementations(implementations)`
Crea una nueva `Variant` a partir de una lista de `AttributeImplementation`.
- Valida que los atributos recibidos coincidan **exactamente** con los necesarios.
- Valida tipos de dato de cada valor.
- Agrega la variante al producto si todo es válido.

### `del_variant(variant_id) → bool`
Elimina una variante por su id. Retorna `True` si se eliminó.

### `get_add_attribute_impact(attribute) → dict | None`
Helper para operaciones de categoría. Retorna `None` si el producto ya tiene el atributo, o un dict `{product_id: [variant_ids]}` con las variantes que necesitarían implementación.

---

## Helpers internos

### `_add_variant(variant)`
Agrega directamente una variante a la lista (sin validaciones extra). Usado internamente por `create_variant_by_implementations`.

### `_check_implementation(attr_impl) → bool`
Valida que una implementación tenga tipo correcto y que el atributo esté suscripto en el producto o categoría. Lanza `ValueError` si no.

---

## Serialización

### `to_json() → dict`
Serializa el producto completo: datos base, categoría, implementaciones, atributos y variantes.

### `from_json(data: dict) → Product` *(classmethod)*
Reconstruye un producto completo desde un diccionario, incluyendo categoría, implementaciones y variantes anidadas.
