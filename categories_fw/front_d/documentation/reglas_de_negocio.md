# Reglas de Negocio — front_d

Lista de reglas extraídas del código (`models.js`, `Gestor.js`) y la documentación.
Para cada una respondé: **si** / **no** / **parcial** (con corrección).

---

## Índice

| Bloque | Tema | Reglas |
|---|---|---|
| 1 | Estructura del árbol visual (qué puede ser hijo de qué) | 1–4 |
| 2 | Exclusividad de hijos en categoría | 5–7 |
| 3 | Ciclos y restricciones de movimiento | 8–10 |
| 4 | Atributos: tipos de datos | 11–14 |
| 5 | Atributos: estáticos vs dinámicos | 15–16 |
| 6 | Atributos de tipo enum | 17–18 |
| 7 | Herencia de atributos y shielding | 19–22 |
| 8 | Agregar producto | 23–24 |
| 9 | Agregar variante | 25–28 |
| 10 | Agregar atributo a una categoría | 29–31 |
| 11 | Quitar atributo de una categoría | 32–36 |
| 12 | Mover categoría | 37–40 |
| 13 | Mover producto | 41–42 |
| 14 | Eliminación en cascada | 43–45 |
| 15 | Persistencia en localStorage | 46–48 |
| 16 | Identificación de atributos | 49–50 |

---

## Bloque 1 — Estructura del árbol visual

**1.** Solo puede existir una categoría en el nivel raíz del canvas (hijo directo del root virtual). Si ya hay una, el botón "Agregar" al nivel raíz está bloqueado.

**2.** Una categoría solo puede ser hija de otra categoría (o del root). No puede ser hija de un producto ni de una variante.

**3.** Un producto solo puede ser hijo de una categoría. No puede ser hijo del root, de otro producto ni de una variante.

**4.** Una variante solo puede ser hija de un producto. No puede ser hija de una categoría ni del root.

---

## Bloque 2 — Exclusividad de hijos en categoría

**5.** Una categoría puede contener subcategorías **o** productos, pero nunca ambos al mismo tiempo.

**6.** Si una categoría ya tiene al menos un producto, agregar una subcategoría está bloqueado.

**7.** Si una categoría ya tiene al menos una subcategoría, agregar un producto está bloqueado.

---

## Bloque 3 — Ciclos en la jerarquía

**8.** No se puede hacer que una categoría sea descendiente de sí misma (ciclo detectado y bloqueado).

**9.** No se puede mover un nodo (categoría o producto) dentro de sí mismo ni dentro de uno de sus propios descendientes.

**10.** No se puede mover un nodo al nivel raíz mediante drag & drop (ese nivel solo se puede usar desde el botón "Agregar raíz").

---

## Bloque 4 — Atributos: tipos de datos

**11.** Los tipos de dato válidos para un atributo son exactamente cuatro: `text`, `number`, `boolean`, `enum`.

**12.** Por convención interna, `text` y `number` son siempre atributos de **producto** (`is_static = true`).

**13.** Por convención interna, `boolean` es siempre atributo de **variante** (`is_static = false`).

**14.** `enum` puede ser de producto o de variante según el valor de `is_static`: si es estático se muestra como información del producto; si es dinámico se muestra como opción seleccionable para la variante.

---

## Bloque 5 — Atributos: estáticos vs dinámicos

**15.** `is_static = true` → el atributo se implementa a nivel de **producto** (aplica a todos los ejemplares iguales del producto).

**16.** `is_static = false` → el atributo es dinámico y se implementa a nivel de **variante** (cada variante puede tener un valor diferente).

---

## Bloque 6 — Atributos de tipo enum

**17.** Solo se pueden agregar valores a un atributo si su `data_type` es `"enum"`. Intentar hacerlo en otro tipo lanza error.

**18.** Los valores posibles de un atributo enum deben ser únicos dentro del mismo atributo; no se puede agregar un valor que ya existe.

---

## Bloque 7 — Herencia de atributos

**19.** Los atributos definidos en una categoría se heredan a todas las subcategorías y productos descendientes.

**20.** Un producto debe implementar todos los atributos **estáticos** del conjunto completo de su cadena de categorías (propios de la categoría + heredados de los ancestros).

**21.** Una variante debe implementar todos los atributos **dinámicos** del conjunto completo de categorías del producto padre.

**22.** Si una categoría intermedia entre un ancestro y un producto ya define el mismo atributo, ese producto (y sus variantes) queda "shieldeado": los cambios en el ancestro no lo impactan porque ya recibe el atributo de la categoría intermedia.

---

## Bloque 8 — Agregar producto

**23.** Al agregar un producto a una categoría que tiene atributos estáticos (propios o heredados), el sistema muestra un formulario para que el usuario complete el valor de cada atributo estático antes de confirmar (flujo aditivo).

**24.** Si la categoría no tiene atributos estáticos, el producto se agrega sin formulario adicional (flujo "none").

---

## Bloque 9 — Agregar variante

**25.** Para poder crear una variante en un producto, la cadena de categorías del producto debe definir al menos un atributo dinámico. Si no existe ninguno, la operación se bloquea con mensaje explicativo.

**26.** Al crear una variante, el sistema muestra un formulario con todos los atributos dinámicos requeridos por la categoría del producto (flujo aditivo siempre que haya attrs dinámicos).

**27.** Una variante debe implementar exactamente los atributos dinámicos requeridos: ni más ni menos. Implementaciones faltantes o de más son inválidas.

**28.** No pueden existir dos variantes de un mismo producto con la misma combinación de valores. La unicidad se determina por la firma `"key1:val1|key2:val2|..."` (sorted).

---

## Bloque 10 — Agregar atributo a una categoría

**29.** Al agregar un atributo **estático** a una categoría, todos los productos en su subárbol (no shieldeados por una categoría intermedia que ya define ese atributo) deben implementar el valor del atributo nuevo. El sistema muestra un input por cada producto afectado (flujo aditivo).

**30.** Al agregar un atributo **dinámico** a una categoría, todas las variantes existentes en su subárbol (en productos no shieldeados) deben recibir una implementación del atributo nuevo. El sistema muestra un input por cada variante afectada (flujo aditivo).

**31.** Si al agregar un atributo (estático o dinámico) no hay productos ni variantes impactados en el subárbol, la operación se aplica sin formulario adicional (flujo "none").

---

## Bloque 11 — Quitar atributo de una categoría

**32.** Si el atributo que se quita sigue estando definido en algún **ancestro** de la categoría editada, quitarlo de esta categoría no tiene ningún impacto (los descendientes siguen recibiéndolo por herencia). Flujo "none".

**33.** Si el atributo deja de estar en la herencia, todos los productos y variantes que lo implementaban lo pierden. El sistema muestra la lista de elementos afectados antes de confirmar (flujo destructivo).

**34.** Si al quitar el atributo una variante queda con **cero** implementaciones, esa variante se elimina automáticamente al confirmar.

**35.** Si al quitar el atributo una variante pierde algunas implementaciones pero le quedan otras, solo se filtran las implementaciones del atributo quitado; la variante no se elimina.

**36.** Si tras quitar el atributo dos variantes del mismo producto quedan con la misma firma (misma combinación de valores), la variante duplicada se elimina. No pueden existir dos variantes con la misma firma en el mismo producto, ni al crearlas ni como consecuencia de una modificación.

---

## Bloque 12 — Mover categoría

**37.** Mover una categoría a un nuevo padre puede provocar que los productos de su subárbol ganen atributos nuevos (los del nuevo padre) y/o pierdan atributos (los del padre anterior). El flujo puede ser aditivo, destructivo o mixto.

**38.** Si el nuevo padre es el mismo que el padre actual (solo cambio de posición entre hermanos dentro del mismo padre), no hay impacto en atributos (flujo "none").

**39.** Si un atributo aparece tanto en el "padre saliente" como en el "padre entrante" (porque ambos lo heredan de un ancestro común), ese atributo se netea: no se cuenta como ganancia ni como pérdida real.

**40.** Al mover una categoría, los atributos dinámicos que se pierden se evalúan variante por variante: si la variante pierde **todas** sus implementaciones → la variante se elimina; si pierde solo algunas → se filtran solo las implementaciones perdidas.

---

## Bloque 13 — Mover producto

**41.** Al mover un producto a una nueva categoría se analizan dos capas:
   - Atributos **estáticos**: los que la nueva categoría requiere y el producto no tiene se solicitan al usuario; los que el producto tiene y la nueva categoría no requiere se eliminan.
   - Atributos **dinámicos**: los que la nueva categoría requiere y las variantes no tienen se solicitan al usuario; los que las variantes tienen y la nueva categoría no requiere se eliminan de las variantes.

**42.** Mover una variante no tiene impacto en atributos (flujo "none") porque las variantes no tienen atributos propios; los reciben de la categoría del producto padre.

---

## Bloque 14 — Eliminación en cascada

**43.** Eliminar un nodo elimina también toda su descendencia (todos los hijos, nietos, etc., en cascada).

**44.** El nodo raíz virtual (id = 0) no puede eliminarse.

**45.** Antes de eliminar un nodo con descendientes, el sistema muestra la lista completa de lo que se borrará para que el usuario confirme.

---

## Bloque 15 — Persistencia

**46.** El árbol de catálogo se guarda automáticamente en `localStorage("igm-catalog")` después de cada render (incluso si el usuario no hizo clic en "guardar").

**47.** El estado de collapse/expand de las cartas también se persiste aunque no dispare un re-render completo del árbol.

**48.** Los atributos globales se guardan en `localStorage("igm-attrs")` de forma separada al catálogo.

---

## Bloque 16 — Identificación de atributos

**49.** La `key` es el identificador único de un atributo (ej: `"color"`, `"talle"`). El `AttributeFactory` garantiza que no existan dos instancias de `Attribute` con la misma `key` en memoria.

**50.** La igualdad entre dos instancias de `Attribute` se resuelve por `id` cuando ambas tienen `id` asignado; por identidad de objeto (referencia) si alguna no tiene `id`.


