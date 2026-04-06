# Acciones y Reglas de Negocio — models.py

> Este documento cubre **todas las acciones posibles** sobre el modelo, con sus condiciones de entrada, estados posibles y efectos resultantes.

---

## Índice

1. [Atributo — agregar valor enum](#1-atributo--agregar-valor-enum)
2. [Categoría — agregar atributo dinámico](#2-categoría--agregar-atributo-dinámico)
3. [Categoría — agregar atributo estático](#3-categoría--agregar-atributo-estático)
4. [Categoría — eliminar atributo](#4-categoría--eliminar-atributo)
5. [Categoría — cambiar categoría padre](#5-categoría--cambiar-categoría-padre)
6. [Categoría — eliminar subcategoría hija](#6-categoría--eliminar-subcategoría-hija)
7. [Categoría — agregar producto](#7-categoría--agregar-producto)
8. [Categoría — eliminar producto](#8-categoría--eliminar-producto)
9. [Producto — agregar atributo dinámico](#9-producto--agregar-atributo-dinámico)
10. [Producto — agregar atributo estático](#10-producto--agregar-atributo-estático)
11. [Producto — eliminar atributo propio](#11-producto--eliminar-atributo-propio)
12. [Producto — agregar implementación estática directa](#12-producto--agregar-implementación-estática-directa)
13. [Producto — crear variante](#13-producto--crear-variante)
14. [Producto — eliminar variante](#14-producto--eliminar-variante)

---

## 1. Atributo — agregar valor enum

**Método:** `Attribute.add_enum_value(value)`

| Estado / Condición | Efecto |
|---|---|
| El atributo **no** es de tipo `enum` | `ValueError` — operación bloqueada |
| El valor **ya existe** en `enum_values` | `ValueError` — operación bloqueada |
| El valor **no existe** y el tipo es `enum` | El valor se agrega a la lista de valores posibles |

---

## 2. Categoría — agregar atributo dinámico

**Método:** `Category.add_dinamic_attribute(attribute, product_variant_implementations)`

> El atributo dinámico vive en las variantes (no es info fija del producto). `is_static=False`.

### Condición previa
- Si `attribute.is_static == True` → `ValueError`, operación bloqueada.

### Escenario A — algún ancestro ya tiene el atributo
- La búsqueda hacia arriba (`_add_attribute_look_up`) encuentra el atributo en algún ancestro.
- **Efecto:** no se hace nada, retorna `{}`. El árbol ya lo cubre.

### Escenario B — nadie lo tiene y no hay productos impactados hacia abajo
- Ningún ancestro lo tiene y ningún producto descendiente lo necesita (o todos ya lo tienen propio).
- **Efecto:** el atributo se agrega directamente a `self.attributes`. Retorna `{}`.

### Escenario C — hay productos descendientes que no tienen el atributo
La función requiere `product_variant_implementations` con la siguiente estructura:
```
[{"product_id": id, "variants": [{"variant_id": id, "value": value}, ...]}]
```

| Sub-condición | Efecto |
|---|---|
| Faltan productos en la lista (no coincide exactamente con los en riesgo) | Retorna lista de productos en riesgo, **sin modificar nada** |
| Hay `product_id` duplicados en la lista | Retorna lista de productos en riesgo, **sin modificar nada** |
| Faltan variantes de un producto (no coincide exactamente) | Retorna lista de productos en riesgo, **sin modificar nada** |
| Hay `variant_id` duplicados | Retorna lista de productos en riesgo, **sin modificar nada** |
| Un valor no es válido para el tipo de dato del atributo | Retorna lista de productos en riesgo, **sin modificar nada** |
| Cobertura exacta y valores válidos | Se agregan `AttributeImplementation` a cada variante afectada; el atributo se agrega a `self.attributes`. Retorna `{}` |

---

## 3. Categoría — agregar atributo estático

**Método:** `Category.add_static_attribute(attribute, implementations)`

> El atributo estático es info fija del producto (texto, número). `is_static=True`.

### Condición previa
- Si `attribute.is_static == False` → `ValueError`, operación bloqueada.

### Escenario A — algún ancestro ya tiene el atributo
- **Efecto:** no se hace nada, retorna `{}`.

### Escenario B — nadie lo tiene y no hay productos impactados
- **Efecto:** el atributo se agrega directamente a `self.attributes`. Retorna `{}`.

### Escenario C — hay productos descendientes que no tienen el atributo
La función requiere `implementations` con la siguiente estructura:
```
[{"product_id": id, "value": value}]
```

| Sub-condición | Efecto |
|---|---|
| Faltan productos o sobran en la lista | Retorna lista de productos en riesgo, **sin modificar nada** |
| Hay `product_id` duplicados | Retorna lista de productos en riesgo, **sin modificar nada** |
| Un valor no es válido para el tipo de dato del atributo | Retorna lista de productos en riesgo, **sin modificar nada** |
| Cobertura exacta y valores válidos | Se agregan `AttributeImplementation` a cada producto afectado; el atributo se agrega a `self.attributes`. Retorna `{}` |

---

## 4. Categoría — eliminar atributo

**Método:** `Category.del_attribute(attribute, delete_opt=0)`

### Paso 1 — cálculo de impacto (`del_attribute_check_family_impact`)

| Estado | Resultado del check |
|---|---|
| Algún ancestro tiene el atributo | Lista vacía `[]` (nadie queda sin cobertura) |
| La categoría tiene productos propios | Los productos que **no tienen** ese atributo propio quedan en riesgo |
| La categoría tiene subcategorías | Busca recursivamente hacia abajo: productos sin ese atributo propio quedan en riesgo |
| Una subcategoría tiene el atributo ella misma | Su rama no propaga el riesgo (corta la búsqueda hacia abajo) |

### Paso 2 — aplicación según `delete_opt`

| `delete_opt` | Condición | Efecto |
|---|---|---|
| cualquiera | No hay productos en riesgo (`[]`) | Elimina el atributo de `self.attributes` y `_attribute_keys`. Retorna `[]` |
| `0` (default) | Hay productos en riesgo | Solo retorna la lista de productos afectados, **sin modificar nada** |
| `1` | Hay productos en riesgo | Elimina el atributo; borra las `AttributeImplementation` del atributo en `product.attributes_implementations` (implementaciones estáticas). Retorna `None` implícitamente (sin `return` explícito) |
| `2` | Hay productos en riesgo | Elimina el atributo de la categoría; inyecta el atributo directamente en cada producto afectado (`product.attributes` y `_attribute_keys`). Retorna `[]` |

> **Limitación conocida — `delete_opt=1` y atributos dinámicos:** el código solo limpia `product.attributes_implementations`. Si el atributo eliminado es **dinámico**, las implementaciones que viven en `variant.attribute_implementations` de cada variante **no se eliminan**. Las variantes quedan con implementaciones huérfanas.

---

## 5. Categoría — cambiar categoría padre

**Método:** `Category.change_categorie_father(father_categorie, implementations)`

> Mueve `self` para ser hija del nuevo `father_categorie`.

### Condición previa
- Si `father_categorie` tiene productos propios (`len(products) > 0`) → `ValueError`, operación bloqueada.
  - Regla fundamental: un nodo no puede tener subcategorías y productos al mismo tiempo.

> **Limitación conocida — solo maneja atributos del nuevo padre como dinámicos:** `change_lookup_for_attributes` recolecta todos los atributos del nuevo padre (estáticos y dinámicos juntos), pero el código de aplicación siempre construye slots de variante (`variant_id`) para todos. Si algún atributo del nuevo padre es **estático**, la implementación igual se aplica a nivel variante, que no es su lugar correcto.

### Condición previa adicional — validación anti-ciclo
- Se recorre la cadena `father_categorie → father_categorie.father_categorie → ...` hacia arriba.
- Si `self` aparece en algún punto → `ValueError`. Previene que el árbol forme un ciclo que rompería toda búsqueda recursiva.

### Parámetro `del_option` — atributos huérfanos del padre anterior
Cuando `self` cambia de padre, los atributos que el padre viejo aportaba y el nuevo no cubre (y que `self` no tiene propios) quedan **huérfanos**. `del_option` controla qué se hace con ellos:

| `del_option` | Condición | Efecto |
|---|---|---|
| `0` (default) | Hay productos con implementaciones de atributos huérfanos | Retorna `orphan_impact` (`{attr: [products]}`), **sin modificar nada** |
| `0` | No hay impacto de huérfanos | Continúa normalmente |
| `1` | Siempre | Inyecta los atributos huérfanos directamente en `self.attributes` y `_attribute_keys`, para que los descendientes los sigan heredando. Las implementaciones ya existentes en los productos se mantienen intactas |
| `2` | Siempre | Elimina las implementaciones huérfanas de los productos afectados: estáticas en `product.attributes_implementations`, dinámicas en `variant.attribute_implementations` |

### Desvinculación del padre anterior
En todos los escenarios que llegan al punto de aplicar cambios, `self` se remueve de `old_father.subcategories`.

### Escenario A — el nuevo padre no aporta atributos nuevos a los descendientes de self
- Todos los atributos del nuevo padre ya están cubiertos por los productos de self (o no hay productos impactados).
- **Efecto:** se resuelven huérfanos según `del_option`, se desvincula del padre viejo, se vincula al nuevo. Retorna `{}`.

### Escenario B — el nuevo padre tiene atributos que los productos descendientes de self no tienen
Se recolectan todos los atributos del nuevo padre hacia arriba (sin duplicados). Para cada atributo nuevo, se determinan los productos impactados.

La función requiere `implementations` con la siguiente estructura:
```python
{
  attr_key: [(product_id, [{"variant_id": id, "value": value}, ...]), ...],
  ...
}
```

| Sub-condición | Efecto |
|---|---|
| Falta un atributo entero en `implementations` | Retorna `impact_map`, **sin modificar nada** |
| Falta un producto dentro de un atributo | Retorna `impact_map`, **sin modificar nada** |
| Falta una variante dentro de un producto | Retorna `impact_map`, **sin modificar nada** |
| Un valor es `None` o inválido para el tipo de dato | Retorna `impact_map`, **sin modificar nada** |
| Cobertura exacta y valores válidos | Aplica `AttributeImplementation` a cada variante afectada; luego realiza el cambio de padre. Retorna `{}` |

> **Nota:** solo los atributos de la nueva rama padre que los descendientes **no tienen** requieren implementación. Los que ya tienen los productos no se tocan.

---

## 6. Categoría — eliminar subcategoría hija

**Método:** `Category.del_categorie(categorie, del_option)`

> `self` es el padre; `categorie` es la hija a eliminar.

### Condición previa
- Si `categorie` no está en `self.subcategories` → retorna `False`.

### Paso 1 — cálculo de atributos sobrantes
Se calculan los atributos que aporta `categorie` y que **no** están cubiertos por `self` ni sus ancestros.

| Estado | Resultado |
|---|---|
| No hay atributos sobrantes | Elimina `categorie` de `self.subcategories` y desconecta `categorie.father_categorie`. Retorna `[]` |
| Hay atributos sobrantes, pero ningún producto los usa | Elimina `categorie` igualmente. Retorna `[]` |

### Paso 2 — si hay atributos sobrantes con productos impactados

> El `impact_map` solo incluye productos que **tienen implementación del atributo** (`attr.key in p._impl_keys`) pero **no tienen el atributo como propio** (`attr.key not in p._attribute_keys`). Estos son los productos que dependen de la categoría eliminada para cubrir ese atributo.

| `del_option` | Efecto |
|---|---|
| `0` | Migra la **definición** del atributo sobrante directamente al producto (`product.attributes` y `_attribute_keys`). Las implementaciones (`_impl_keys`) ya existentes se mantienen intactas. Luego elimina `categorie`. Retorna `[]` |
| `1` | Elimina las `AttributeImplementation` de los atributos sobrantes en `product.attributes_implementations` y actualiza `_impl_keys`. Luego elimina `categorie`. Retorna `[]` |
| `2` | Solo retorna la lista de productos impactados, **sin modificar nada** |

---

## 7. Categoría — agregar producto

**Método:** `Category.add_product(product)`

| Estado | Efecto |
|---|---|
| La categoría tiene subcategorías (`len(subcategories) > 0`) | `ValueError` — operación bloqueada. Regla: una categoría no puede tener subcategorías y productos al mismo tiempo |
| El producto ya está en la categoría (mismo `code`) | Retorna `False`, no se agrega |
| La categoría no tiene subcategorías y el producto no existe | Agrega el producto a `self.products` y `_product_codes`. Retorna `True` |

---

## 8. Categoría — eliminar producto

**Método:** `Category.del_product(product)`

| Estado | Efecto |
|---|---|
| El producto no está en la categoría | Retorna `False` |
| El producto está en la categoría | Lo elimina de `self.products` y `_product_codes`. Retorna `True` |

> **Nota:** este método solo desvincula el producto de la categoría. No elimina el objeto producto del sistema.

---

## 9. Producto — agregar atributo dinámico

**Método:** `Product.add_dinamic_attribute(attribute, variant_options)`

### Escenario A — el atributo ya está en los atributos necesarios del producto
- El atributo ya está cubierto (por la categoría o por el producto mismo).
- **Efecto:** se agrega directamente a `self.attributes` y `_attribute_keys`, **sin aplicar ninguna implementación a las variantes** (la categoría ya lo cubre). Retorna `True`.

### Escenario A' — el producto no tiene variantes y el atributo no está cubierto
- `variants_id` y `variant_options_id` son ambos sets vacíos → son iguales → pasa la validación.
- **Efecto:** el atributo se agrega a `self.attributes` sin ninguna implementación de variante (no hay variantes que actualizar). Retorna `True`.

### Escenario B — el atributo no está cubierto, hay variantes
Se requiere `variant_options`:
```
[{"variant_id": id, "value": value}, ...]
```

| Sub-condición | Efecto |
|---|---|
| Los `variant_id` no coinciden exactamente con todas las variantes del producto | Retorna `False`, **sin modificar nada** |
| Hay `variant_id` duplicados | Retorna `False`, **sin modificar nada** |
| Un valor no es válido para el tipo de dato del atributo | Retorna `False`, **sin modificar nada** |
| Cobertura exacta y valores válidos | Agrega `AttributeImplementation` a cada variante; agrega el atributo a `self.attributes`. Retorna `True` |

---

## 10. Producto — agregar atributo estático

**Método:** `Product.add_static_attribute(attribute, implementation)`

> `implementation` es un `AttributeImplementation` ya construido.

| Estado | Efecto |
|---|---|
| El valor no es válido para el tipo de dato del atributo | `ValueError` |
| El atributo no está suscripto en la categoría del producto (ni en sus ancestros) | Retorna `False` |
| El atributo ya está implementado en el producto | `ValueError` — implementación duplicada |
| El atributo está suscripto, valor válido, no duplicado | Agrega la implementación a `attributes_implementations` y `_impl_keys`. Retorna `True` |

---

## 11. Producto — eliminar atributo propio

**Método:** `Product.del_attribute(attribute, delete_opt=0)`

### Condición previa
- Si el atributo no está en `self._attribute_keys` (atributos propios del producto) → retorna `False`.

### Escenario A — la categoría (o un ancestro) ya cubre el atributo
- El producto lo tenía "redundantemente".
- **Efecto:** se elimina de `self.attributes` y `_attribute_keys`. No hay huérfanas. Retorna `[]`.

### Escenario B — el atributo no está cubierto por la categoría

#### Sub-escenario B1 — no hay implementaciones huérfanas
- No hay `AttributeImplementation` que dependan de este atributo.
- **Efecto:** se elimina directamente. Retorna `[]`.

#### Sub-escenario B2 — hay implementaciones huérfanas

| `delete_opt` | Tipo de atributo | Efecto |
|---|---|---|
| `0` | estático | Retorna lista de `AttributeImplementation` afectadas, **sin modificar nada** |
| `0` | dinámico | Retorna lista de `Variant` que tienen ese atributo implementado, **sin modificar nada** |
| `1` | estático | Elimina el atributo y borra todas sus `AttributeImplementation` del producto |
| `1` | dinámico | Elimina el atributo y borra las implementaciones de ese atributo en todas las variantes del producto |

---

## 12. Producto — agregar implementación estática directa

**Método:** `Product.add_product_implementation(attribute_implementation)`

| Estado | Efecto |
|---|---|
| El atributo de la implementación es dinámico (`is_static=False`) | `ValueError` — operación bloqueada |
| El valor no es válido para el tipo de dato | `ValueError` |
| El atributo no está suscripto en el producto o su categoría | Retorna `False` |
| El atributo ya está implementado en el producto | `ValueError` — implementación duplicada |
| Todo válido | Agrega a `attributes_implementations` y `_impl_keys` |

---

## 13. Producto — crear variante

**Método:** `Product.create_variant_by_implementations(implementations)`

> `implementations` es una lista de `AttributeImplementation`.

Los atributos necesarios se calculan del producto + su categoría (todos los dinámicos, `is_static=False`).

| Estado | Efecto |
|---|---|
| Hay atributos duplicados en la lista de implementaciones | Imprime error, retorna `None`. **Sin modificar nada** |
| Los atributos de las implementaciones no coinciden exactamente con los necesarios (faltan o sobran) | Imprime error, retorna `None`. **Sin modificar nada** |
| Un valor no es válido para el tipo de dato de su atributo | Imprime error, retorna `None`. **Sin modificar nada** |
| Exactamente los atributos necesarios, valores válidos, sin duplicados | Crea el objeto `Variant` y lo agrega a `self.variants` |

> **Limitación conocida — variantes duplicadas:** el código tiene un comentario `# una vez chequeado verificamos que no haya otra implementacion igual` pero **no lo implementa**. No se verifica si ya existe una variante con la misma combinación de valores. Es un TODO pendiente.

---

## 14. Producto — eliminar variante

**Método:** `Product.del_variant(variant_id)`

| Estado | Efecto |
|---|---|
| No existe ninguna variante con ese `variant_id` | Retorna `False` |
| Existe la variante | La elimina de `self.variants`. Retorna `True` |

> **Nota:** eliminar una variante no afecta los atributos del producto ni de la categoría.

---

## Reglas generales del modelo

### Árbol de categorías
- Una categoría **no puede tener subcategorías y productos al mismo tiempo**. Los productos solo viven en las hojas del árbol.
- La herencia de atributos es **hacia abajo y siempre recursiva**: un producto o subcategoría hereda todos los atributos de toda su cadena de ancestros.

### Atributos estáticos vs dinámicos
- **Estático** (`is_static=True`): info fija del producto (ej: peso, material). Se implementa a nivel producto.
- **Dinámico** (`is_static=False`): opción elegible por el cliente (ej: color, talle). Se implementa a nivel variante.

### Cobertura exacta
- Siempre que una acción requiera implementaciones de atributos en productos o variantes, la cobertura debe ser **exacta**: ni más ni menos que los afectados. Sobrar o faltar bloquea la operación.

### Caches internos
- `_attribute_keys`, `_product_codes`, `_impl_keys` son caches de acceso rápido.
- Se mantienen **manualmente** dentro de cada método.
- Modificar las listas directamente sin usar los métodos de la clase deja los caches desincronizados.

### Principio de no modificación ante validación fallida
- Toda validación se hace **antes** de aplicar cambios.
- Si alguna condición falla, se retorna el estado de riesgo/error y **no se modifica nada** del modelo.
