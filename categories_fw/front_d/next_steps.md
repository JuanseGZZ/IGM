- refactorizar:

* pasar de la ui a el html esos modales que se estan generando al pedo dinamicamente.
* plantear para que es cada cosa:
. el events es son triggers que sirven para llamar a otras cosas, no deberia haber muchas funciones ahi.

* pasar la logica de zoom de events a ui.


- hacer la lista de todos los casos de usos y reglas de negocio que se implementaron, y ver cuales faltan. Puede ayudar la logica de codigo, las reglas y los bugs arreglados.

- ver si se esta usando algo de la logica de negocio que esta en los models.js

- si la esta usando ver de migrarla a gestor asi queda en un solo lado.