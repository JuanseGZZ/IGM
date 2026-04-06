# models.py — Documentación de clases

## Attribute

**Definición de un atributo** (no su valor — eso es AttributeImplementation)
- `key` → identificador interno único
- `name` → nombre legible
- `data_type` → `text | number | boolean | enum`
- `is_static` → `True` = atributo de producto / `False` = atributo de variante
- `enum_values` → lista de valores posibles si el tipo es `enum`

**Métodos**
- `add_enum_value(value)` → agrega valor posible al enum (lanza error si ya existe)
- `check_value(value)` → valida que el valor sea del tipo correcto
- `to_json()` → serializa el atributo a dict
- `from_json(data)` → reconstruye el atributo desde dict

---

## Attribute_factory

**Factory con caché** — garantiza que no existan dos instancias del mismo atributo
- `_instances` → dict con el caché `key → Attribute`

**Métodos**
- `get(key, name, data_type, ...)` → devuelve instancia existente o crea una nueva
- `clear()` → vacía el caché (útil en tests)

---

## AttributeImplementation

**Une un Attribute con un valor concreto** — es la celda específica de una propiedad
- `attribute` → referencia al objeto `Attribute`
- `value` → valor asignado (ej: `"Rojo"`, `42`, `True`)

Vive en `Product.attributes_implementations` (estáticos) o en `Variant.attribute_implementations` (dinámicos).

**Métodos**
- `to_json()` → serializa con el atributo anidado
- `from_json(data)` → deserializa desde dict

---

## Category

**Nodo del árbol de categorías** — contiene atributos heredables, subcategorías y/o productos

> Regla fundamental: una categoría no puede tener subcategorías y productos al mismo tiempo.

- `attributes` → atributos propios de esta categoría
- `subcategories` → categorías hijas
- `father_categorie` → categoría padre (o `None` si es raíz)
- `products` → productos directos (solo si no hay subcategorías)

**Lectura recursiva**
- `get_attributes()` → atributos propios + todos los de ancestros
- `get_attribute_keys()` → set de keys (más eficiente para lookups)

**Agregar atributos**
- `add_dinamic_attribute(attribute, product_variant_implementations)` → agrega atributo de variante; requiere valores para cada variante de cada producto afectado
- `add_static_attribute(attribute, implementations)` → agrega atributo de producto; requiere valor para cada producto afectado

**Eliminar atributos**
- `del_attribute(attribute, delete_opt=0)` → modo `0` avisa impacto sin modificar, `1` borra implementaciones huérfanas, `2` inyecta el atributo directamente en los productos afectados
- `del_attribute_check_family_impact(attribute)` → retorna productos que quedarían sin cobertura

**Jerarquía de categorías**
- `change_categorie_father(father_categorie, implementations, del_option=0)` → mueve esta categoría como hija de otra; resuelve herencia de atributos nuevos e impacto de atributos huérfanos del padre anterior (`del_option`: `0`=reporta sin modificar, `1`=inyecta huérfanos en `self`, `2`=elimina implementaciones huérfanas)
- `del_categorie(categorie, del_option)` → elimina subcategoría hija con tres modos: `0` inyecta atributos sobrantes en productos, `1` borra implementaciones, `2` solo reporta impacto

**Productos**
- `add_product(product)` → agrega producto (lanza error si hay subcategorías)
- `del_product(product)` → elimina producto de la categoría

---

## Variant

**Combinación específica de opciones de un producto** — implementa los atributos dinámicos

- `attribute_implementations` → lista de `AttributeImplementation` de atributos no estáticos

No tiene precio ni título propio: los hereda del `Product` al que pertenece.

**Métodos**
- `to_json()` → serializa la variante con sus implementaciones
- `from_json(data)` → reconstruye la variante desde dict

---

## Product

**Entidad central del catálogo** — tiene información base, atributos, implementaciones estáticas y variantes

> La `category` es obligatoria — el constructor lanza `ValueError` si no se pasa.

- `code` → código único del producto
- `title`, `price`, `description`, `brand` → datos base
- `category` → referencia a su `Category`
- `attributes_implementations` → implementaciones de atributos estáticos (info fija)
- `attributes` → atributos dinámicos propios (complementan los de la categoría)
- `variants` → lista de `Variant`

**Lectura**
- `is_attribute_in(attribute)` → verifica si el producto tiene el atributo propio
- `get_attributes()` → propios + los de la categoría (recursivo)
- `get_needed_atributes_implementations(is_static)` → qué atributos necesitan implementación en el producto o en sus variantes

**Agregar atributos**
- `add_dinamic_attribute(attribute, variant_options)` → agrega atributo de variante y aplica valores a cada variante
- `add_static_attribute(attribute, implementation)` → agrega atributo estático con su implementación
- `add_product_implementation(attribute_implementation)` → verifica y agrega una implementación estática (lanza error si ya existe)

**Gestión de variantes**
- `create_variant_by_implementations(implementations)` → crea una `Variant` validando que las implementaciones coincidan exactamente con los atributos requeridos
- `del_variant(variant_id)` → elimina variante por id

**Serialización**
- `to_json()` → dict completo con todos los datos anidados
- `from_json(data)` → reconstruye el producto completo desde dict
