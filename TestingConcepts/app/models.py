#modelo de jerarquia de atributos
DataTypes = ["text", "number", "boolean", "enum"]

# text y number son simbre de producto
# boolean es siempre de variante
# enum puede ser de producto o de variante, si es de producto se muestra como info, si es de variante se muestra como una opcion para elegir.

class Attribute:
    def __init__(self, key:str, name:str, data_type:str,id:int=None, is_static:bool=False):
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

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "data_type": self.data_type,
            "is_static": self.is_static,
            "enum_values": [
                ev.to_json() if hasattr(ev, "to_json") else ev
                for ev in self.enum_values
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        obj = cls(
            key=data.get("key"),
            name=data.get("name"),
            data_type=data.get("data_type"),
            id=data.get("id"),
            is_static=data.get("is_static", False)
        )

        obj.enum_values = [
            EnumValue.from_json(ev) if isinstance(ev, dict) else ev
            for ev in data.get("enum_values", [])
        ]

        return obj

class Category:
    def __init__(self, name:str, id:int=None, attributes: list = None):
        self.id = id
        self.name = name
        self.attributes = attributes or [] # lista de objetos Attribute

    def add_attribute(self, attribute):
        if attribute not in self.attributes:
            self.attributes.append(attribute)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "attributes": [
                attr.to_json() if hasattr(attr, "to_json") else attr
                for attr in self.attributes
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        attributes = [
            Attribute.from_json(attr) if isinstance(attr, dict) else attr
            for attr in data.get("attributes", [])
        ]

        return cls(
            name=data.get("name"),
            id=data.get("id"),
            attributes=attributes
        )

class AttributeImplementation: # esta clase representa la implementacion de un atributo, lo va a contener toda variant que le competa
    def __init__(self, attribute:Attribute, value:str, id:int = None):
        self.id = id
        self.attribute = attribute # objeto Attribute referencia.
        self.value = value

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "attribute": self.attribute.to_json() if self.attribute else None,
            "value": self.value
        }

    @classmethod
    def from_json(cls, data: dict):
        attribute_data = data.get("attribute")

        attribute = (
            Attribute.from_json(attribute_data)
            if isinstance(attribute_data, dict)
            else attribute_data
        )

        return cls(
            attribute=attribute,
            value=data.get("value"),
            id=data.get("id")
        )

class Variant: # hereda todas las propiedades por asociacion con el producto, y implementa obligatoriamente los atributos del producto y de la categoria.
    def __init__(self, attribute_implementations, id=None,):
        self.id = id
        self.attribute_implementations = attribute_implementations # lista de objetos AttributeImplementation, implementamos atributos no staticos, es decir, los que no se muestran como informacion del producto, sino que son opciones para elegir.

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "attribute_implementations": [
                ai.to_json() if hasattr(ai, "to_json") else ai
                for ai in self.attribute_implementations
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        attribute_implementations = [
            AttributeImplementation.from_json(ai) if isinstance(ai, dict) else ai
            for ai in data.get("attribute_implementations", [])
        ]

        return cls(
            attribute_implementations=attribute_implementations,
            id=data.get("id")
        )

class Product:
    def __init__(self, code:str, title:str, price:float, description:str,brand:str, id:int = None, category: Category = None,attributes_implementations: list = None, attributes: list = None, variants: list = None):
        #agregar los otros ifs de los obligatorios
        if category is None:
            raise ValueError("Product must have a category") 
        
        self.id = id
        self.code = code
        self.title = title
        self.price = price
        self.description = description
        self.brand = brand
        self.category = category
        self.attributes_implementations = attributes_implementations or [] # implementaciones de atributos estaticos
        self.attributes = attributes or [] # lista de objetos Attribute
        self.variants = variants or [] # lista de objetos Variant

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "brand": self.brand,
            "category": self.category.to_json() if self.category else None,
            "attributes_implementations": [
                ai.to_json() if hasattr(ai, "to_json") else ai
                for ai in self.attributes_implementations
            ],
            "attributes": [
                attr.to_json() if hasattr(attr, "to_json") else attr
                for attr in self.attributes
            ],
            "variants": [
                v.to_json() if hasattr(v, "to_json") else v
                for v in self.variants
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        category_data = data.get("category")
        category = (
            Category.from_json(category_data)
            if isinstance(category_data, dict)
            else category_data
        )

        attributes_implementations = [
            AttributeImplementation.from_json(ai) if isinstance(ai, dict) else ai
            for ai in data.get("attributes_implementations", [])
        ]

        attributes = [
            Attribute.from_json(attr) if isinstance(attr, dict) else attr
            for attr in data.get("attributes", [])
        ]

        variants = [
            Variant.from_json(v) if isinstance(v, dict) else v
            for v in data.get("variants", [])
        ]

        return cls(
            code=data.get("code"),
            title=data.get("title"),
            price=data.get("price"),
            description=data.get("description"),
            brand=data.get("brand"),
            id=data.get("id"),
            category=category,
            attributes_implementations=attributes_implementations,
            attributes=attributes,
            variants=variants
        )

    def add_attribute(self, attribute:Attribute): 
        if attribute not in self.attributes and attribute not in self.category.attributes:
            self.attributes.append(attribute)

    def add_variant(self, variant:Variant):
        if variant not in self.variants:
            self.variants.append(variant)

    def add_attribute_implementation(self, attribute_implementation:AttributeImplementation):
        if attribute_implementation.attribute.is_static:
            # verificar si el atributo ya esta implementado
            for impl in self.attributes_implementations:
                if impl.attribute == attribute_implementation.attribute:
                    raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado para este producto.")
            #verificar que sea un atributo del producto o de la categoria
            if attribute_implementation.attribute in self.attributes or attribute_implementation.attribute in self.category.attributes:
                # verificar que el valor sea valido segun el tipo de dato
                if attribute_implementation.attribute.check_value(attribute_implementation.value):
                    self.attributes_implementations.append(attribute_implementation)
        else:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' no es estático y no puede ser implementado en el producto.")

    # da los atributos necesario que requeriria una variante o producto depende del parametro
    def get_needed_atributes_implementations(self, is_static:bool=False): 
        attributes = []
        for attr in self.attributes:
            if attr.is_static == is_static:
                attributes.append(attr)
        for attr in self.category.attributes:
            if attr.is_static == is_static:
                attributes.append(attr)
        return attributes

    def create_variant_by_implementations(self,implementations:list[AttributeImplementation]): # crea en base a implementaciones
        variant = Variant(attribute_implementations=[])
        # chequeamos que las implementaciones sean las necesarias
        if len(implementations) != len(self.get_needed_atributes_implementations()):
            return None
        try:
            for impl in implementations:
                self.add_variant_implementation(variant,impl)
        except ValueError as e:
            print(f"Error al crear la variante: {e}")
            return None
        self.add_variant(variant=variant)
        return variant

    def add_variant_implementation(self,variant:Variant,attribute_implementation:AttributeImplementation):
        # verificar que el atributo no sea estatico
        if attribute_implementation.attribute.is_static:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' es estático y no puede ser implementado en una variante.")
        # verificar que el atributo este definido en el producto o en la categoria
        if attribute_implementation.attribute not in self.attributes and attribute_implementation.attribute not in self.category.attributes:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' no está definido para el producto '{self.product.title}'.")
        # verificar que el valor sea valido segun el tipo de dato
        if not attribute_implementation.attribute.check_value(attribute_implementation.value):
            raise ValueError(f"El valor '{attribute_implementation.value}' no es válido para el atributo '{attribute_implementation.attribute.name}'.")
        #verificar que el atributo no este ya implementado en la variante
        for impl in variant.attribute_implementations:
            if impl.attribute == attribute_implementation.attribute:
                raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado en esta variante.")
        variant.attribute_implementations.append(attribute_implementation)

#como va a viajar la informacion?
# la informacion va a viajar como producto json y sus attr de producto y adentro variants json cada una con sus espesificaciones de attr.

# ---------------------- testing
def testing():
    #creo atributos y categorias
    atributo = Attribute(key="Talle",name="talle",data_type="enum")
    atributo.add_enum_value("41")
    atributo.add_enum_value("42")
    atributo.add_enum_value("43")
    categoria = Category(name="Zapatillas")
    categoria.add_attribute(attribute=atributo)

    #creo atributo estatico
    atributoStatic = Attribute(key="peso_g",name="peso (g)",data_type="number",is_static=True)

    #creo producto y le agrego su static, ademas va a heredar el dinamic(variant atribute) del category.
    producto = Product(code="asd22f3f",title="shordan",price=1200,description="amazin",brand="nike",category=categoria)
    producto.add_attribute(attribute=atributoStatic)

    #implementamos el static
    product_implementation = AttributeImplementation(attribute=atributoStatic,value="350")
    producto.add_attribute_implementation(attribute_implementation=product_implementation)
    #aca deberiamos poner el mismo add dinamico que tengo en variant

    #creamos variant
    necesidades_variante = producto.get_needed_atributes_implementations(is_static=False)
    implementaciones = []
    for attr_necesario in necesidades_variante:
        print(attr_necesario.name)
        valor = input(">:")
        implementaciones.append(AttributeImplementation(attribute=attr_necesario,value=valor))

    for i in implementaciones:
        print(f"{i.attribute.name} -> {i.value}")

    producto.create_variant_by_implementations(implementations=implementaciones)

    import json

    print(json.dumps(producto.to_json(), indent=4, ensure_ascii=False))

#testing()