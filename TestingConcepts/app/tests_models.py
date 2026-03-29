from models import *

#testing area

def test():
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
    prod1 = Product(code="P001", title="Remera A", price=100.0, description="desc",     brand="Nike",
                    id=1, category=cat, attributes=[attr_talle], variants=[var1, var2])
    prod2 = Product(code="P002", title="Remera B", price=120.0, description="desc",     brand="Adidas",
                    id=2, category=cat, attributes=[attr_talle], variants=[var3, var4])

    cat.products = [prod1, prod2]

    print("=== TEST 1: caso feliz - todo matchea ===")
    import json
    print(f"Productos que retornaria: {json.dumps([p.to_json() for p in cat.    _add_attribute_variant_impact_check(attribute=attr_color,   product_variant_implementations=[])], indent=2)}")

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
    print("var1 impls:", [(i.attribute.key, i.value) for i in var1. attribute_implementations])
    print("var3 impls:", [(i.attribute.key, i.value) for i in var3. attribute_implementations])

    print()
    print("=== TEST 2: ancestro ya cubre - no hace nada ===")
    cat2 = Category(name="Ropa Deportiva", id=11, attributes=[], father_categorie=cat)
    result2 = cat2.add_dinamic_attribute(attribute=attr_color,  product_variant_implementations=[])
    print("resultado (esperado {}):", result2)

    print()
    print("=== TEST 3: valor invalido para enum ===")
    attr_color2 = Attribute(key="color2", name="Color2", data_type="enum", id=3)
    attr_color2.add_enum_value("negro")

    cat3 = Category(name="Pantalones", id=12, attributes=[attr_talle])
    var5 = Variant(id=5, attribute_implementations=[AttributeImplementation (attribute=attr_talle, value="M")])
    prod3 = Product(code="P003", title="Pantalon", price=200.0, description="desc",     brand="Puma",
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
    print("attr_color2 en cat3 (esperado False):", attr_color2.key in cat3. _attribute_keys)

    print()
    print("=== TEST 4: faltan variantes en la implementacion ===")
    attr_material = Attribute(key="material", name="Material", data_type="text", id=4)
    cat4 = Category(name="Buzos", id=13, attributes=[attr_talle])
    var6 = Variant(id=6, attribute_implementations=[AttributeImplementation (attribute=attr_talle, value="S")])
    var7 = Variant(id=7, attribute_implementations=[AttributeImplementation (attribute=attr_talle, value="XL")])
    prod4 = Product(code="P004", title="Buzo", price=300.0, description="desc",     brand="Under",
                    id=4, category=cat4, attributes=[attr_talle], variants=[var6,   var7])
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
    print("attr_material en cat4 (esperado False):", attr_material.key in cat4. _attribute_keys)

    print()
    print("=== TEST 5 (static): caso feliz ===")
    attr_descripcion = Attribute(key="descripcion", name="Descripcion", data_type="text", id=5, is_static=True)
    cat5 = Category(name="Accesorios", id=14, attributes=[])
    prod5 = Product(code="P005", title="Cinturon", price=50.0, description="desc", brand="Zara",
                    id=5, category=cat5, variants=[])
    prod6 = Product(code="P006", title="Cartera", price=80.0, description="desc", brand="Zara",
                    id=6, category=cat5, variants=[])
    cat5.products = [prod5, prod6]

    result5 = cat5.add_static_attribute(
        attribute=attr_descripcion,
        implementations=[
            {"product_id": 5, "value": "Cinturon de cuero"},
            {"product_id": 6, "value": "Cartera de lona"},
        ]
    )
    print("resultado (esperado {}):", result5)
    print("attr_descripcion en cat5:", attr_descripcion.key in cat5._attribute_keys)
    print("impl prod5:", [(i.attribute.key, i.value) for i in prod5.attributes_implementations])
    print("impl prod6:", [(i.attribute.key, i.value) for i in prod6.attributes_implementations])

    print()
    print("=== TEST 6 (static): valor invalido ===")
    attr_peso = Attribute(key="peso", name="Peso", data_type="number", id=6, is_static=True)
    cat6 = Category(name="Herramientas", id=15, attributes=[])
    prod7 = Product(code="P007", title="Martillo", price=30.0, description="desc", brand="Stanley",
                    id=7, category=cat6, variants=[])
    cat6.products = [prod7]

    result6 = cat6.add_static_attribute(
        attribute=attr_peso,
        implementations=[
            {"product_id": 7, "value": "no es un numero"},  # tipo incorrecto
        ]
    )
    print("resultado (esperado lista con prod7):", result6)
    print("attr_peso en cat6 (esperado False):", attr_peso.key in cat6._attribute_keys)

    print()
    print("=== TEST 7 (static): atributo no estatico ===")
    attr_dinamico = Attribute(key="dinamico", name="Dinamico", data_type="text", id=7, is_static=False)
    try:
        cat5.add_static_attribute(attribute=attr_dinamico, implementations=[])
        print("ERROR: deberia haber lanzado excepcion")
    except ValueError as e:
        print("excepcion correcta:", e)

#test()

def test2():
    # ── atributos ──────────────────────────────────────────────────────────
    # el hijo ya tiene "material" — el padre trae "color" y "talle" nuevos + "material" que ya esta
    attr_color = Attribute(key="color", name="Color", data_type="enum", id=1)
    attr_color.add_enum_value("rojo")
    attr_color.add_enum_value("azul")
    attr_color.add_enum_value("negro")
    attr_talle = Attribute(key="talle", name="Talle", data_type="text", id=2)
    attr_material = Attribute(key="material", name="Material", data_type="text", id=3)

    # ── nuevo padre: color + talle + material ─────────────────────────────
    nuevo_padre = Category(name="Ropa", id=10, attributes=[attr_color, attr_talle, attr_material])

    # ── categoria hija: ya tiene material, le faltan color y talle ────────
    cat_hija = Category(name="Remeras", id=11, attributes=[attr_material])

    # ── prod1: 2 variantes ────────────────────────────────────────────────
    var1 = Variant(id=1, attribute_implementations=[
        AttributeImplementation(attribute=attr_material, value="algodon")
    ])
    var2 = Variant(id=2, attribute_implementations=[
        AttributeImplementation(attribute=attr_material, value="poliester")
    ])
    prod1 = Product(code="P001", title="Remera A", price=100.0, description="desc", brand="Nike",
                    id=1, category=cat_hija, attributes=[attr_material], variants=[var1, var2])

    # ── prod2: 2 variantes ────────────────────────────────────────────────
    var3 = Variant(id=3, attribute_implementations=[
        AttributeImplementation(attribute=attr_material, value="algodon")
    ])
    var4 = Variant(id=4, attribute_implementations=[
        AttributeImplementation(attribute=attr_material, value="lino")
    ])
    prod2 = Product(code="P002", title="Remera B", price=120.0, description="desc", brand="Adidas",
                    id=2, category=cat_hija, attributes=[attr_material], variants=[var3, var4])

    cat_hija.products = [prod1, prod2]

    print("=== TEST2-1: caso feliz - 2 productos, 3 attrs en padre (1 ya cubierto) ===")
    # solo color y talle deben generar impacto, material ya lo tiene la hija
    result = cat_hija.change_categorie_father(
        father_categorie=nuevo_padre,
        implementations={
            "color": [
                (1, [{"variant_id": 1, "value": "rojo"}, {"variant_id": 2, "value": "negro"}]),
                (2, [{"variant_id": 3, "value": "azul"}, {"variant_id": 4, "value": "rojo"}]),
            ],
            "talle": [
                (1, [{"variant_id": 1, "value": "M"}, {"variant_id": 2, "value": "L"}]),
                (2, [{"variant_id": 3, "value": "S"}, {"variant_id": 4, "value": "XL"}]),
            ],
        }
    )
    print("resultado (esperado {}):", result)
    print("padre asignado:", cat_hija.father_categorie.name)
    print("hija en subcategories:", cat_hija in nuevo_padre.subcategories)
    print("var1 impls:", [(i.attribute.key, i.value) for i in var1.attribute_implementations])
    print("var2 impls:", [(i.attribute.key, i.value) for i in var2.attribute_implementations])
    print("var3 impls:", [(i.attribute.key, i.value) for i in var3.attribute_implementations])
    print("var4 impls:", [(i.attribute.key, i.value) for i in var4.attribute_implementations])

    print()
    print("=== TEST2-2: falta un atributo en implementations ===")
    cat_hija2 = Category(name="Pantalones", id=12, attributes=[])
    var3 = Variant(id=3, attribute_implementations=[])
    prod2 = Product(code="P002", title="Pantalon", price=80.0, description="desc", brand="Zara",
                    id=2, category=cat_hija2, variants=[var3])
    cat_hija2.products = [prod2]

    result2 = cat_hija2.change_categorie_father(
        father_categorie=nuevo_padre,
        implementations={
            "color": [(2, [{"variant_id": 3, "value": "rojo"}])],
            # falta talle
        }
    )
    print("resultado (esperado impact_map):", type(result2))
    print("padre NO asignado (esperado None):", cat_hija2.father_categorie)

    print()
    print("=== TEST2-3: valor invalido para enum ===")
    cat_hija3 = Category(name="Buzos", id=13, attributes=[])
    var4 = Variant(id=4, attribute_implementations=[])
    prod3 = Product(code="P003", title="Buzo", price=120.0, description="desc", brand="Adidas",
                    id=3, category=cat_hija3, variants=[var4])
    cat_hija3.products = [prod3]

    result3 = cat_hija3.change_categorie_father(
        father_categorie=nuevo_padre,
        implementations={
            "color": [(3, [{"variant_id": 4, "value": "verde"}])],  # verde no esta en enum
            "talle": [(3, [{"variant_id": 4, "value": "XL"}])],
        }
    )
    print("resultado (esperado impact_map):", type(result3))
    print("padre NO asignado (esperado None):", cat_hija3.father_categorie)

    print()
    print("=== TEST2-4: padre tiene productos - debe lanzar excepcion ===")
    padre_con_productos = Category(name="ConProductos", id=20, attributes=[])
    var5 = Variant(id=5, attribute_implementations=[])
    prod_en_padre = Product(code="P099", title="X", price=1.0, description="x", brand="x",
                            id=99, category=padre_con_productos, variants=[var5])
    padre_con_productos.products = [prod_en_padre]
    try:
        cat_hija3.change_categorie_father(father_categorie=padre_con_productos, implementations={})
        print("ERROR: deberia haber lanzado excepcion")
    except ValueError as e:
        print("excepcion correcta:", e)

    print()
    print("=== TEST2-5: sin impacto - asigna directo ===")
    padre_sin_attrs = Category(name="SinAtributos", id=21, attributes=[])
    cat_hija4 = Category(name="Gorros", id=14, attributes=[])
    result5 = cat_hija4.change_categorie_father(father_categorie=padre_sin_attrs, implementations={})
    print("resultado (esperado {}):", result5)
    print("padre asignado:", cat_hija4.father_categorie.name)

#test2()

def test3():
    # ── delete_all=0: hay perjudicados, retorna lista sin modificar nada ──────
    print("=== TEST3-1: delete_all=0 - retorna perjudicados sin hacer nada ===")
    attr_color = Attribute(key="color", name="Color", data_type="enum", id=1)
    attr_color.add_enum_value("rojo")

    cat1 = Category(name="Ropa", id=10, attributes=[attr_color])
    # prod1: no tiene color propio (perjudicado)
    prod1 = Product(code="P001", title="Remera A", price=100.0, description="desc", brand="Nike",
                    id=1, category=cat1,
                    attributes_implementations=[AttributeImplementation(attribute=attr_color, value="rojo")])
    # prod2: tiene color propio (no perjudicado)
    prod2 = Product(code="P002", title="Remera B", price=120.0, description="desc", brand="Adidas",
                    id=2, category=cat1, attributes=[attr_color])
    cat1.products = [prod1, prod2]

    result1 = cat1.del_attribute(attribute=attr_color, delete_all=0)
    print("perjudicados (esperado [Remera A]):", [p.title for p in result1])
    print("color sigue en cat1 (esperado True):", attr_color.key in cat1._attribute_keys)

    # ── delete_all=1: elimina implementaciones de perjudicados y el attr de la cat
    print()
    print("=== TEST3-2: delete_all=1 - elimina implementaciones y attr de categoria ===")
    attr_talle = Attribute(key="talle", name="Talle", data_type="text", id=2)
    cat2 = Category(name="Pantalones", id=11, attributes=[attr_talle])
    prod3 = Product(code="P003", title="Pantalon A", price=80.0, description="desc", brand="Zara",
                    id=3, category=cat2,
                    attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="M")])
    cat2.products = [prod3]

    cat2.del_attribute(attribute=attr_talle, delete_all=1)
    print("talle en cat2 (esperado False):", attr_talle.key in cat2._attribute_keys)
    print("attributes_implementations prod3 (esperado []):", prod3.attributes_implementations)
    print("_impl_keys prod3 (esperado set()):", prod3._impl_keys)

    # ── delete_all=2: inyecta attr en perjudicados y lo elimina de la cat ─────
    print()
    print("=== TEST3-3: delete_all=2 - inyecta attr en perjudicados y lo elimina de la categoria ===")
    attr_material = Attribute(key="material", name="Material", data_type="text", id=3)
    cat3 = Category(name="Buzos", id=12, attributes=[attr_material])
    prod4 = Product(code="P004", title="Buzo A", price=150.0, description="desc", brand="Puma",
                    id=4, category=cat3,
                    attributes_implementations=[AttributeImplementation(attribute=attr_material, value="algodon")])
    cat3.products = [prod4]

    cat3.del_attribute(attribute=attr_material, delete_all=2)
    print("material en cat3 (esperado False):", attr_material.key in cat3._attribute_keys)
    print("material en prod4._attribute_keys (esperado True):", attr_material.key in prod4._attribute_keys)
    print("material en prod4.attributes (esperado True):", any(a.key == attr_material.key for a in prod4.attributes))

test3()