# Documentación — models.py

Este archivo es el núcleo del sistema. Toda la lógica de negocio vive acá. La app visual (app.py) es solo un consumidor: llama métodos del modelo, muestra lo que devuelven, y aplica los cambios que el modelo indica.

---

## Constantes

```python
DataTypes = ["text", "number", "boolean", "enum"]
```

Los cuatro tipos de dato posibles para un atributo.

---

## Clase `Attribute`

Representa la definición de un atributo reutilizable en el catálogo.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador único |
| `key` | str | Clave interna (única por atributo) |
| `name` | str | Nombre legible |
| `data_type` | str | Uno de DataTypes |
| `is_static` | bool | True = info de producto, False = opción de variante |
| `enum_values` | list | Solo si `data_type == "enum"` |

### Métodos

**`add_enum_value(value)`** — Agrega un valor posible. Rechaza si el atributo no es enum o si el valor ya existe.

**`check_value(value)`** — Valida que un valor sea del tipo correcto para el atributo.

**`__eq__` / `__hash__`** — Igualdad por `id` si tiene id, por identidad de objeto si no.

### Clase `Attribute_factory`

Singleton por key. Evita duplicar instancias del mismo atributo. No es el foco actual del desarrollo.

---

## Clase `AttributeImplementation`

Representa la asignación concreta de un valor a un atributo, en un producto o variante específico.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador |
| `attribute` | Attribute | Referencia al atributo definido |
| `value` | str | Valor concreto asignado |

No tiene lógica propia. Es un par (Attribute, valor).

---

## Clase `Category`

El árbol de categorías es la estructura central. Cada categoría puede tener atributos propios y hereda los de sus ancestros.

### Regla de exclusividad
Una categoría puede tener **subcategorías** o **productos**, nunca ambos.

### Campos relevantes

| Campo | Descripción |
|---|---|
| `attributes` | Atributos propios de esta categoría |
| `subcategories` | Hijos que son categorías |
| `products` | Hijos que son productos |
| `father_categorie` | Padre en el árbol |

### Métodos de lectura

**`get_ancestor_attrs() → set`** — Sube por el árbol y acumula todos los atributos de la ascendencia.

**`get_effective_inherited_attrs() → set`** — Attrs que llegan realmente desde arriba: ancestros menos lo que esta categoría ya define (evita solapamientos).

**`get_full_attr_set() → set`** — Todos los atributos visibles en este nivel: propios + heredados. Es el conjunto que rige a los productos de esta categoría.

### Métodos de mutación (validados)

**`add_subcategory(cat)`** — Valida exclusividad y ciclos. Setea `cat.father_categorie`.

**`add_product(product)`** — Valida exclusividad. **No setea `product.category`** ← gap.

**`set_father(father)`** — Setea `father_categorie` con validación de ciclo.

### Métodos de impacto (solo lectura — no mutan estado)

Todos retornan listas de pares `(set[Attribute], list[Product])`: qué atributos impactan a qué productos.

**`impact_on_add_father(new_father) → list[tuple]`** — E1: qué productos ganan atributos si esta categoría gana ese padre.

**`impact_on_remove_father() → list[tuple]`** — E3: qué productos pierden atributos si esta categoría pierde su padre actual. Llamar ANTES de mutar.

**`impact_on_change_father(new_father) → (list, list)`** — E2: combina E3 + E1. Devuelve `(impact_out, impact_in)`.

**`impact_on_add_attribute(attr) → list[tuple]`** — E4: qué productos deben incorporar `attr` porque esta categoría lo agregó.

**`impact_on_remove_attribute(attr) → list[tuple]`** — E5: qué productos deben quitar `attr` porque esta categoría lo eliminó.

**`compute_impact(attrs) → list[tuple]`** — Motor interno. Dado un set de attrs, desciende el árbol y devuelve qué attrs llegan a qué productos (filtrando lo que las subcategorías intermedias ya redefinen).

### Gaps del modelo (mutaciones que la app hace directo)

- No existe `remove_subcategory(cat)` → la app hace `cat.father_categorie.subcategories.remove(cat)` directo.
- No existe `remove_product(product)` → la app hace `cat.products.remove(product)` directo.
- `add_product` no actualiza `product.category` → la app hace `product.category = new_cat` directo.
- No existe setter de atributos → la app hace `cat.attributes = [...]` directo.

---

## Clase `Variant`

Representa una variante de un producto. Implementa los atributos dinámicos (is_static=False).

| Campo | Descripción |
|---|---|
| `attribute_implementations` | Lista de AttributeImplementation con atributos dinámicos |

No tiene referencia directa al producto. La relación es `producto.variants`.

---

## Clase `Product`

Representa un producto dentro de una categoría.

| Campo | Descripción |
|---|---|
| `code` | Código único del producto |
| `title` | Nombre |
| `price` | Precio |
| `description` | Descripción |
| `brand` | Marca |
| `category` | Categoría a la que pertenece |
| `attributes_implementations` | Implementaciones de atributos estáticos |
| `variants` | Lista de variantes |

### Métodos de lectura

**`_current_static_attrs() → set`** — Attrs estáticos actualmente implementados en el producto.

**`_current_dynamic_attrs() → set`** — Attrs dinámicos actualmente en `attributes_implementations` (ojo: los dinámicos reales están en las variantes, no acá).

**`get_required_dynamic_attrs() → set`** — Attrs dinámicos que exige la categoría actual del producto. Los que toda variante debe implementar.

### Métodos de impacto

**`impact_on_change_category(new_category) → (to_add, to_remove)`** — E6: compara `categoria_actual.get_full_attr_set()` vs `nueva_categoria.get_full_attr_set()`. Devuelve el delta completo (estáticos y dinámicos). Llamar ANTES de mutar `self.category`.

### Métodos de variantes (E7)

**`add_variant(variant)`** — Valida completitud (implementa exactamente los attrs dinámicos requeridos) y unicidad (no existe otra variante con la misma firma). Agrega si pasa.

**`remove_variant(variant)`** — Quita una variante existente.

**`clean_variants_after_attr_removal(removed_attrs) → (int, int)`** — E8: limpieza tras remoción de atributos. En orden: (1) quita las implementaciones de `removed_attrs` de todas las variantes, (2) elimina las variantes que queden vacías, (3) elimina variantes duplicadas que surjan. Retorna `(vaciadas_eliminadas, duplicadas_eliminadas)`. Llamar después de aplicar E5 o E6.

**`_check_variant_completeness(variant)`** — Valida que no falten ni sobren atributos dinámicos.

**`_check_variant_uniqueness(variant)`** — Valida que la combinación de valores no exista ya.

---

## Flujo de uso esperado

```
1. Llamar impact_on_*()  →  obtener qué va a cambiar
2. Mostrar el resultado al usuario / decidir si proceder
3. Aplicar los cambios indicados por el impacto
4. Llamar el método de mutación del modelo (add_subcategory, add_product, etc.)
5. Para lo que el modelo no cubre (removes): mutar directo, marcado como GAP
```

El modelo **computa** el impacto pero **no lo aplica**. La aplicación es responsabilidad del llamador.
