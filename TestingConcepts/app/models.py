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
        attributes: list = None, 
        subcategories: list = [], 
        father_categorie: Category = None,
        products: list = []
        ):
        self.id = id
        self.name = name
        self.attributes = attributes or [] # lista de objetos Attribute
        self._attribute_keys = {a.key for a in self.attributes}
        self.subcategories = subcategories or [] # lista de subcategorias
        self.father_categorie = father_categorie or None # categoria padre
        self.products = products = products or [] # lista de productos que estan con esta categoria

    def get_attributes(self) -> list: # get recursivo, va a traer toda la rama genialogica y devolver atributos.
        attributes = self.attributes.copy()
        if (self.father_categorie):
            attributes += self.father_categorie.get_attributes()
        return attributes

    # busca recursivamente para arriba si esta un attibut espesifico
    def add_attribute_look_up(self,attribute:Attribute):
        #si lo tengo retorno true
        if attribute.key in self._attribute_keys:
            return True
        #si no tengo padre y no lo tengo retorno false
        if self.father_categorie == None:
            return False
        #si no lo tengo pero tengo padre se lo piedo a mi padre y retorno lo que me diga
        return self.father_categorie.add_attribute_look_up(attribute=attribute)

    def add_attribute_look_down(self, attribute:Attribute):
        #miro que soy, si una categoria padre de categorias o de productos
        # lo hago recursivo en padre de categoria, y lo hago retornate en padre de productos
        # chequeo que tenga el attributo y corto busqueda
        if attribute.key in self._attribute_keys:
            return []
        # si no tengo el attributo busco hijos
        products = []
        if len(self.subcategories) > 0:
            for c in self.subcategories: #recorremos todas las categorias hijo llamando recursivamente a sus busquedas
                products.extend(c.add_attribute_look_down(attribute=attribute))
            return products
        if len(self.products) > 0:
            return list(self.products)
        # si no hay nada retornamos nada
        return []
            
    def add_attribute_check_family_impact(self,
        attribute:Attribute,
        ):
        #miramos si aca o arriba esta el attributo
        if self.add_attribute_look_up(attribute=attribute):
            # si esta le respondemos que no necesita nada.
            return None
        # si no hay nadie que lo cubra miramos para abajo a quien perjudicamos
        products = self.add_attribute_look_down(attribute=attribute)
        products_in_risk = []
        for p in products:
            if not p.is_attribute_in(attribute=attribute):
                products_in_risk.append(p)
        return products_in_risk

    # dividir esto en add_dinamic_attribute_check y add_dinamic_attribute para poder reutilizar el check en add_categorie
    def add_dinamic_attribute(self, 
        attribute:Attribute,
        product_variant_implementations):
        #[{"product_id": id, "variants": [{"variant_id": id, "value": value}]}]
        impact = self.add_attribute_check_family_impact(attribute=attribute)
        
        # algun ancestro ya lo cubre, nada que hacer
        if impact is None:
            return {}

        # no hay productos perjudicados, agregamos libre
        if not impact:
            if attribute.key not in self._attribute_keys:
                self.attributes.append(attribute)
                self._attribute_keys.add(attribute.key)
            return {}

        #si hay impacto
        # construimos set de product_ids en riesgo y de los que llegan, chequeando duplicados
        impact_product_ids = {p.id for p in impact}
        impl_product_ids = set()
        for entry in product_variant_implementations:
            pid = entry["product_id"]
            if pid in impl_product_ids:
                return impact  # product_id duplicado
            impl_product_ids.add(pid)

        # deben cubrir exactamente los mismos productos
        if impact_product_ids != impl_product_ids:
            return impact

        impact_map = {p.id: p for p in impact}
        pending = []  # (variant, AttributeImplementation) a aplicar si todo matchea

        for entry in product_variant_implementations:
            product = impact_map[entry["product_id"]]
            product_variant_ids = {v.id for v in product.variants}
            variants_map = {v.id: v for v in product.variants}

            # chequeamos duplicados de variant_id y construimos set de los que llegan
            entry_variant_ids = set()
            for v_entry in entry["variants"]:
                vid = v_entry["variant_id"]
                if vid in entry_variant_ids:
                    return impact  # variant_id duplicado
                entry_variant_ids.add(vid)

            # deben cubrir exactamente las variantes del producto
            if product_variant_ids != entry_variant_ids:
                return impact

            # chequeamos valores y acumulamos cambios pendientes
            for v_entry in entry["variants"]:
                try:
                    if not attribute.check_value(v_entry["value"]):
                        return impact
                except ValueError:
                    return impact
                impl = AttributeImplementation(attribute=attribute, value=v_entry["value"])
                pending.append((variants_map[v_entry["variant_id"]], impl))

        # todo matcheó, aplicamos
        for variant, impl in pending:
            variant.attribute_implementations.append(impl)

        self.attributes.append(attribute)
        self._attribute_keys.add(attribute.key)
        return {}


    def add_static_attribute(self, attribute:Attribute, implementations):
        pass

    def del_attribute_check_family_impact(self,
        attribute:Attribute,
        is_static:bool=False
        ):
        pass

    def del_attribute(self, attibute:Attribute):
        # tiene que verificar que no perjudique productos, es decir, ancestros tienen que tener ese atributo, o todos los herederos tenerlo propiamente. retorna perjudicados si los hay, sino efectua.
        pass

    def add_categorie(self,categorie:Category,):
        # no puede tener productos si quiere tener categorias
        # cosas que pueden pasar si estan habilitados los attributes y add categoria

        # si el hijo a agregar tiene padre responder el error. 

        # que tengamos padre con atributos y o rescursivamente abuelos y asi.
        # vamos a recolectar todos los attributos sin replica que hay para arriba.
        # y agregarles sin replica tampoco lo que ya tenemos.
        # vamos a iterarlos para abajo viendo que impacta y agregandolo a la lista.

        # se verifica que todas las implementaciones necesarias respondidas macheen con las que llegaron por parametro y sino vamos a responder las impl necesarias
        # si machean implementan.
        # se agrega al padre.

        pass

    def del_categorie(self,categorie:Category):
        # tiene que verificar que no perjudique productos, es decir, ancestros tienen que tener ese atributo, o todos los herederos tenerlo propiamente. retorna perjudicados si los hay, sino efectua.
        pass

    def create_product(self, product):
        # el producto vive en la categoria
        pass

    def del_product(self, product):
        # se elimina el producto, todo en el.
        pass

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

class Variant: # hereda todas las propiedades por asociacion con el producto, y implementa obligatoriamente los atributos del producto y de la categoria.
    def __init__(self, attribute_implementations:list=None, id:int=None,):
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
    attributes_implementations: list = None, 
    attributes: list = None, 
    variants: list = None
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
        self.attributes = attributes or [] # lista de objetos Attribute
        self._attribute_keys = {a.key for a in self.attributes}
        self.variants = variants or [] # lista de objetos Variant

    def is_attribute_in(self, attribute: Attribute):
        return attribute.key in self._attribute_keys

    def get_attributes(self):
        attributes = self.attributes.copy()
        attributes += self.category.get_attributes()
        return attributes

    def add_dinamic_attribute(self,
        attribute:Attribute,
        variant_options:list = None,
        ):
        # variant_options[{ "variant_id": "value" },...] struct que llega.
        #debe verificar que no este, y ademas pedir data de variantes para aplicar los cambios.
        # pedimos atributos purgados
        needed_attributes = self.get_needed_atributes_implementations()
        needed_keys = {a.key for a in needed_attributes}
        if attribute.key in needed_keys:
            self.attributes.append(attribute)
            self._attribute_keys.add(attribute.key)
            return True
        # si no esta debemos checkear que datos necesito y efectuar si es valido
        #hago un set con las id de las variantes y con los id pasado en variant options
        #agregando los id en variant variant_options_id verifico que no haya id duplicados, si los hay retorno false
        # ids de las variantes que tiene el producto
        variant_options_id = set()
        variants_id = {v.id for v in self.variants}
        # ids que llegan en variant_options, chequeando duplicados
        for opt in variant_options:
            vid = opt["variant_id"]
            if vid in variant_options_id:
                return False  # id duplicado en los datos que llegan
            variant_options_id.add(vid)
        # verificar que sean exactamente los mismos
        if variants_id != variant_options_id:
            return False

        # verificamos valores y tipado
        try:
            for vo in variant_options:
                attribute.check_value(vo["value"])
        except ValueError as error:
            print(error)
            return False

        # estan bien entonces les agrego las attribute implementation
        variants_map = {v.id: v for v in self.variants}
        for opt in variant_options:
            variant = variants_map[opt["variant_id"]]
            impl = AttributeImplementation(attribute=attribute, value=opt["value"])
            variant.attribute_implementations.append(impl)

        self.attributes.append(attribute)
        self._attribute_keys.add(attribute.key)
        return True

    def add_static_attribute(self,
        attribute:Attribute,
        implementation:AttributeImplementation
        ):
        # verifica que el value sea correcto.
        attribute.check_value(implementation.value)
        # verifica que exista la subscripcion.
        needed_keys = {a.key for a in self.get_needed_atributes_implementations(is_static=True)}
        if attribute.key in needed_keys:
            #verifica que la implementacion no sea repetida, redundante pero por las dudas
            if implementation.attribute.key in self._impl_keys:
                raise ValueError("La implementacion ya esta hecha")

            # agrega la implementacion
            self.attributes_implementations.append(implementation)
            self._impl_keys.add(implementation.attribute.key)
            return True

        return False

    def del_attribute():
        #verificar que no joda porque la ancestros contienen ese attribute.
        pass

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

    def _add_variant(self, variant:Variant):
        self.variants.append(variant)

    def del_variant(self,variant_id:int):
        pass

    def add_product_implementation(self, attribute_implementation:AttributeImplementation):
        if not attribute_implementation.attribute.is_static:
            raise ValueError("Estas intentando meter un atributo dinamico como implementacion estatica")

        # chequeamos tipo de dato y que esta en attributs del producto o categoria
        try: 
            self._check_implementation(attr_impl=attribute_implementation)
        except ValueError as error:
            print(error)    
            return False

        # verificar si el atributo ya esta implementado en el producto
        if attribute_implementation.attribute.key in self._impl_keys:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado para este producto")

        self.attributes_implementations.append(attribute_implementation)
        self._impl_keys.add(attribute_implementation.attribute.key)

    def _check_implementation(self, attr_impl:AttributeImplementation): #mixed
        # verificar que el valor sea valido segun el tipo de dato
        if not attr_impl.attribute.check_value(attr_impl.value):
            raise ValueError(f"El valor '{attr_impl.value}' no es válido para el atributo '{attr_impl.attribute.name}'.")
        # verificar que el atributo este definido en el producto o en la categoria
        needed_keys = {a.key for a in self.get_needed_atributes_implementations(is_static=True)}
        if attr_impl.attribute.key not in needed_keys:
            raise ValueError(f"La implimentacion es de un attributo que no se encuentra subscripto.")
        return True
        
    # da los atributos necesario que requeriria una variante o producto depende del parametro
    def get_needed_atributes_implementations(self, is_static:bool=False) -> set:
        all_attributes = self.get_attributes()
        result = set()
        for attr in all_attributes:
            if attr.is_static == is_static:
                result.add(attr)
        return result

    def create_variant_by_implementations(self, implementations:list[AttributeImplementation]):
        needed_attributes = self.get_needed_atributes_implementations()

        # construimos el set de atributos de las implementaciones recibidas, detectando duplicados
        impl_attributes = set()
        for impl in implementations:
            if impl.attribute in impl_attributes:
                print(f"Error: atributo '{impl.attribute.name}' duplicado en las implementaciones.")
                return None
            impl_attributes.add(impl.attribute)

        # los sets tienen que ser identicos
        if impl_attributes != needed_attributes:
            print("Error: las implementaciones no coinciden con los atributos requeridos.")
            return None

        # ya sabemos que las implementaciones para los atributos son los que tiene que poner, ahora mandamos a chequear los types para los values.
        for i in implementations:
            try:
                i.attribute.check_value(i.value)
            except ValueError as error:
                print(f"Error en tipo: {error}")
                return None
        # una vez chequeado verificamos que no haya otra implementacion igual
            
        # por ultimo agregamos la variante
        varian = Variant(attribute_implementations=implementations)
        self._add_variant(variant=varian)

    # helpers para category add and del attributes

    def get_add_attribute_impact(self, attribute: Attribute) -> dict | None:
        # si ya lo tiene, no impacta
        if self.is_attribute_in(attribute):
            return None
        # si no lo tiene, devuelve sus variant ids listos para appendear
        return { self.id: [v.id for v in self.variants] }


#como va a viajar la informacion?
# la informacion va a viajar como producto json y sus attr de producto y adentro variants json cada una con sus espesificaciones de attr.


#testing area

# ── atributos ──────────────────────────────────────────────────────────────
attr_color = Attribute(key="color", name="Color", data_type="enum", id=1)
attr_color.add_enum_value("rojo")
attr_color.add_enum_value("azul")
attr_color.add_enum_value("verde")

attr_talle = Attribute(key="talle", name="Talle", data_type="text", id=2)

# ── categoria con attr_talle ya definido ───────────────────────────────────
cat = Category(name="Ropa", id=10, attributes=[attr_talle])

# ── variantes ──────────────────────────────────────────────────────────────
var1 = Variant(id=1, attribute_implementations=[
    AttributeImplementation(attribute=attr_talle, value="M")
])
var2 = Variant(id=2, attribute_implementations=[
    AttributeImplementation(attribute=attr_talle, value="L")
])
var3 = Variant(id=3, attribute_implementations=[
    AttributeImplementation(attribute=attr_talle, value="S")
])
var4 = Variant(id=4, attribute_implementations=[
    AttributeImplementation(attribute=attr_talle, value="XL")
])

# ── productos ──────────────────────────────────────────────────────────────
prod1 = Product(code="P001", title="Remera A", price=100.0, description="desc", brand="Nike",
                id=1, category=cat, attributes=[attr_talle], variants=[var1, var2])
prod2 = Product(code="P002", title="Remera B", price=120.0, description="desc", brand="Adidas",
                id=2, category=cat, attributes=[attr_talle], variants=[var3, var4])

cat.products = [prod1, prod2]

print("=== TEST 1: caso feliz - todo matchea ===")
result = cat.add_dinamic_attribute(
    attribute=attr_color,
    product_variant_implementations=[
        {"product_id": 1, "variants": [
            {"variant_id": 1, "value": "rojo"},
            {"variant_id": 2, "value": "azul"},
        ]},
        {"product_id": 2, "variants": [
            {"variant_id": 3, "value": "verde"},
            {"variant_id": 4, "value": "rojo"},
        ]},
    ]
)
print("resultado (esperado {}):", result)
print("attr_color en cat:", attr_color.key in cat._attribute_keys)
print("var1 impls:", [(i.attribute.key, i.value) for i in var1.attribute_implementations])
print("var3 impls:", [(i.attribute.key, i.value) for i in var3.attribute_implementations])

print()
print("=== TEST 2: ancestro ya cubre - no hace nada ===")
cat2 = Category(name="Ropa Deportiva", id=11, attributes=[], father_categorie=cat)
result2 = cat2.add_dinamic_attribute(attribute=attr_color, product_variant_implementations=[])
print("resultado (esperado {}):", result2)

print()
print("=== TEST 3: valor invalido para enum ===")
attr_color2 = Attribute(key="color2", name="Color2", data_type="enum", id=3)
attr_color2.add_enum_value("negro")

cat3 = Category(name="Pantalones", id=12, attributes=[attr_talle])
var5 = Variant(id=5, attribute_implementations=[AttributeImplementation(attribute=attr_talle, value="M")])
prod3 = Product(code="P003", title="Pantalon", price=200.0, description="desc", brand="Puma",
                id=3, category=cat3, attributes=[attr_talle], variants=[var5])
cat3.products = [prod3]

result3 = cat3.add_dinamic_attribute(
    attribute=attr_color2,
    product_variant_implementations=[
        {"product_id": 3, "variants": [
            {"variant_id": 5, "value": "amarillo"},  # no esta en enum_values
        ]},
    ]
)
print("resultado (esperado lista con prod3):", result3)
print("attr_color2 en cat3 (esperado False):", attr_color2.key in cat3._attribute_keys)

print()
print("=== TEST 4: faltan variantes en la implementacion ===")
attr_material = Attribute(key="material", name="Material", data_type="text", id=4)
cat4 = Category(name="Buzos", id=13, attributes=[attr_talle])
var6 = Variant(id=6, attribute_implementations=[AttributeImplementation(attribute=attr_talle, value="S")])
var7 = Variant(id=7, attribute_implementations=[AttributeImplementation(attribute=attr_talle, value="XL")])
prod4 = Product(code="P004", title="Buzo", price=300.0, description="desc", brand="Under",
                id=4, category=cat4, attributes=[attr_talle], variants=[var6, var7])
cat4.products = [prod4]

result4 = cat4.add_dinamic_attribute(
    attribute=attr_material,
    product_variant_implementations=[
        {"product_id": 4, "variants": [
            {"variant_id": 6, "value": "algodon"},  # falta var7
        ]},
    ]
)
print("resultado (esperado lista con prod4):", result4)
print("attr_material en cat4 (esperado False):", attr_material.key in cat4._attribute_keys)