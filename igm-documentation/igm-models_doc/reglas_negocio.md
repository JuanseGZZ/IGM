# Reglas de Negocio del Modelo

Este documento define el comportamiento esperado del sistema de catalogo para `Attribute`, `AttributeImplementation`, `Category`, `Product` y `Variant`.

La idea no es describir solamente lo que hoy hace `models.py`, sino dejar claro lo que el sistema deberia contemplar cuando ocurren cambios, impactos o migraciones dentro del arbol de categorias y productos.

## 1. Principios generales

- Una categoria puede tener subcategorias o productos directos, pero no ambas cosas al mismo tiempo.
- Toda categoria puede tener padre o ser raiz, pero el arbol no puede tener ciclos.
- Todo producto debe pertenecer siempre a una categoria valida.
- Toda variante pertenece a un unico producto.
- Un atributo representa una definicion; una implementacion representa un valor concreto de esa definicion.
- La `key` de un atributo es unica a nivel logico. Dos atributos con la misma `key` deben representar el mismo concepto.
- Un atributo estatico se implementa a nivel producto.
- Un atributo dinamico se implementa a nivel variante.
- Ninguna operacion con impacto debe dejar cambios parciales: primero se valida todo, despues se aplica todo.
- Si una operacion falla, el sistema debe conservar el estado anterior intacto.
- Ningun producto o variante debe quedar con implementaciones huerfanas de atributos que ya no estan suscriptos por producto, categoria o ancestros.
- Ningun producto debe tener dos implementaciones estaticas para la misma `key`.
- Ninguna variante debe tener dos implementaciones dinamicas para la misma `key`.
- Las listas cacheadas (`_attribute_keys`, `_impl_keys`, `_product_codes`) deben quedar sincronizadas con las colecciones reales.
- Si una operacion necesita datos adicionales para no romper consistencia, el sistema primero debe reportar impacto y pedir esos datos antes de escribir.

## 2. Reglas estructurales del dominio

### 2.1 Atributos

- `text` y `number` deberian usarse como atributos estaticos de producto.
- `boolean` deberia usarse como atributo dinamico de variante.
- `enum` puede ser estatico o dinamico.
- Si se necesita romper esta convencion, el sistema deberia exigir una justificacion explicita o una migracion controlada.

### 2.2 Cobertura de atributos

- Un atributo puede quedar cubierto por:
  - la categoria actual,
  - un ancestro de la categoria,
  - el producto en forma propia.
- Si un atributo esta cubierto por arriba, no hace falta duplicarlo abajo.
- Si un atributo deja de estar cubierto por arriba, el sistema debe decidir una de estas estrategias:
  - pedir implementaciones nuevas,
  - inyectar el atributo como propio en productos afectados,
  - borrar implementaciones que queden sin sustento,
  - cancelar la operacion.

### 2.3 Impacto y cobertura exacta

- Cuando se agrega un atributo con impacto, la cobertura enviada debe ser exacta:
  - todos los productos afectados deben estar representados,
  - ninguna fila extra debe aparecer,
  - no puede haber `product_id` duplicados,
  - no puede haber `variant_id` duplicados dentro del mismo producto,
  - los valores enviados deben respetar `data_type` y, si aplica, `enum_values`.
- El sistema no deberia aceptar coberturas parciales.

## 3. Ciclo de vida de un atributo

### 3.1 Crear atributo

- Validar que `key`, `name` y `data_type` existan.
- Validar que `data_type` pertenezca al conjunto soportado.
- Validar que la `key` no colisione con otra definicion incompatible.
- Si el atributo es `enum`, inicializar la lista de valores posibles.
- Si existe factory/cache global, devolver la misma instancia logica para la misma `key`.

### 3.2 Editar atributo

- Cambiar `name` no deberia tener impacto estructural.
- Cambiar `key` deberia tratarse como migracion, no como simple edicion.
- Cambiar `data_type` deberia bloquearse si ya hay implementaciones existentes, salvo que exista una migracion explicita.
- Cambiar `is_static` deberia bloquearse si ya existen productos o variantes que usan ese atributo, salvo migracion total.
- Si se aprueba una migracion, el sistema debe recalcular donde vive cada implementacion.

### 3.3 Agregar valor enum

- Solo deberia permitirse si `data_type == "enum"`.
- El valor no debe estar repetido.
- Agregar un nuevo valor no deberia afectar implementaciones existentes.

### 3.4 Quitar valor enum

- Solo deberia permitirse si `data_type == "enum"`.
- Antes de borrar el valor, el sistema debe buscar si esta siendo usado por algun producto o variante.
- Si esta en uso, el sistema deberia:
  - rechazar la operacion, o
  - exigir remapeo de todos los usos antes de borrar.

### 3.5 Eliminar atributo del sistema

- Antes de eliminarlo, el sistema debe buscar referencias en:
  - categorias,
  - productos,
  - implementaciones estaticas,
  - implementaciones dinamicas.
- Si todavia hay referencias, la operacion deberia bloquearse o ejecutarse como migracion guiada.

## 4. Operaciones sobre categorias

### 4.1 Crear categoria raiz

- Debe nacer sin padre.
- Puede nacer con atributos.
- No deberia nacer a la vez con subcategorias y productos si no existe una carga inicial consistente.
- Si nace con subcategorias, cada subcategoria debe apuntar correctamente a ella.

### 4.2 Crear subcategoria

- El padre destino no puede tener productos directos.
- La nueva relacion no puede introducir ciclos.
- La subcategoria debe agregarse al padre y el padre debe quedar asignado en la hija.
- Si la subcategoria ya tenia otro padre, esto ya no es alta simple: es movimiento de categoria.

### 4.3 Mover una categoria de un padre a otro padre

- El sistema debe considerar esto como una operacion de reestructuracion completa.
- Procedimiento esperado:
  1. Validar que el nuevo padre exista.
  2. Validar que el nuevo padre no tenga productos directos.
  3. Validar que el nuevo padre no sea la propia categoria ni un descendiente suyo.
  4. Identificar el linaje actual: padre actual, abuelo, bisabuelo, etc.
  5. Identificar el nuevo linaje: nuevo padre, nuevo abuelo, etc.
  6. Calcular atributos que la categoria y su rama perderian al salir del linaje actual.
  7. Calcular atributos que la categoria y su rama ganarian al entrar al nuevo linaje.
  8. Para cada atributo perdido, verificar si ya esta cubierto localmente por:
     - la categoria movida,
     - alguna subcategoria,
     - el producto en forma propia.
  9. Si un atributo perdido deja productos sin cobertura, armar reporte de impacto.
  10. Para cada atributo nuevo, detectar que productos/variantes necesitan implementacion nueva.
  11. Separar siempre el impacto en:
     - atributos estaticos que requieren valor por producto,
     - atributos dinamicos que requieren valor por variante.
  12. Validar que la informacion complementaria cubra exactamente todos los afectados.
  13. Validar tipos y enums de todos los valores enviados.
  14. Recién cuando todo sea valido:
     - remover la categoria del padre anterior,
     - asignar el nuevo padre,
     - agregarla a `subcategories` del nuevo padre,
     - aplicar las nuevas implementaciones,
     - resolver los atributos perdidos segun la politica elegida,
     - reconstruir caches si hace falta.
- Politicas posibles para atributos perdidos:
  - inyectar el atributo como propio en productos afectados,
  - borrar implementaciones que queden huerfanas,
  - cancelar el movimiento.
- Si falta un dato, sobra una fila o falla una validacion, no debe aplicarse ningun cambio parcial.

### 4.4 Desprender una categoria de su padre y volverla raiz

- Debe tratarse como un movimiento hacia un linaje vacio.
- El sistema debe recalcular todos los atributos que dejara de heredar.
- Si hay atributos perdidos con impacto, debe ofrecer las mismas politicas que en el movimiento entre padres.

### 4.5 Agregar atributo estatico a una categoria

- El atributo debe ser estatico.
- Antes de agregarlo, el sistema debe ver si algun ancestro ya lo cubre.
- Si ya esta cubierto por arriba, agregarlo abajo es redundante y deberia:
  - rechazarse, o
  - permitirse solo si se quiere convertir en atributo propio por una razon explicita.
- Si no esta cubierto por arriba:
  - buscar todos los productos descendientes que quedarian obligados a tener implementacion estatica,
  - excluir los productos que ya lo tengan como atributo propio o ya tengan cobertura valida.
- Si hay productos afectados:
  - pedir un valor por producto,
  - validar cobertura exacta,
  - validar tipos,
  - aplicar implementaciones y luego registrar el atributo en la categoria.
- Si no hay afectados, se registra el atributo y termina.

### 4.6 Agregar atributo dinamico a una categoria

- El atributo debe ser dinamico.
- Antes de agregarlo, el sistema debe ver si algun ancestro ya lo cubre.
- Si ya esta cubierto por arriba, agregarlo abajo es redundante y deberia tratarse igual que el caso estatico.
- Si no esta cubierto por arriba:
  - buscar todos los productos descendientes afectados,
  - para cada producto afectado, pedir un valor por cada variante existente.
- Reglas de validacion:
  - cada producto afectado debe aparecer una sola vez,
  - cada variante afectada debe aparecer una sola vez,
  - no puede faltar ninguna variante,
  - no pueden aparecer variantes ajenas al producto,
  - todos los valores deben pasar `check_value`.
- Si todo es valido, el sistema agrega las implementaciones en variantes y registra el atributo en la categoria.

### 4.7 Eliminar un atributo de una categoria

- El sistema primero debe verificar si el atributo sigue cubierto por algun ancestro.
- Si un ancestro lo cubre, se puede borrar de la categoria sin impacto sobre descendientes.
- Si no hay cobertura superior, el sistema debe buscar productos perjudicados en toda la rama.
- El analisis debe separar:
  - productos que ya tienen el atributo propio,
  - productos que solo dependian de la categoria,
  - variantes con implementaciones dinamicas de ese atributo,
  - productos con implementaciones estaticas de ese atributo.
- El sistema deberia ofrecer modos de resolucion:
  - modo reporte: listar afectados sin tocar nada,
  - modo borrar: borrar implementaciones huerfanas y luego borrar el atributo de categoria,
  - modo preservar: inyectar el atributo como propio en cada producto afectado y luego borrar el de categoria,
  - modo cancelar.
- Si el atributo es dinamico y se elige borrar, las implementaciones deben borrarse de variantes, no de producto.
- Si el atributo es estatico y se elige borrar, las implementaciones deben borrarse de producto.

### 4.8 Eliminar una subcategoria hija

- Solo deberia poder eliminarse si realmente es hija directa.
- El sistema debe calcular que atributos de esa subcategoria y su linaje interno dejarian de estar cubiertos al sacarla de `self`.
- Luego debe medir impacto en todos los productos de la rama eliminada.
- Opciones esperadas:
  - solo informar impacto,
  - borrar implementaciones huerfanas y luego eliminar la subcategoria,
  - inyectar atributos faltantes en productos afectados y luego eliminar la subcategoria,
  - reubicar la subcategoria antes de eliminarla.
- Si la subcategoria tiene hijos, el impacto debe incluir toda su rama.
- Si se elimina definitivamente, la relacion bidireccional debe quedar limpia:
  - la hija sale de `subcategories` del padre,
  - `father_categorie` de la hija pasa a `None`.

### 4.9 Agregar producto a una categoria

- La categoria destino no puede tener subcategorias.
- El producto no debe estar repetido por `code`.
- El producto debe quedar con `category` apuntando a esa categoria.
- Al entrar el producto, el sistema deberia verificar si cumple con todos los atributos requeridos por la categoria y ancestros.
- Si no cumple, deberia:
  - quedar en estado incompleto/borrador, o
  - exigirse completar datos antes de confirmar el alta.

### 4.10 Quitar producto de una categoria

- Solo deberia quitarse si realmente pertenece a esa categoria.
- Debe salir de `products` y del cache de codigos.
- Si el producto sigue existiendo en el sistema, deberia moverse a otra categoria o quedar sin categoria solo si el dominio lo permite.
- Si el dominio exige categoria obligatoria siempre, quitarlo de la categoria deberia formar parte de un movimiento o una baja.

### 4.11 Mover un producto de una categoria a otra

- Debe analizarse como mini migracion.
- Procedimiento esperado:
  1. validar que la nueva categoria exista y sea hoja,
  2. calcular atributos que el producto pierde al salir,
  3. calcular atributos que gana al entrar,
  4. verificar que las implementaciones actuales sigan siendo validas,
  5. pedir nuevos valores para atributos ganados,
  6. decidir que hacer con atributos perdidos,
  7. aplicar todo en forma atomica,
  8. actualizar ambas categorias.
- Si la nueva categoria exige atributos dinamicos, la validacion debe cubrir todas las variantes.

### 4.12 Eliminar una categoria del sistema

- Si tiene padre, deberia resolverse via la operacion de eliminar subcategoria.
- Si es raiz y tiene subcategorias o productos, el sistema deberia exigir una politica explicita:
  - cancelar,
  - reubicar hijos,
  - borrar en cascada,
  - migrar productos.
- No deberia existir una baja silenciosa de una categoria con rama viva.

## 5. Operaciones sobre productos

### 5.1 Crear producto

- `category` es obligatoria.
- `code` deberia ser unico en todo el sistema.
- El producto deberia inicializar sus colecciones internas vacias y consistentes.
- Al crearse, el sistema debe calcular:
  - atributos estaticos requeridos,
  - atributos dinamicos requeridos,
  - si puede existir sin variantes o necesita variantes desde el inicio.
- Si faltan implementaciones o variantes requeridas, el sistema deberia marcarlo como incompleto o rechazar la alta.

### 5.2 Editar datos base del producto

- `title`, `price`, `description`, `brand` deberian poder editarse sin afectar atributos.
- Si cambia `code`, el sistema debe verificar unicidad global y actualizar referencias derivadas.
- Ninguna edicion base deberia romper la categoria asociada.

### 5.3 Suscribir un atributo estatico propio a un producto

- Este caso deberia existir aunque hoy no este completamente explicitado.
- Procedimiento esperado:
  - validar que el atributo sea estatico,
  - validar que no este ya cubierto por el producto o la categoria,
  - registrar el atributo como propio del producto,
  - exigir inmediatamente una implementacion estatica valida.

### 5.4 Agregar implementacion estatica a un producto

- El atributo de la implementacion debe ser estatico.
- El valor debe pasar `check_value`.
- El atributo debe estar suscripto por:
  - la categoria,
  - un ancestro,
  - o el propio producto.
- No se debe permitir una segunda implementacion para la misma `key`.
- Si todo es valido, la implementacion se agrega y el cache se actualiza.

### 5.5 Suscribir un atributo dinamico propio a un producto

- El atributo debe ser dinamico.
- Si el producto ya lo hereda de la categoria, suscribirlo como propio solo deberia permitirse si se busca independencia futura.
- Si el producto ya tiene variantes:
  - debe pedirse un valor por variante,
  - debe validarse cobertura exacta,
  - luego se agregan implementaciones y se registra el atributo.
- Si todavia no tiene variantes:
  - puede suscribirse el atributo y exigir que toda variante futura lo implemente.

### 5.6 Eliminar un atributo propio de un producto

- Solo deberia poder eliminarse si el atributo es realmente propio del producto.
- Si la categoria o algun ancestro ya lo cubren, se puede quitar de `self` sin impacto.
- Si no lo cubre nadie mas, el sistema debe analizar impacto.
- Opciones esperadas:
  - informar implementaciones afectadas,
  - borrar implementaciones y quitar el atributo,
  - cancelar.
- Si es estatico, la implementacion a borrar vive en `attributes_implementations`.
- Si es dinamico, las implementaciones a borrar viven en cada variante.

### 5.7 Mover producto a otra categoria

- Debe seguir las reglas de la seccion 4.11.
- El producto no deberia quedar asociado a dos categorias a la vez.
- Las variantes deben revalidarse contra los atributos dinamicos de la nueva categoria.

### 5.8 Eliminar producto

- Debe salir de la categoria.
- Deben borrarse o desvincularse sus variantes.
- Deben borrarse sus implementaciones estaticas.
- Si existe persistencia, el borrado deberia ser transaccional.

## 6. Operaciones sobre variantes

### 6.1 Crear variante

- La variante debe cubrir exactamente todos los atributos dinamicos requeridos por el producto.
- No debe traer atributos de mas ni de menos.
- No debe repetir la misma `key` dos veces.
- Todos los valores deben ser validos para su atributo.
- Seria deseable que el sistema impida variantes duplicadas con la misma combinacion de valores si el negocio no las permite.
- Si todo es valido, se agrega al producto.

### 6.2 Editar variante

- Solo deberian editarse implementaciones dinamicas.
- No se debe permitir cambiar un valor a uno invalido.
- La variante no deberia quedar con atributos faltantes.
- Si se cambia la combinacion de valores, el sistema deberia verificar que no choque con otra variante existente.

### 6.3 Eliminar variante

- Debe eliminarse por `id` o por referencia inequívoca.
- Si el producto necesita al menos una variante para ser operable, el sistema deberia impedir dejarlo sin ninguna o marcarlo incompleto.
- Al borrarla, deben borrarse sus implementaciones dinamicas asociadas.

## 7. Casos complejos que el sistema debe contemplar

### 7.1 Un ancestro agrega un atributo nuevo

- Toda la rama descendiente debe analizarse.
- Los productos ya cubiertos localmente no requieren accion.
- Los productos no cubiertos deben recibir implementaciones nuevas o reportarse como impacto.
- Si el atributo es dinamico, la exigencia es por variante.
- Si el atributo es estatico, la exigencia es por producto.

### 7.2 Un ancestro elimina un atributo

- Toda la rama descendiente debe analizarse.
- Si algun descendiente ya tiene el atributo propio, queda cubierto y no hay impacto para ese caso.
- Si no queda cubierto, el sistema debe pedir resolucion explicita.

### 7.3 Una categoria intermedia se mueve

- Deben analizarse simultaneamente:
  - atributos que se pierden del linaje viejo,
  - atributos que se ganan del linaje nuevo,
  - productos y variantes afectados en toda la rama.
- La operacion no deberia dividirse en pasos manuales independientes porque eso puede dejar estados intermedios inconsistentes.

### 7.4 Se cambia la definicion de un atributo ya usado

- Debe tratarse como migracion.
- El sistema debe relevar:
  - donde se usa,
  - donde se implementa,
  - si el cambio afecta producto o variante,
  - si los valores actuales siguen siendo validos.
- Si no hay plan de migracion, el cambio debe bloquearse.

### 7.5 Se reconstruye un objeto desde JSON

- Deben reconstruirse las relaciones necesarias sin crear ciclos infinitos.
- Deben regenerarse caches derivados.
- No deberian perderse implementaciones ni referencias de padre/hijo relevantes.

## 8. Politicas de validacion y errores

- Los errores deberian ser explicitos y predecibles.
- Las validaciones de negocio deberian devolver impacto entendible cuando falta informacion.
- Las validaciones de integridad dura deberian lanzar error:
  - tipo de dato invalido,
  - intento de usar atributo dinamico como estatico o viceversa,
  - ciclos en categorias,
  - duplicados estructurales,
  - categoria con productos y subcategorias a la vez.
- Los errores de cobertura deberian indicar exactamente:
  - que producto falta,
  - que variante falta,
  - que valor es invalido,
  - que atributo genero el conflicto.

## 9. Reglas de atomicidad

- Ninguna operacion de alto impacto deberia aplicar cambios parciales.
- El orden correcto siempre deberia ser:
  1. analizar impacto,
  2. pedir datos faltantes,
  3. validar cobertura exacta,
  4. validar tipos y duplicados,
  5. aplicar cambios,
  6. actualizar caches,
  7. verificar consistencia final.

## 10. Checklist de consistencia final

Despues de cualquier operacion importante, el sistema deberia garantizar:

- la categoria correcta figura como padre,
- el padre correcto contiene a la hija,
- no hay categorias duplicadas en `subcategories`,
- no hay productos duplicados en `products`,
- no hay atributos duplicados en listas propias,
- no hay implementaciones duplicadas por `key`,
- no hay implementaciones dinamicas colgando en producto,
- no hay implementaciones estaticas colgando en variante,
- cada variante implementa exactamente los atributos dinamicos requeridos,
- cada producto implementa exactamente los atributos estaticos requeridos,
- los caches reflejan el estado real.

## 11. Casos deseables aunque hoy no esten del todo implementados

- estado borrador/publicado para productos incompletos,
- movimiento de producto entre categorias como operacion de primer nivel,
- desprender categoria y convertirla en raiz,
- migracion guiada de atributos ya usados,
- remapeo de valores enum antes de borrar una opcion,
- deteccion de variantes duplicadas,
- reportes de impacto con estructura uniforme para UI y API,
- reconstruccion segura de caches al deserializar,
- auditoria de cambios sobre categorias, atributos, productos y variantes.
