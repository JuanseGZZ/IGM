- Caundo el abuelo tiene dos hijos y uno de los hijos tiene un attributo, y el otro no, y el abuelo tambien agrega ese attributo que tiene el primer hijo, no deberia ser tomado como impacto el nieto del primer hijo, y sin embargo el sistema lo esta tomando como impacto. ARREGLADO

- no se deberia poder crear una variante de un producto si nadie en la familia de ese producto tiene ningun attributo variante. ARREGLADO

- cuando el abuelo tiene un atributo y el hijo no pero el producto del hijo tiene una variante implementada con ese attributo, si al abuelo se lo saco no me sale la alerta de impacto detectado, cuando claramente esa variante esta siendo impactada. ARREGLADO


- no se deberia poder crear dos variantes iguales. ARREGLADO

- si quitan un attributo y queda la variante sin implementaciones, se deberia eliminar esa variante directamente ARREGLADO

- cuando corro categorias me deja correrla como hermana de la hija del root y no deberia. ARREGLADO

- cuando tengo una categoria abajo de la otra y abajo un producto con una variante, y corro la categoria con el hijo a otro lado, si bien me sale el cartel que se va a eliminar el atributo que estoy dejando attras en la del abuelo, no elimina esa implementacion en las variantes. ARREGLADO.


- si yo tengo una categoria con un attributo de variante, y arriba de esa categoria tengo el mismo attributo de bariante y abajo tengo un producto con una variante que implementa ese attributo de variante, y yo elimino ese attributo de variante de la categoria, eso elimina la implementacion, pero no deberia porque ese attributo sigue siendo heredado por la categoria abuelo, entonces no deberia decirme de impacto, porque no lo estaria habiendo. ARREGLADO