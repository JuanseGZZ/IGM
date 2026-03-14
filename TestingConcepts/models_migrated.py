#modelo de jerarquia de atributos

DataTypes = ["text", "number", "boolean", "enum"]

# text y number son simbre de producto
# boolean es siempre de variante
# enum puede ser de producto o de variante, si es de producto se muestra como info, si es de variante se muestra como una opcion para elegir.

class Attribute:
    def __init__(self,id, key, name, data_type, is_static=False):
        self.id = id
        self.key = key
        self.name = name
        self.data_type = data_type
        self.is_static = is_static # el atributo estatico es aquel que se muestra como informacion del producto.
        self.enum_values = [] # si el tipo de dato es enum, esta lista va a contener los valores posibles, va a ser una lista de objetos EnumValue

    def add_enum_value(self, value): # esto es una class pero en el repositorio va a mantener los estados y actualizar las lineas.
        if self.data_type != "enum":
            raise ValueError("El atributo no es de tipo enum.")
        if value not in self.enum_values:
            self.enum_values.append(value)
        else:
            raise ValueError("El valor ya existe en la lista de valores posibles.")

    def check_value(self, value):
        if self.data_type == "text":
            return isinstance(value, str)
        elif self.data_type == "number":
            return isinstance(value, (int, float))
        elif self.data_type == "boolean":
            return isinstance(value, bool)
        elif self.data_type == "enum":
            return value in self.enum_values
        else:
            raise ValueError("Tipo de dato no reconocido.")

class Category:
    def __init__(self, id, name, attributes):
        self.id = id
        self.name = name
        self.attributes = attributes # lista de objetos Attribute

    def add_attribute(self, attribute):
        if attribute not in self.attributes:
            self.attributes.append(attribute)

class Product:
    def __init__(self, id, title, price, description,brand, category_id, attributes =[], variants=[]):
        self.id = id
        self.title = title
        self.price = price
        self.description = description
        self.brand = brand
        self.category_id = category_id
        self.attributes_implementations = [] # implementamos atributos estaticos
        self.attributes = attributes # lista de objetos Attribute
        self.variants = variants # lista de objetos Variant

    def add_attribute(self, attribute): 
        if attribute not in self.attributes and attribute not in self.category_id.attributes:
            self.attributes.append(attribute)

    def add_variant(self, variant):
        if variant not in self.variants:
            self.variants.append(variant)

    def add_attribute_implementation(self, attribute_implementation):
        if attribute_implementation.attribute.is_static:
            # verificar si el atributo ya esta implementado
            for impl in self.attributes_implementations:
                if impl.attribute == attribute_implementation.attribute:
                    raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado para este producto.")
            #verificar que sea un atributo del producto o de la categoria
            if attribute_implementation.attribute in self.attributes or attribute_implementation.attribute in self.category_id.attributes:
                # verificar que el valor sea valido segun el tipo de dato
                if attribute_implementation.attribute.check_value(attribute_implementation.value):
                    self.attributes_implementations.append(attribute_implementation)

class AttributeImplementation: # esta clase representa la implementacion de un atributo, lo va a contener toda variant que le competa
    def __init__(self, id, attribute, value):
        self.id = id
        self.attribute = attribute # objeto Attribute referencia.
        self.value = value

class Variant: # hereda todas las propiedades por asociacion con el producto, y implementa obligatoriamente los atributos del producto y de la categoria.
    def __init__(self, product, attribute_implementations, id=None,):
        self.id = id
        self.product = product
        self.attribute_implementations = attribute_implementations # lista de objetos AttributeImplementation, implementamos atributos no staticos, es decir, los que no se muestran como informacion del producto, sino que son opciones para elegir.

    def add_attribute_implementation(self, attribute_implementation):
        # verificar que el atributo no sea estatico
        if attribute_implementation.attribute.is_static:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' es estático y no puede ser implementado en una variante.")
        # verificar que el atributo este definido en el producto o en la categoria
        if attribute_implementation.attribute not in self.product.attributes and attribute_implementation.attribute not in self.product.category_id.attributes:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' no está definido para el producto '{self.product.title}'.")
        # verificar que el valor sea valido segun el tipo de dato
        if not attribute_implementation.attribute.check_value(attribute_implementation.value):
            raise ValueError(f"El valor '{attribute_implementation.value}' no es válido para el atributo '{attribute_implementation.attribute.name}'.")
        #verificar que el atributo no este ya implementado en la variante
        for impl in self.attribute_implementations:
            if impl.attribute == attribute_implementation.attribute:
                raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado en esta variante.")
        self.attribute_implementations.append(attribute_implementation)

def createVariant(product, implementations):
    variant = Variant(product=product, attribute_implementations=[])
    try:
        for impl in implementations:
            variant.add_attribute_implementation(impl)
    except ValueError as e:
        print(f"Error al crear la variante: {e}")
        return None
    return variant


#como va a viajar la informacion?
# la informacion va a viajar como producto json y sus attr de producto y adentro variants json cada una con sus espesificaciones de attr.


# ---------------------- thinking

# iteradores para id
i_var = 0
i_cat = 0
i_prod = 0
i_attr = 0 
i_imp = 0

i_attr+=1
atribute = Attribute(i_attr, "color", "Color", "enum",is_static=False) # atributo de variable.
atribute.add_enum_value("red")
atribute.add_enum_value("blue")

i_attr+=1
#atributos de producto
atribute2 = Attribute(i_attr, "large_cm", "Large (cm)", "number", is_static=True)
atribute3 = Attribute(i_attr, "ancho_cm", "Ancho (cm)", "number", is_static=True)
atribute4 = Attribute(i_attr, "altura_cm", "Altura (cm)", "number", is_static=True)

i_cat+=1
category = Category(i_cat, "Shirts", [atribute])
i_prod+=1
product = Product(i_prod, "T-Shirt", 19.99, "A comfortable t-shirt", "BrandX", category, [])
i_var+=1
variant1 = Variant(i_var, product, [AttributeImplementation(i_imp, atribute, "red")])
i_var+=1
variant2 = Variant(i_var, product, [AttributeImplementation(i_imp, atribute, "blue")])

i_cat+=1
category2 = Category(i_cat, "Muebles", [atribute2, atribute3]) # le agregamos ancho, alto y largo, como heredables.
i_prod+=1
#creamos producto y le implementamos los atributos heredados estaticos, por eso los implementamos en producto.
product2 = Product(i_prod, "Desk", 199.99, "A sturdy desk", "BrandY", category2, [atribute4,atribute])
product2.add_attribute_implementation(AttributeImplementation(i_imp, atribute4, 75))
product2.add_attribute_implementation(AttributeImplementation(i_imp, atribute3, 60))
product2.add_attribute_implementation(AttributeImplementation(i_imp, atribute2, 150))

# i_imp+=1
i_imp+=1 
variant3 = createVariant(product2, [AttributeImplementation(i_imp, atribute, "red")])
