from typing import List
#modelo de jerarquia de atributos
DataTypes = ["text", "number", "boolean", "enum"]
# Buenas parcticas locales
# text y number son simbre de producto
# boolean es siempre de variante
# enum puede ser de producto o de variante, si es de producto se muestra como info, si es de variante se muestra como una opcion para elegir.

class Attribute:
    def __init__(self, 
        key:str, 
        name:str, 
        data_type:str,
        id:int=None, 
        is_static:bool=False
        ):
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

    def __eq__(self, other):
        if not isinstance(other, Attribute):
            return NotImplemented
        return self.id == other.id if self.id is not None else self is other

    def __hash__(self):
        return hash(self.id) if self.id is not None else id(self)

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
        attr = cls(
            key=data.get("key"),
            name=data.get("name"),
            data_type=data.get("data_type"),
            id=data.get("id"),
            is_static=data.get("is_static", False)
        )
        for ev in data.get("enum_values", []):
            attr.enum_values.append(ev)
        return attr

class Attribute_factory:
    _instances: dict = {}

    @classmethod
    def get(cls, key: str, name: str, data_type: str, id: int = None, is_static: bool = False) -> "Attribute":
        if key not in cls._instances:
            cls._instances[key] = Attribute(key=key, name=name, data_type=data_type, id=id, is_static=is_static)
        return cls._instances[key]

    @classmethod
    def clear(cls):
        cls._instances.clear()

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

class Category:
    def __init__(self, 
        name:str, 
        id:int=None, 
        attributes: list[Attribute] = None, 
        subcategories: list[Category] = None, 
        father_categorie: Category = None,
        products: list[Product] = None
        ):
        self.id = id
        self.name = name
        self.attributes = attributes or [] # lista de objetos Attribute
        self._attribute_keys = {a.key for a in self.attributes}
        self.subcategories = subcategories or [] # lista de subcategorias
        self.father_categorie = father_categorie or None # categoria padre
        self.products = products or [] # lista de productos que estan con esta categoria
        self._product_codes = {p.code for p in self.products}

    

class Variant: # hereda todas las propiedades por asociacion con el producto, y implementa obligatoriamente los atributos del producto y de la categoria.
    def __init__(self, attribute_implementations:List[AttributeImplementation]=None, id:int=None,):
        self.id = id
        self.attribute_implementations = attribute_implementations or [] # lista de objetos AttributeImplementation, implementamos atributos no staticos, es decir, los que no se muestran como informacion del producto, sino que son opciones para elegir.

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
    def __init__(self, 
    code:str, 
    title:str, 
    price:float, 
    description:str,
    brand:str, 
    id:int = None, 
    category: Category = None,
    attributes_implementations: List[AttributeImplementation] = None, 
    variants: List[Variant] = None
    ):
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
        self._impl_keys = {i.attribute.key for i in self.attributes_implementations}
        self._attribute_keys = {a.key for a in self.attributes}
        self.variants = variants or [] # lista de objetos Variant
    