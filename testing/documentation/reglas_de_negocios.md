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

**R13** — Dado que un producto pertenece a una categoría → debe implementar todos los atributos estáticos que esa categoría exige (propios + heredados).

---

## Variantes

**R14** — Dado que se agrega una variante a un producto → debe implementar exactamente los atributos dinámicos que exige la categoría del producto (ni más ni menos). Si faltan o sobran, se rechaza.

**R15** — Dado que se intenta agregar una variante con la misma combinación de valores que otra ya existente en el mismo producto → se rechaza. Las variantes deben ser únicas por firma.

---

## Eventos de cambio (Impactos)

**E1 — Categoría gana padre nuevo**
Dado que una categoría pasa a tener un padre que antes no tenía → sus productos descendientes ganan los atributos que el nuevo padre aporta (menos los que la propia subcategoría ya define, según R4).

**E2 — Categoría cambia de padre**
Dado que una categoría cambia su padre → es la combinación de E3 (pierde los attrs del padre viejo) más E1 (gana los attrs del padre nuevo). Se calcula el delta completo.

**E3 — Categoría pierde su padre**
Dado que una categoría deja de tener padre → sus productos descendientes pierden todos los atributos que estaban llegando por herencia (los que venían de la ascendencia anterior, menos los que la propia subcategoría ya redefinía).

**E4 — Categoría agrega un atributo propio**
Dado que una categoría agrega un atributo → los productos en sus ramas descendientes deben incorporar ese atributo, excepto los productos cuya rama intermedia ya define ese mismo atributo (según R4).

**E5 — Categoría quita un atributo propio**
Dado que una categoría elimina un atributo → los productos en sus ramas descendientes pierden ese atributo, excepto los cuya rama intermedia lo redefine (misma lógica que E4 pero en sentido inverso).

**E6 — Producto cambia de categoría**
Dado que un producto se mueve a otra categoría → gana los atributos que la nueva categoría exige y que la anterior no exigía, y pierde los que la anterior exigía y la nueva no. El delta se calcula comparando `categoria_actual.get_full_attr_set()` vs `categoria_nueva.get_full_attr_set()`.

**E7 — Variante: consistencia con la categoría**
Dado que se agrega una variante → debe implementar exactamente los atributos dinámicos del `full_attr_set` de la categoría del producto. Se valida completitud (no faltan) y no exceso (no sobran).

---

## Pendiente / A definir

- ¿Qué pasa con las variantes existentes de un producto cuando ese producto cambia de categoría? (el modelo detecta el delta de la categoría en E6, pero no valida las variantes existentes)
- ¿Qué pasa con las variantes cuando una categoría cambia sus atributos dinámicos (E4/E5)?
- ¿Un producto puede existir sin variantes?
