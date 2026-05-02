# Modelos de Dominio

Archivo: `models.js`

Modelos de dominio del catálogo. No dependen de ninguna capa de infraestructura ni de la UI. Son idénticos a los modelos del backend Python (`categories_fw/app/models.py`), traducidos a JS.

---

## Constantes

```js
const DataTypes = ["text", "number", "boolean", "enum"]
```

Buenas prácticas internas:
- `text` / `number` → siempre atributo de **producto** (estático)
- `boolean` → siempre atributo de **variante** (dinámico)
- `enum` → puede ser de producto o variante según `is_static`

---

## Attribute

Dimensión descriptiva del catálogo.

```js
new Attribute({ key, name, data_type, id = null, is_static = false })
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | `int\|null` | Asignado al persistir |
| `key` | `string` | Identificador único (`"color"`, `"talle"`) |
| `name` | `string` | Nombre visible |
| `data_type` | `string` | `"text"`, `"number"`, `"boolean"`, `"enum"` |
| `is_static` | `bool` | `true` = info de producto; `false` = dimensión de variante |
| `enum_values` | `array` | Valores posibles si `data_type === "enum"` |

### Métodos

| Método | Descripción |
|---|---|
| `add_enum_value(value)` | Agrega valor a la lista; lanza si ya existe o no es enum |
| `check_value(value)` | Valida que un valor sea del tipo correcto |
| `equals(other)` | Igualdad por `id` si está asignado, por referencia si no |
| `to_json()` | Serializa a objeto plano |
| `Attribute.from_json(data)` | Construye desde objeto plano |

---

## AttributeFactory

Singleton por `key`. Garantiza que no se creen dos instancias de `Attribute` con el mismo `key`.

```js
AttributeFactory.get(key, name, data_type, id, is_static) // → Attribute
AttributeFactory.clear()                                   // limpia cache
```

---

## AttributeImplementation

Par `(atributo, valor)` que concreta un atributo en un producto o variante.

```js
new AttributeImplementation({ attribute, value, id = null })
```

| Campo | Tipo | Descripción |
|---|---|---|
| `attribute` | `Attribute` | Referencia al atributo |
| `value` | `any` | Valor concreto |

### Métodos

| Método | Descripción |
|---|---|
| `to_json()` | Serializa |
| `AttributeImplementation.from_json(data)` | Construye desde objeto plano |

---

## Category

Nodo del árbol de categorías. Puede tener subcategorías **o** productos, nunca ambos.

```js
new Category({ name, id, attributes, subcategories, father_categorie, products })
```

### Predicados de consulta (sin throw, sin mutación)

Usados por el Gestor para preguntar antes de actuar.

| Método | Retorna | Descripción |
|---|---|---|
| `can_add_subcategory()` | `string\|null` | Error legible si ya tiene productos; `null` si se puede |
| `can_add_product()` | `string\|null` | Error legible si ya tiene subcategorías; `null` si se puede |

### Mutaciones seguras

| Método | Descripción |
|---|---|
| `add_subcategory(cat)` | Valida ciclo + exclusividad, agrega y enlaza padre |
| `add_product(product)` | Valida exclusividad, agrega |
| `set_father(father)` | Valida ciclo, actualiza `father_categorie` |

### Navegación de atributos

| Método | Retorna | Descripción |
|---|---|---|
| `get_ancestor_attrs()` | `AttributeSet` | Todos los attrs de todos los ancestros |
| `get_effective_inherited_attrs()` | `AttributeSet` | Ancestros menos los que `self` ya define |
| `get_full_attr_set()` | `AttributeSet` | Propios + heredados efectivos |

### Métodos de impacto (sin mutación)

Todos retornan `Array<[AttributeSet, Product[]]>`. Cada par representa los atributos que llegan a ese grupo de productos tras filtrar lo que las ramas intermedias ya definen.

| Método | Evento | Descripción |
|---|---|---|
| `impact_on_add_father(new_father)` | E1 | Attrs nuevos que bajarían a los productos de `self` |
| `impact_on_remove_father()` | E3 | Attrs heredados que se perderían |
| `impact_on_change_father(new_father)` | E2 | Retorna `[impacto_salida, impacto_entrada]` |
| `impact_on_add_attribute(attr)` | E4 | Productos que deberían implementar `attr` |
| `impact_on_remove_attribute(attr)` | E5 | Productos que deberían perder la implementación |

---

## Product

Hoja del árbol. Pertenece a exactamente una categoría hoja.

```js
new Product({ code, title, price, description, brand, id, category, attributes_implementations, variants })
```

`category` es obligatorio — lanza si es `null`.

### Métodos

| Método | Retorna | Descripción |
|---|---|---|
| `impact_on_change_category(new_category)` | `[to_add, to_remove]` | Delta de attrs estáticos al cambiar categoría |
| `get_required_dynamic_attrs()` | `AttributeSet` | Attrs dinámicos que toda variante debe implementar |
| `add_variant(variant)` | — | Valida completitud + unicidad, agrega |
| `remove_variant(variant)` | — | Lanza si no pertenece al producto |

### Firma de variante

La unicidad se determina por el string `"key1:val1|key2:val2|..."` (sorted) sobre todas las implementaciones de la variante.

---

## Variant

Combinación de valores de atributos dinámicos para un producto.

```js
new Variant({ attribute_implementations, id })
```

Solo implementa atributos con `is_static = false`. El conjunto de atributos requeridos lo determina la categoría del producto padre vía `get_required_dynamic_attrs()`.

---

## AttributeSet

Set de `Attribute` con igualdad semántica: por `id` si está asignado, por referencia de objeto si no. Necesario porque JS no tiene operator overloading.

```js
const set = new AttributeSet([attr1, attr2])
set.add(attr)
set.has(attr)        // → bool
set.size             // → number
set.values()         // → IterableIterator<Attribute>
set.difference(other) // → AttributeSet
set.clone()          // → AttributeSet
```

---

## Exports

```js
export {
  DataTypes,
  Attribute, AttributeFactory, AttributeImplementation, AttributeSet,
  Category,
  Variant,
  Product,
}
```
