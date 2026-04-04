# Category

> Nodo del árbol de categorías. Puede contener subcategorías **o** productos (no ambos a la vez). Define atributos heredables hacia abajo en la jerarquía.

## Propiedades

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador en base de datos |
| `name` | str | Nombre de la categoría |
| `attributes` | list[Attribute] | Atributos propios de esta categoría |
| `_attribute_keys` | set | Caché de keys de atributos propios |
| `subcategories` | list[Category] | Subcategorías hijas |
| `father_categorie` | Category | Categoría padre (o `None` si es raíz) |
| `products` | list[Product] | Productos que pertenecen directamente a esta categoría |
| `_product_codes` | set | Caché de códigos de productos |

## Caches internos

`_attribute_keys` y `_product_codes` se mantienen sincronizados **manualmente** dentro de cada método. Si se modifican `attributes` o `products` directamente (sin pasar por los métodos de la clase), los caches quedan desactualizados y el comportamiento es impredecible.

> Siempre usar los métodos oficiales para agregar o eliminar atributos y productos.

## Regla fundamental

> Una categoría **no puede tener subcategorías y productos al mismo tiempo**.  
> Si tiene subcategorías, los productos van en las hojas del árbol.

---

## Métodos de lectura

### `get_attributes() → list`
Devuelve todos los atributos propios **más** los de todos los ancestros (recursivo hacia arriba).

### `get_attribute_keys() → set`
Igual que `get_attributes()` pero devuelve solo los `key` (más eficiente para lookups).

---

## Métodos de atributos — Agregar

### `add_dinamic_attribute(attribute, product_variant_implementations)`
Agrega un atributo **dinámico** (de variante) a la categoría.
- Verifica impacto en productos descendientes que no lo tengan.
- `product_variant_implementations`: `[{"product_id": id, "variants": [{"variant_id": id, "value": value}]}]`
- Retorna `{}` si exitoso, o lista de productos en riesgo si la validación falla.

### `add_static_attribute(attribute, implementations)`
Agrega un atributo **estático** (de producto) a la categoría.
- `implementations`: `[{"product_id": id, "value": value}]`
- Retorna `{}` si exitoso, o lista de productos en riesgo.

---

## Métodos de atributos — Eliminar

### `del_attribute(attribute, delete_opt=0)`
Elimina un atributo de la categoría con tres modos:
- `0` → Solo avisa qué productos se verían afectados (no elimina)
- `1` → Elimina el atributo **y** borra las implementaciones en productos afectados
- `2` → Elimina el atributo **e inyecta** el atributo directamente en los productos afectados

### `del_attribute_check_family_impact(attribute) → list[Product]`
Retorna los productos que quedarían sin cobertura si se elimina el atributo.

---

## Métodos de jerarquía de categorías

### `change_categorie_father(father_categorie, implementations)`
Mueve esta categoría como hija de otra.
- Detecta los atributos nuevos que hereda del padre y los aplica a los productos descendientes.
- `implementations`: dict `{attr_key: [(product_id, [{"variant_id": id, "value": value}])]}`.
- Retorna `{}` si exitoso o el mapa de impacto si falta información.

### `del_categorie(categorie, del_option)`
Elimina una subcategoría hija con tres modos:
- `0` → Inyecta los atributos sobrantes en los productos afectados
- `1` → Elimina las implementaciones huérfanas
- `2` → Solo retorna los productos impactados (sin modificar nada)

Retorna `False` si `categorie` no es hija directa de `self`.

---

## Métodos de productos

### `add_product(product) → bool`
Agrega un producto a la categoría. Lanza error si la categoría tiene subcategorías.

### `del_product(product) → bool`
Elimina un producto de la categoría.

### `create_product(product)`
Placeholder para crear producto (pendiente de implementación).

---

## Helpers internos de búsqueda

### `_add_attribute_look_up(attribute) → bool`
Busca **hacia arriba** (ancestros) si alguno ya tiene el atributo.

### `_add_attribute_look_down(attribute) → list[Product]`
Busca **hacia abajo** (descendientes) qué productos se verían afectados.

### `_add_attribute_product_check_family_impact(attribute) → list[Product] | None`
Combina look_up y look_down: retorna `None` si un ancestro ya lo cubre, o la lista de productos en riesgo.

### `_add_attribute_variant_impact_check(attribute, product_variant_implementations)`
Helper para `add_dinamic_attribute`. Valida cobertura exacta de productos y variantes.

### `_add_static_impact_check(attribute, implementations)`
Helper para `add_static_attribute`. Valida cobertura exacta de productos.

### `_del_attribute_look_up(category, attribute) → bool` *(staticmethod)*
Busca hacia arriba si algún ancestro tiene el atributo (versión estática).

### `_del_attribute_look_down(category, attribute) → list[Product]` *(staticmethod)*
Busca hacia abajo qué productos quedarían sin cobertura.

### `change_lookup_for_attributes(init_categorie) → set` *(staticmethod)*
Recolecta todos los atributos desde una categoría hacia arriba, sin duplicados.

---

## Serialización

### `to_json() → dict`
Serializa `id`, `name`, `attributes` y `subcategories` (recursivo hacia abajo).
- `father_categorie` y `products` no se serializan para evitar referencias circulares (`Product.to_json` embebe la categoría).

### `from_json(data: dict) → Category` *(classmethod)*
Reconstruye una categoría desde un diccionario, incluyendo sus `subcategories` de forma recursiva.
- A cada subcategoría reconstruida se le setea `father_categorie` apuntando al padre.
- `products` no se reconstruyen desde aquí.
