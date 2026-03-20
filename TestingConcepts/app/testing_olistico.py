from models import Product,Category,Attribute,Variant,AttributeImplementation
from product_repo import ProductRepo
from category_repo import CategoryRepo
from attributes_repo import AttributeRepo

#creaciones

#dinamic attribute
da_color = Attribute("color","color","enum")
da_color.add_enum_value("rojo")
da_color.add_enum_value("azul")
da_color.add_enum_value("amarillo")
#static attribute
peso = Attribute("peso_g","peso (g)","number",is_static=True)
material = Attribute("material","material","enum",is_static=True)
material.add_enum_value("acero")
material.add_enum_value("oro")
material.add_enum_value("plata")

#categorias
categoria = Category(name="relojes",attributes=[material])

#creamos producto
casio_x82 = Product(code="x82asdaf",
                    title="Casio x82 masculino oro",
                    price=250,
                    description="blablabla",
                    brand="casio",
                    attributes=[peso,da_color],
                    attributes_implementations=[AttributeImplementation(attribute=peso,value="237")]
                    )  
casio_x82.create_variant_by_implementations()

#eliminaciones 