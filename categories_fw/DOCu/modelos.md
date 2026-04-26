# Modelos de dominio

Todos los modelos viven en `app/models.py`. No dependen de ninguna capa de infraestructura.

---

## Attribute

Representa una dimensión descriptiva del catálogo.

```python
Attribute(key, name, data_type, id=None, is_static=False)
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int\|None` | Asignado por la base al persistir |
| `key` | `str` | Identificador único (`"color"`, `"talle"`) |
| `name` | `str` | Nombre visible |
| `data_type` | `str` | `"text"`, `"number"`, `"boolean"`, `"enum"` |
| `is_static` | `bool` | `True` = info de producto; `False` = dimensión de variante |
| `enum_values` | `list` | Valores posibles si `data_type == "enum"` |

### Métodos

| Método | Descripción |
|---|---|
| `add_enum_value(value)` | Agrega un valor válido a la lista; lanza si ya existe o no es enum |
| `check_value(value)` | Valida que un valor sea del tipo correcto |

### Igualdad

Dos `Attribute` son iguales si tienen el mismo `id` (cuando está asignado); caso contrario, por identidad de objeto. Esto permite usarlos en sets.

---

## AttributeImplementation

Par `(atributo, valor)` que concreta un atributo en un producto o variante.

```python
AttributeImplementation(attribute, value, id=None)
```

Un `product_implementation` almacena atributos estáticos del producto.  
Un `variant_implementation` almacena atributos dinámicos de la variante.

---

## Category

Nodo del árbol de categorías. Puede tener subcategorías **o** productos, nunca ambos.

```python
Category(name, id=None, attributes=[], subcategories=[], father_categorie=None, products=[])
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int\|None` | Asignado por la base |
| `name` | `str` | Nombre de la categoría |
| `attributes` | `list[Attribute]` | Atributos propios (no heredados) |
| `subcategories` | `list[Category]` | Hijos directos |
| `father_categorie` | `Category\|None` | Padre directo |
| `products` | `list[Product]` | Productos (solo si es hoja) |

### Validadores internos

| Método | Cuándo se llama | Qué verifica |
|---|---|---|
| `_check_no_cycle(candidate_child)` | Antes de establecer padre | Que `candidate_child` no sea ya ancestro de `self` |
| `_check_exclusive_children(adding)` | Antes de agregar subcategoría o producto | Que no haya mezcla de tipos de hijos |

### Mutaciones seguras

| Método | Descripción |
|---|---|
| `add_subcategory(cat)` | Valida ciclo + exclusividad, luego agrega y enlaza padre |
| `add_product(product)` | Valida exclusividad, luego agrega |
| `set_father(father)` | Valida ciclo desde el nuevo padre, actualiza `father_categorie` |

### Navegación de atributos

| Método | Retorna | Descripción |
|---|---|---|
| `get_ancestor_attrs()` | `set[Attribute]` | Todos los attrs de todos los ancestros (sin filtrar) |
| `get_effective_inherited_attrs()` | `set[Attribute]` | Ancestros menos los que `self` ya define |
| `get_full_attr_set()` | `set[Attribute]` | Propios + heredados efectivos |

### Métodos de impacto (sin mutación)

Todos retornan pares `(set[Attribute], list[Product])`. Cada par representa los atributos que sobreviven hasta ese grupo de productos tras filtrar lo que las ramas intermedias ya definen.

| Método | Evento | Descripción |
|---|---|---|
| `impact_on_add_father(new_father)` | E1 | Attrs nuevos que bajarían a los productos de `self` |
| `impact_on_remove_father()` | E3 | Attrs heredados que se perderían |
| `impact_on_change_father(new_father)` | E2 | Retorna `(impacto_salida, impacto_entrada)` |
| `impact_on_add_attribute(attr)` | E4 | Productos que deberían implementar `attr` |
| `impact_on_remove_attribute(attr)` | E5 | Productos que deberían perder la implementación |

### Algoritmo de impacto

```
compute_impact(attrs):
  si self tiene productos → devuelve [(attrs, productos)]
  por cada subcategoría:
    sub_remaining = attrs - sub.attributes   # la rama ya define estos attrs
    si sub_remaining:
      descender recursivamente con sub_remaining
```

Las ramas que ya definen un atributo "absorben" ese atributo y sus productos no se ven afectados.

---

## Product

Hoja del árbol. Pertenece a exactamente una categoría hoja.

```python
Product(code, title, price, description, brand, id=None, category=None,
        attributes_implementations=[], variants=[])
```

| Campo | Tipo | Descripción |
|---|---|---|
| `code` | `str` | SKU único |
| `title` | `str` | Nombre del producto |
| `price` | `float` | Precio |
| `category` | `Category` | Obligatorio; no puede ser `None` |
| `attributes_implementations` | `list[AttributeImplementation]` | Implementaciones de attrs estáticos |
| `variants` | `list[Variant]` | Variantes del producto |

### Métodos de impacto

| Método | Retorna | Descripción |
|---|---|---|
| `impact_on_change_category(new_category)` | `(to_add, to_remove)` | Delta de attrs estáticos al cambiar de categoría |
| `get_required_dynamic_attrs()` | `set[Attribute]` | Attrs dinámicos que toda variante debe implementar |

### Gestión de variantes

| Método | Descripción |
|---|---|
| `add_variant(variant)` | Valida completitud + unicidad, luego agrega |
| `remove_variant(variant)` | Lanza si la variante no pertenece al producto |
| `_check_variant_completeness(variant)` | Verifica que la variante implemente exactamente los attrs dinámicos requeridos |
| `_check_variant_uniqueness(variant)` | Verifica que no exista una variante con la misma combinación de valores |

### Firma de variante

La unicidad se determina por `frozenset((attr.key, value))` sobre todas las implementaciones de la variante.

---

## Variant

Combinación de valores de atributos dinámicos para un producto.

```python
Variant(attribute_implementations=[], id=None)
```

Solo implementa atributos **dinámicos** (`is_static=False`). El set de atributos requeridos lo determina la categoría del producto padre vía `get_required_dynamic_attrs()`.
