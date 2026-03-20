from models import Product,Category,Attribute,Variant,AttributeImplementation
from product_repo import ProductRepo
from category_repo import CategoryRepo
from attributes_repo import AttributeRepo

# --- creaciones

#dinamic attribute
da_color = Attribute(key="color",name="color",data_type="enum")
da_color.add_enum_value("rojo")
da_color.add_enum_value("azul")
da_color.add_enum_value("amarillo")
#static attribute
peso = Attribute(key="peso_g",name="peso (g)",data_type="number",is_static=True)
material = Attribute(key="material",name="material",data_type="enum",is_static=True)
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
                    category=categoria,
                    attributes_implementations=[AttributeImplementation(attribute=peso,value="237")]
                    )  
# creamos variantes
casio_x82.create_variant_by_implementations(implementations=[AttributeImplementation(da_color,"rojo")])
casio_x82.create_variant_by_implementations(implementations=[AttributeImplementation(da_color,"azul")])

# --- persistencia
db_color = AttributeRepo().save(da_color)
da_color.id = db_color.id
db_peso=AttributeRepo().save(peso)
peso.id = db_peso.id
db_material=AttributeRepo().save(material)
material.id = db_material.id
db_categoria=CategoryRepo().save(categoria)
categoria.id=db_categoria.id


#ProductRepo().save(casio_x82)

producto=ProductRepo().read_by_code("x82asdaf")
import json
print(json.dumps(producto.to_json(), indent=4, ensure_ascii=False))

# --- eliminaciones 