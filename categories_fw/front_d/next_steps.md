- refactorizar:


* plantear para que es cada cosa:
. el events es son triggers que sirven para llamar a otras cosas, no deberia haber muchas funciones ahi.


- hacer la lista de todos los casos de usos y reglas de negocio que se implementaron, y ver cuales faltan. Puede ayudar la logica de codigo, las reglas y los bugs arreglados.

- ver si se esta usando algo de la logica de negocio que esta en los models.js

- si la esta usando ver de migrarla a gestor asi queda en un solo lado.

- para ver el modo de importaciones pedir que haga una lista de los archivos diciendo que importa que. corregir estructura.




AGREGACIONES: 
- editar attributos.
- que se pueda editar en producto las implementaciones de attributos de producto
- que se vean las implementaciones de los productos.


imples:

hacer que me grafique las cosas en el models de py y que me de botones para indicar acciones en nodo con ui para python. si anda todo bien el worflow va a ser me llega un arbol y lo armo de arriba hacia abajo si sale todo bien se queda, sino se retorna error