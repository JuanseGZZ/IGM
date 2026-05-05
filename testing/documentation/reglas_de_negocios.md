# Reglas de Negocio

Formato: **dado [situación] → se actúa como [consecuencia]**

---

## Categorías

**R1** — Dado que se intenta agregar una subcategoría a una categoría que ya tiene productos → se rechaza. Una categoría tiene subcategorías O productos, nunca ambos.

**R2** — Dado que se intenta agregar un producto a una categoría que ya tiene subcategorías → se rechaza. Misma exclusividad del R1.

**R3** — Dado que se intenta hacer que A sea hijo de B, siendo B ya descendiente de A → se rechaza. No pueden existir ciclos en el árbol.

**R4** — Dado que una categoría tiene atributos propios y un ancestro define el mismo atributo → el atributo de la subcategoría prevalece. El ancestro no propaga ese atributo hacia abajo a través de ella.

**R5** — Dado que se consulta el conjunto completo de atributos de una categoría → se devuelve la unión de sus atributos propios más todos los atributos heredados de sus ancestros (respetando R4).

---

## Atributos

**R6** — Dado que un atributo tiene `is_static = True` → se implementa a nivel producto. Es información descriptiva del producto (ej: material, peso).

**R7** — Dado que un atributo tiene `is_static = False` → se implementa a nivel variante. Es una opción elegible que distingue variantes entre sí (ej: color, talle).

**R8** — Dado que el tipo de dato es `text` o `number` → el atributo es siempre estático (de producto).

**R9** — Dado que el tipo de dato es `boolean` → el atributo es siempre dinámico (de variante).

**R10** — Dado que el tipo de dato es `enum` → puede ser estático o dinámico según `is_static`. Si es de producto, se muestra como info. Si es de variante, se muestra como opción elegible.

**R11** — Dado que un atributo es `enum` y se intenta agregar un valor que ya existe → se rechaza.

---

## Productos

**R12** — Dado que se crea un producto → debe pertenecer a una categoría. No existe producto sin categoría.

**R13** — Dado que un producto pertenece a una categoría → debe implementar exactamente los atributos estáticos que esa categoría exige (propios + heredados): ni faltan ni sobran. Se valida al agregarlo con `add_product`.

**R13b** — Dado que una variante pertenece a un producto → debe implementar exactamente los atributos dinámicos que exige la categoría del producto: ni faltan ni sobran. Los atributos estáticos no van en variantes. Se valida al agregarla con `add_variant`.

---

## Variantes

**R14** — Dado que se agrega una variante a un producto → debe implementar exactamente los atributos dinámicos que exige la categoría del producto (ni más ni menos). Si faltan o sobran, se rechaza.

**R15** — Dado que se intenta agregar una variante con la misma combinación de valores que otra ya existente en el mismo producto → se rechaza. Las variantes deben ser únicas por firma.

---

## Eventos de cambio (Impactos)

**E1 — Categoría gana padre nuevo**
Dado que una categoría pasa a tener un padre que antes no tenía → sus productos descendientes ganan los atributos que el nuevo padre aporta (menos los que la propia subcategoría ya define, según R4).

**E2 — Categoría cambia de padre**
Dado que una categoría cambia su padre → se calcula el **delta neto**: qué attrs se heredaban antes vs qué attrs se heredarán con el nuevo padre. Si un attr sigue llegando por otra rama del árbol (ej: el nuevo padre también es descendiente del mismo ancestro que aportaba ese attr), no hay impacto real para ese attr. Solo impactan los attrs que realmente aparecen o desaparecen del conjunto heredado.

**E3 — Categoría pierde su padre**
Dado que una categoría deja de tener padre → sus productos descendientes pierden todos los atributos que estaban llegando por herencia (los que venían de la ascendencia anterior, menos los que la propia subcategoría ya redefinía).

**E4 — Categoría agrega un atributo propio**
Dado que una categoría agrega un atributo → los productos en sus ramas descendientes deben incorporar ese atributo, excepto los productos cuya rama intermedia ya define ese mismo atributo (según R4).

**E5 — Categoría quita un atributo propio**
Dado que una categoría elimina un atributo → los productos en sus ramas descendientes pierden ese atributo, excepto los cuya rama intermedia lo redefine (misma lógica que E4 pero en sentido inverso). **Si un ancestro de la categoría ya define ese mismo atributo, no hay impacto: el atributo seguirá propagándose desde el ancestro.**

**E6 — Producto cambia de categoría**
Dado que un producto se mueve a otra categoría → gana los atributos que la nueva categoría exige y que la anterior no exigía, y pierde los que la anterior exigía y la nueva no. El delta se calcula comparando `categoria_actual.get_full_attr_set()` vs `categoria_nueva.get_full_attr_set()`.

**E7 — Variante: consistencia con la categoría**
Dado que se agrega una variante → debe implementar exactamente los atributos dinámicos del `full_attr_set` de la categoría del producto. Se valida completitud (no faltan) y no exceso (no sobran).

**E8 — Limpieza de variantes tras remoción de atributos**
Dado que ciertos atributos dejan de aplicar a un producto (por E5 o E6) → se ejecutan tres pasos en orden:
1. Se quitan de cada variante las implementaciones de los atributos removidos.
2. Las variantes que queden sin ninguna implementación se eliminan.
3. Las variantes que queden con la misma firma (misma combinación de valores) se deduplicación: se conserva la primera, se eliminan las demás.

**R16** — Dado que una variante queda sin implementaciones tras una remoción de atributos → se elimina automáticamente.

**R17** — Dado que dos variantes quedan con la misma combinación de valores tras una remoción de atributos → se elimina la duplicada. No pueden existir dos variantes con la misma firma en el mismo producto, ni al crearlas ni tras modificaciones.

---

## Atributos — restricciones de ciclo de vida

**R18** — Dado que se intenta eliminar un `Attribute` del catálogo → se verifica si está en uso (en atributos de alguna categoría, en implementaciones de productos, o en implementaciones de variantes). Si está en uso, se bloquea y se muestra dónde. Si el usuario confirma la eliminación forzada, se quitan todas las implementaciones, se eliminan las variantes que queden vacías, y luego se elimina el atributo.

**R19** — Dado que se intenta cambiar el campo `is_static` de un atributo que ya está en uso → se rechaza. El atributo ya no puede cambiar de naturaleza (estático ↔ dinámico). Si se necesita otro comportamiento, hay que crear un atributo nuevo.

**R20** — Dado que se intenta crear o guardar un atributo de tipo `enum` sin ningún valor definido → se rechaza. Un enum sin valores nunca podría pasar `check_value`.

**R21** — Dado que existe una categoría raíz → no puede ser eliminada, no puede ser movida como hija de otra categoría, y no puede tener categorías hermanas. Solo puede tener hijos (subcategorías o productos, sujeto a R1/R2). Esta es una categoría especial de la que depende todo el árbol.

---

## Pendiente / A definir

- ¿Un producto puede existir sin variantes?
  si, un producto puede no tener variantes. luego otro sistema lo mostrara o no pero en nuestro sistema puede vivir sin variantes.

---

## A chequear — del archivo original (`categories_fw/app/reglas`)

Reglas que escribiste antes. Las que ya están cubiertas se marcan. Las que faltan o tienen dudas quedan abiertas.

| Regla original | Estado |
|---|---|
| Categoría agrega padre → ver todos los attrs del padre y ascendencia, recorrer ramas filtrando lo que las subcategorías intermedias redefinen, impactar productos al final de cada camino | ✓ Cubierto — E1 + `compute_impact` + `_descend_impact` |
| Categoría cambia de padre → verificar salida Y entrada, ambas son impactos | ✓ Cubierto — E2 (delta neto: losing / gaining) |
| Categoría elimina padre → solo la salida | ✓ Cubierto — E3 |
| Categoría agrega atributo → solo ese attr, recorre ramas, impacta productos | ✓ Cubierto — E4 |
| Categoría elimina atributo → solo ese attr, mismo recorrido | ✓ Cubierto — E5 |
| Producto cambia de categoría → recolecta attrs implementados, compara con nueva herencia, agrega los que faltan y elimina los que sobran | ✓ Parcialmente — E6 calcula delta correcto. **⚠ FALTA**: cuando `to_add` incluye attrs dinámicos, hay que agregarlos a las variantes, no al producto |
| Producto agrega y quita variantes → mira ancestros e implementa necesidades | ✓ Cubierto — E7 (`add_variant` valida completitud) y E8 (limpieza) |
| Atributos estáticos → producto / dinámicos → variante | ✓ Cubierto — R6, R7, R8, R9, R10 |
| Categorías: hijos son productos O categorías, no ambos; no cíclicas | ✓ Cubierto — R1, R2, R3 |
| Productos: solo implementan estáticos heredados | ✓ Cubierto — R13, `_check_product_completeness` |
| Variantes: solo dinámicos heredados, combinación única | ✓ Cubierto — R13b, R14, R15, `_check_variant_completeness` |

---

## Casos verificados (ex "A chequear")

Preguntas que surgieron al revisar el modelo. Todas respondidas y aplicadas.

| Caso                                      | Regla resultante                                                                                                                               | Estado                              |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| AC-1 — E6 con `to_add` dinámicos          | Dinámicos van a variantes, no al producto. Se agregan con value="" a cada variante existente. UI pendiente: formulario para completar valores. | ✓ Implementado                      |
| AC-2 — E4 con attrs dinámicos             | Mismo tratamiento que AC-1: `_apply_add_impls` separa estáticos (producto) y dinámicos (variantes). UI pendiente: formulario.                  | ✓ Implementado                      |
| AC-3 — Eliminar un Attribute en uso       | → R18: bloquear + confirmar + cascada de eliminación + limpiar variantes vacías.                                                               | ✓ Implementado                      |
| AC-4 — Cambiar `is_static` si está en uso | → R19: no se puede cambiar. Crear otro atributo.                                                                                               | ✓ Implementado                      |
| AC-5 — Enum sin valores                   | → R20: no se puede crear/guardar. Mínimo un valor requerido.                                                                                   | ✓ Implementado                      |
| AC-6 — Categoría raíz                     | → R21: no se puede eliminar, mover ni agregar hermanos. Solo tiene hijos.                                                                      | ✓ Documentado (app ya lo bloqueaba) |
| AC-7 — R4 en reversa (E5 redundancia)     | Si un ancestro ya tiene el attr, quitar el attr propio no genera impacto.                                                                      | ✓ Implementado en modelo            |
| AC-8 — Firma de variante                  | Las variantes solo tienen attrs dinámicos heredados. La firma es el conjunto de (attr, valor). E8 ya maneja deduplicación correctamente.       | ✓ Documentado (código ya correcto)  |

**UI pendiente (AC-1/AC-2):** cuando se agregan attrs dinámicos a productos con variantes existentes, las variantes quedan con value="" para esos attrs. Falta formulario que muestre: por atributo → por producto → sus variantes, para que el usuario complete los valores.