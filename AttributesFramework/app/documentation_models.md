# Documentación de models.py

---

## Clases

### `Attribute`
Define la estructura de un atributo del catálogo (ej: Talle, Color, Material).

Tiene dos modos:
- **Estático** (`is_static=True`): información fija del producto (ej: material, temporada). Su valor vive en `Product.attributes_implementations`.
- **Dinámico** (`is_static=False`): opción elegible por el comprador (ej: talle, color). Su valor vive en `Variant.attribute_implementations`.

Tipos de dato soportados: `text`, `number`, `boolean`, `enum`. Para `enum`, los valores válidos deben cargarse con `add_enum_value` antes de usarlo.

#### Métodos

**`add_enum_value(value)`**
- Si `data_type != "enum"` → lanza `ValueError`.
- Si el valor ya existe en `enum_values` → lanza `ValueError`.
- Si es nuevo → lo agrega a `enum_values`.

**`check_value(value)`**
- `"text"` → `True` si `value` es `str`, `False` si no.
- `"number"` → `True` si `value` es `int` o `float`, `False` si no.
- `"boolean"` → `True` si `value` es `bool`, `False` si no.
- `"enum"` → `True` si `value` está en `enum_values`, `False` si no.
- tipo desconocido → lanza `ValueError`.

**`to_json()`**
- Serializa el atributo a dict. Si `enum_values` contiene objetos con `to_json`, los serializa también.

---

### `Attribute_factory`
Singleton / registro global de instancias de `Attribute` indexado por `key`. Garantiza que para una misma key siempre se devuelva la misma instancia, evitando duplicados cuando múltiples partes del sistema referencian el mismo atributo.

#### Métodos

**`get(key, name, data_type, id, is_static)`**
- Si la key ya existe en el registro → retorna la instancia existente (ignora los demás parámetros).
- Si la key no existe → crea un nuevo `Attribute`, lo registra y lo retorna.

**`clear()`**
- Vacía el registro global. Útil para tests o reinicio de estado.

---

### `AttributeImplementation`
Par concreto `(Attribute, valor)` que asigna un valor real a un atributo en un contexto específico.

- Si el atributo es estático → la implementación vive en `Product.attributes_implementations`.
- Si el atributo es dinámico → la implementación vive en `Variant.attribute_implementations`.

No valida el valor al construirse; la validación corre antes de crear la instancia.

#### Métodos

**`to_json()`**
- Serializa la implementación a dict, incluyendo el atributo anidado.

**`from_json(data)`**
- Si `"attribute"` es un dict → lo reconstruye como `Attribute`.
- Si ya es un objeto → lo usa directamente.
- Retorna una nueva instancia de `AttributeImplementation`.

---

### `Category`
Nodo en el árbol jerárquico de categorías.

Cada categoría puede tener:
- Un padre (`father_categorie`) del que hereda atributos recursivamente.
- Subcategorías hijas (`subcategories`) **O** productos directos (`products`), nunca ambos.
- Atributos propios (`attributes`) que aplican a todos los productos bajo ella.

La clase gestiona la propagación de cambios de atributos hacia arriba (ancestros) y hacia abajo (productos/variantes), garantizando consistencia en todo el árbol.

#### Métodos

**`get_attributes()`**
- Si tiene `father_categorie` → concatena los atributos propios con los del padre (recursivo).
- Si no tiene padre → retorna solo los propios.

**`get_attribute_keys()`**
- Igual que `get_attributes()` pero retorna un `set` de keys en lugar de lista de objetos.
- Útil para chequeos de pertenencia O(1).

**`_add_attribute_look_up(attribute)`** *(interno)*
- Busca recursivamente hacia arriba si algún ancestro tiene el atributo.
- Si self lo tiene → `True`.
- Si no tiene padre → `False`.
- Si tiene padre → delega al padre recursivamente.

**`_add_attribute_look_down(attribute)`** *(interno)*
- Busca recursivamente hacia abajo qué productos serían impactados al agregar el atributo.
- Si self ya tiene el atributo → `[]` (cubierto, no hay impacto debajo).
- Si tiene subcategorías → recorre cada una recursivamente y acumula.
- Si tiene productos directos → retorna todos.
- Si no tiene nada → `[]`.

**`_add_attribute_product_check_family_impact(attribute)`** *(interno)*
- Si algún ancestro ya lo tiene → `None` (sin impacto).
- Si nadie lo cubre arriba → busca hacia abajo y filtra los productos que no lo tienen propio. Retorna lista de productos en riesgo (puede ser `[]`).

**`_add_attribute_variant_impact_check(attribute, product_variant_implementations)`** *(interno)*
Helper de `add_dinamic_attribute`. Valida cobertura exacta de productos y variantes.
- Si un ancestro ya cubre → `None`.
- Si no hay productos en riesgo → agrega el atributo a self y retorna `{}`.
- Si `product_id` o `variant_id` duplicado → retorna lista de productos en riesgo.
- Si la cobertura de productos/variantes no es exacta → retorna lista de productos en riesgo.
- Si algún value no pasa `check_value` → retorna lista de productos en riesgo.
- Si todo matchea → retorna lista de tuplas `(variant, AttributeImplementation)` listas para aplicar.

**`add_dinamic_attribute(attribute, product_variant_implementations)`**
- Si el atributo es estático → lanza `ValueError`.
- Si un ancestro ya lo cubre o no hay impacto → aplica directo, retorna `{}`.
- Si la validación falla → retorna la lista de productos en riesgo.
- Si todo es válido → agrega `AttributeImplementation` a cada variante afectada, registra el atributo en self, retorna `{}`.

**`_add_static_impact_check(attribute, implementations)`** *(interno)*
Helper de `add_static_attribute`. Igual que `_add_attribute_variant_impact_check` pero a nivel producto (no variante).
- Si un ancestro ya cubre → `None`.
- Si no hay impacto → agrega el atributo a self y retorna `{}`.
- Si `product_id` duplicado o cobertura incompleta → retorna lista de productos en riesgo.
- Si algún value no pasa `check_value` → retorna lista de productos en riesgo.
- Si todo matchea → retorna lista de tuplas `(product, AttributeImplementation)` listas para aplicar.

**`add_static_attribute(attribute, implementations)`**
- Si el atributo no es estático → lanza `ValueError`.
- Si un ancestro ya lo cubre o no hay impacto → aplica directo, retorna `{}`.
- Si la validación falla → retorna la lista de productos en riesgo.
- Si todo es válido → agrega `AttributeImplementation` a cada producto afectado, registra el atributo en self, retorna `{}`.

**`_del_attribute_look_up(category, attribute)`** *(estático, interno)*
- Busca recursivamente hacia arriba si algún ancestro de `category` tiene el atributo.
- Si `category` lo tiene → `True`. Si no tiene padre → `False`. Si tiene padre → delega.

**`_del_attribute_look_down(category, attribute)`** *(estático, interno)*
- Busca hacia abajo qué productos quedarían sin cobertura si se elimina el atributo.
- Si `category` tiene el atributo propio → `[]` (cubierto aquí, no hay impacto debajo).
- Si tiene subcategorías → recorre recursivamente y acumula.
- Si tiene productos → retorna los que no tienen el atributo propio en `_attribute_keys`.
- Si no tiene nada → `[]`.

**`del_attribute_check_family_impact(attribute)`**
- Si un ancestro ya lo tiene → `[]` (sin impacto).
- Si tiene productos directos → retorna los que no tienen el atributo propio.
- Si tiene subcategorías → delega en `_del_attribute_look_down` para cada una y acumula.

**`del_attribute(attribute, delete_all=0)`**
- Si no hay productos perjudicados → elimina el atributo directo, retorna `[]`.
- `delete_all=0` y hay impacto → retorna lista de productos perjudicados, sin modificar nada.
- `delete_all=1` y hay impacto → elimina las implementaciones de ese atributo en los perjudicados, luego elimina el atributo de self, retorna `[]`.
- `delete_all=2` y hay impacto → inyecta el atributo como propio en cada producto perjudicado (para que no queden sin cobertura), luego elimina el atributo de self, retorna `[]`.

**`change_lookup_for_attributes(init_categorie)`** *(estático)*
- Recolecta todos los atributos desde `init_categorie` hacia arriba en un `set` sin duplicados.
- Usado por `change_categorie_father` para determinar qué atributos nuevos heredaría self.

**`change_categorie_father(father_categorie, implementations)`**
- Si `father_categorie` tiene productos directos → lanza `ValueError`.
- Si el nuevo padre no aporta atributos que impacten productos debajo de self → aplica directo, retorna `{}`.
- Si hay atributos nuevos que impactan variantes y `implementations` no los cubre exactamente → retorna `impact_map` (dict `attr → productos`).
- Si algún value es `None` o no pasa `check_value` → retorna `impact_map`.
- Si todo es válido → agrega `AttributeImplementation` a cada variante afectada, asigna `father_categorie`, retorna `{}`.

**`del_categorie(categorie, del_option)`**
- Si `categorie` no está en `subcategories` → retorna `False`.
- Si `categorie` no tiene atributos sobrantes (cubiertos por self o ancestros) → elimina directo, retorna `[]`.
- Si hay atributos sobrantes pero ningún producto los implementa → elimina directo, retorna `[]`.
- `del_option=2` → retorna lista de productos perjudicados sin modificar nada.
- `del_option=1` → elimina las implementaciones de los atributos sobrantes en los perjudicados, luego elimina la categoría, retorna `[]`.
- `del_option=0` → inyecta los atributos sobrantes como propios en cada producto perjudicado, luego elimina la categoría, retorna `[]`.

**`del_product(product)`**
- Si el code del producto no está en `_product_codes` → retorna `False`.
- Si existe → lo elimina de `products` y de `_product_codes`, retorna `True`.

**`add_product(product)`**
- Si self tiene subcategorías → lanza `ValueError`.
- Si el code ya existe en `_product_codes` → retorna `False`.
- Si es nuevo → lo agrega y retorna `True`.

---

### `Variant`
Combinación concreta de valores de atributos dinámicos para un producto.

Cada variante representa una "versión" del producto definida por sus atributos dinámicos (ej: talle=M + color=rojo). No tiene atributos propios; solo implementaciones que corresponden a los atributos dinámicos requeridos por el `Product` y su `Category`.

---

### `Product`
Entidad comercial concreta dentro de una `Category`.

Tiene dos capas de atributos:
- **Heredados** de la categoría (y sus ancestros): accesibles via `get_attributes()`.
- **Propios** (`self.attributes`): definidos directamente en el producto, no cubiertos por la jerarquía.

Los atributos se implementan de dos formas:
- Estáticos → `attributes_implementations` (un valor fijo por producto).
- Dinámicos → `Variant.attribute_implementations` (un valor por variante).

Requiere obligatoriamente una `Category`.

#### Métodos

**`is_attribute_in(attribute)`**
- Si `attribute.key` está en `_attribute_keys` (atributos propios) → `True`.
- Si no → `False`. No considera heredados de categoría.

**`get_attributes()`**
- Retorna atributos propios + los de la categoría (recursivo hacia arriba).

**`get_attribute_keys()`**
- Versión de `get_attributes()` que retorna solo un `set` de keys. Optimizada para chequeos de pertenencia.

**`add_dinamic_attribute(attribute, variant_options)`**
- Si el atributo ya está en los dinámicos necesarios (viene de categoría) → lo registra como propio, retorna `True`.
- Si `variant_id` duplicado en `variant_options` → retorna `False`.
- Si `variant_options` no cubre exactamente todas las variantes → retorna `False`.
- Si algún value no pasa `check_value` → retorna `False`.
- Si todo es válido → agrega `AttributeImplementation` a cada variante, registra el atributo, retorna `True`.

**`add_static_attribute(attribute, implementation)`**
- Si el value no pasa `check_value` → lanza `ValueError`.
- Si el atributo no está en los estáticos necesarios → retorna `False`.
- Si la implementación ya existe → lanza `ValueError`.
- Si todo es válido → agrega la implementación, retorna `True`.

**`del_attribute(attribute, delete_opt=0)`**
- Si el atributo no está en `_attribute_keys` → retorna `False`.
- Si la categoría (o algún ancestro) ya lo cubre → elimina de self sin impacto, retorna `[]`.
- Si no hay implementaciones huérfanas → elimina, retorna `[]`.
- `delete_opt=0` y hay impacto → retorna lista de `AttributeImplementation` (si estático) o `Variant` (si dinámico) afectadas, sin modificar nada.
- `delete_opt=1` y hay impacto → elimina las implementaciones y el atributo, retorna `[]`.

**`del_variant(variant_id)`**
- Si existe una variante con ese id → la elimina y retorna `True`.
- Si no existe → retorna `False`.

**`add_product_implementation(attribute_implementation)`**
- Si el atributo es dinámico → lanza `ValueError`.
- Si el value es inválido o el atributo no está suscripto → retorna `False`.
- Si ya existe una implementación para ese atributo → lanza `ValueError`.
- Si todo es válido → agrega la implementación.

**`_check_implementation(attr_impl)`** *(interno)*
- Si el value no pasa `check_value` → lanza `ValueError`.
- Si el atributo no está entre los estáticos necesarios → lanza `ValueError`.
- Si todo es válido → retorna `True`.

**`get_needed_atributes_implementations(is_static=False)`**
- `is_static=False` → retorna set de atributos dinámicos que cada variante debe implementar.
- `is_static=True` → retorna set de atributos estáticos que el producto debe implementar.
- Considera propios + heredados de categoría.

**`create_variant_by_implementations(implementations)`**
- Si hay atributo duplicado en `implementations` → imprime error, retorna `None`.
- Si el set de atributos no coincide exactamente con los dinámicos necesarios → imprime error, retorna `None`.
- Si algún value no pasa `check_value` → imprime error, retorna `None`.
- Si todo es válido → crea la `Variant` y la agrega al producto.

**`get_add_attribute_impact(attribute)`**
- Si el producto ya tiene el atributo propio → `None` (sin impacto).
- Si no lo tiene → retorna `{self.id: [v.id for v in self.variants]}` indicando qué variantes necesitan implementación.

---

## Visión holística

El sistema modela un catálogo de productos con atributos jerárquicos y variantes.

**Árbol de categorías**
`Category` forma un árbol: cada nodo puede tener subcategorías hijas o productos directos (nunca ambos). Los atributos definidos en un nodo se heredan hacia abajo por toda la rama. Esto permite que, por ejemplo, `Moda → Ropa → Remeras` herede todos los atributos acumulados sin repetirlos en cada nivel.

**Atributos**
Son los "tipos" de características (Talle, Color, Material...). Se definen una vez y se asignan a categorías o productos. `Attribute_factory` garantiza instancia única por key. Tienen dos sabores: estáticos (info fija del producto) y dinámicos (opciones combinables que definen variantes).

**Productos**
Viven en una categoría hoja (sin subcategorías). Heredan todos los atributos de su rama y pueden tener atributos propios adicionales. Los atributos estáticos se concretan en `attributes_implementations` (un valor fijo). Los dinámicos se concretan en las variantes.

**Variantes**
Cada variante es una combinación concreta de todos los atributos dinámicos del producto (propios + heredados). Ej: `{talle=M, color=rojo}`. Al crear una variante se exige que implemente exactamente los atributos dinámicos necesarios, ni más ni menos.

**Implementaciones**
Son el "valor concreto" de un atributo en un contexto:
- `Product.attributes_implementations` → atributo estático con su valor fijo.
- `Variant.attribute_implementations` → atributo dinámico con el valor de esa combinación.

**Flujo de cambios**
Cada vez que se agrega o elimina un atributo en una categoría, el sistema recorre el árbol hacia arriba (para ver si ya está cubierto por algún ancestro) y hacia abajo (para ver qué productos quedarían impactados). Solo cuando el llamador provee implementaciones que cubren exactamente todos los afectados, el sistema aplica los cambios de forma atómica. Si la cobertura es incompleta, retorna la lista de afectados para que el llamador decida cómo resolverlo.
