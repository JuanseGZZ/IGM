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
    # ── jerarquia ──────────────────────────────────────────────────────────────
    # Moda [attr_marca]
    #   └── Ropa [attr_color]
    #         ├── Remeras [attr_talle, attr_material]
    #         │     prod1 (talle:impl, material:impl)  -- perjudicado en ambos
    #         │     prod2 (talle:impl, material:own)   -- perjudicado en talle, no en material
    #         │     prod3 (talle:own,  material:impl)  -- no perjudicado en talle, si en material
    #         └── Pantalones [attr_largo]
    #               prod4 (largo:impl)  -- perjudicado
    #               prod5 (largo:impl)  -- perjudicado
    #               prod6 (largo:own)   -- no perjudicado

    attr_marca    = Attribute(key="marca",    name="Marca",    data_type="text", id=1)
    attr_color    = Attribute(key="color",    name="Color",    data_type="enum", id=2)
    attr_color.add_enum_value("rojo"); attr_color.add_enum_value("azul")
    attr_talle    = Attribute(key="talle",    name="Talle",    data_type="text", id=3)
    attr_material = Attribute(key="material", name="Material", data_type="text", id=4)
    attr_largo    = Attribute(key="largo",    name="Largo",    data_type="number", id=5)

    cat_moda     = Category(name="Moda",      id=1, attributes=[attr_marca])
    cat_ropa     = Category(name="Ropa",      id=2, attributes=[attr_color],             father_categorie=cat_moda)
    cat_remeras  = Category(name="Remeras",   id=3, attributes=[attr_talle, attr_material], father_categorie=cat_ropa)
    cat_pantalon = Category(name="Pantalones",id=4, attributes=[attr_largo],             father_categorie=cat_ropa)
    cat_moda.subcategories     = [cat_ropa]
    cat_ropa.subcategories     = [cat_remeras, cat_pantalon]

    prod1 = Product(code="P001", title="Remera Lisa",   price=100.0, description="d", brand="Nike",   id=1, category=cat_remeras,
                    attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="M"),
                                                AttributeImplementation(attribute=attr_material, value="algodon")])
    prod2 = Product(code="P002", title="Remera Rayada", price=120.0, description="d", brand="Adidas", id=2, category=cat_remeras,
                    attributes=[attr_material],
                    attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="L")])
    prod3 = Product(code="P003", title="Remera Polo",   price=140.0, description="d", brand="Puma",   id=3, category=cat_remeras,
                    attributes=[attr_talle],
                    attributes_implementations=[AttributeImplementation(attribute=attr_material, value="poliester")])
    cat_remeras.products = [prod1, prod2, prod3]

    prod4 = Product(code="P004", title="Jean Slim",     price=200.0, description="d", brand="Levis",  id=4, category=cat_pantalon,
                    attributes_implementations=[AttributeImplementation(attribute=attr_largo, value="32")])
    prod5 = Product(code="P005", title="Jean Wide",     price=220.0, description="d", brand="Levis",  id=5, category=cat_pantalon,
                    attributes_implementations=[AttributeImplementation(attribute=attr_largo, value="34")])
    prod6 = Product(code="P006", title="Chino",         price=180.0, description="d", brand="Zara",   id=6, category=cat_pantalon,
                    attributes=[attr_largo])
    cat_pantalon.products = [prod4, prod5, prod6]

    # ── TEST3-1: delete_all=0 sobre attr_talle en cat_remeras ─────────────────
    # ningún ancestro tiene talle → perjudicados: prod1, prod2 (no tienen talle propio)
    print("=== TEST3-1: delete_all=0 en Remeras/talle ===")
    result1 = cat_remeras.del_attribute(attribute=attr_talle, delete_all=0)
    print("perjudicados (esperado [Remera Lisa, Remera Rayada]):", [p.title for p in result1])
    print("talle sigue en cat_remeras (esperado True):", attr_talle.key in cat_remeras._attribute_keys)

    # ── TEST3-2: delete_all=0 sobre attr_material en cat_remeras ──────────────
    # perjudicados: prod1, prod3 (no tienen material propio)
    print()
    print("=== TEST3-2: delete_all=0 en Remeras/material ===")
    result2 = cat_remeras.del_attribute(attribute=attr_material, delete_all=0)
    print("perjudicados (esperado [Remera Lisa, Remera Polo]):", [p.title for p in result2])
    print("material sigue en cat_remeras (esperado True):", attr_material.key in cat_remeras._attribute_keys)

    # ── TEST3-3: delete_all=1 sobre attr_talle en cat_remeras ─────────────────
    # elimina impls de talle en prod1 y prod2, no toca prod3 (tiene talle propio)
    print()
    print("=== TEST3-3: delete_all=1 en Remeras/talle ===")
    cat_remeras.del_attribute(attribute=attr_talle, delete_all=1)
    print("talle en cat_remeras (esperado False):", attr_talle.key in cat_remeras._attribute_keys)
    print("impl talle prod1 (esperado []):", [i.attribute.key for i in prod1.attributes_implementations if i.attribute.key == "talle"])
    print("impl talle prod2 (esperado []):", [i.attribute.key for i in prod2.attributes_implementations if i.attribute.key == "talle"])
    print("talle en prod3._attribute_keys intacto (esperado True):", attr_talle.key in prod3._attribute_keys)

    # ── TEST3-4: delete_all=2 sobre attr_material en cat_remeras ──────────────
    # inyecta material en prod1 y prod3 (perjudicados), no toca prod2 (tiene material propio)
    print()
    print("=== TEST3-4: delete_all=2 en Remeras/material ===")
    cat_remeras.del_attribute(attribute=attr_material, delete_all=2)
    print("material en cat_remeras (esperado False):", attr_material.key in cat_remeras._attribute_keys)
    print("material en prod1._attribute_keys (esperado True):", attr_material.key in prod1._attribute_keys)
    print("material en prod3._attribute_keys (esperado True):", attr_material.key in prod3._attribute_keys)
    print("material en prod2._attribute_keys intacto (esperado True):", attr_material.key in prod2._attribute_keys)

    # ── TEST3-5: delete_all=1 sobre attr_largo en cat_pantalon ────────────────
    # perjudicados: prod4, prod5. prod6 tiene largo propio.
    print()
    print("=== TEST3-5: delete_all=1 en Pantalones/largo ===")
    cat_pantalon.del_attribute(attribute=attr_largo, delete_all=1)
    print("largo en cat_pantalon (esperado False):", attr_largo.key in cat_pantalon._attribute_keys)
    print("impl largo prod4 (esperado []):", [i.attribute.key for i in prod4.attributes_implementations])
    print("impl largo prod5 (esperado []):", [i.attribute.key for i in prod5.attributes_implementations])
    print("largo en prod6._attribute_keys intacto (esperado True):", attr_largo.key in prod6._attribute_keys)

    # ── TEST3-6: ancestro cubre el atributo → sin perjudicados ────────────────
    # cat_remeras_2 es hija de cat_ropa que tiene attr_color
    # al borrar attr_color de cat_remeras_2, cat_ropa lo cubre → retorna []
    print()
    print("=== TEST3-6: ancestro cubre - sin perjudicados ===")
    cat_remeras_2 = Category(name="Remeras2", id=5, attributes=[attr_color], father_categorie=cat_ropa)
    prod7 = Product(code="P007", title="Remera Sin Color", price=90.0, description="d", brand="HyM", id=7,
                    category=cat_remeras_2,
                    attributes_implementations=[AttributeImplementation(attribute=attr_color, value="rojo")])
    cat_remeras_2.products = [prod7]
    result6 = cat_remeras_2.del_attribute(attribute=attr_color, delete_all=0)
    print("perjudicados (esperado []):", [p.title for p in result6])
    print("color eliminado de cat_remeras_2 (esperado False):", attr_color.key in cat_remeras_2._attribute_keys)

#test3()

def test4():
    # ── jerarquia ──────────────────────────────────────────────────────────────
    # Moda [attr_marca]
    #   └── Ropa [attr_color]
    #         ├── Remeras [attr_talle, attr_material]
    #         │     prod1 (talle:impl, material:impl)   perjudicado en talle y material
    #         │     prod2 (talle:impl, material:own)    perjudicado en talle, no en material
    #         │     prod3 (talle:own,  material:impl)   no perjudicado en talle, si en material
    #         │     prod4 (talle:own,  material:own)    no perjudicado en ninguno
    #         ├── Deportiva [attr_talle]                talle ya esta en Ropa? no, en Remeras si
    #         │     prod5 (talle:impl)                  perjudicado
    #         └── Vacia []                              sin productos ni atributos sobrantes

    attr_marca    = Attribute(key="marca",    name="Marca",    data_type="text", id=1)
    attr_color    = Attribute(key="color",    name="Color",    data_type="enum", id=2)
    attr_color.add_enum_value("rojo"); attr_color.add_enum_value("azul")
    attr_talle    = Attribute(key="talle",    name="Talle",    data_type="text", id=3)
    attr_material = Attribute(key="material", name="Material", data_type="text", id=4)

    def build():
        cat_moda     = Category(name="Moda",      id=1, attributes=[attr_marca])
        cat_ropa     = Category(name="Ropa",      id=2, attributes=[attr_color],              father_categorie=cat_moda)
        cat_remeras  = Category(name="Remeras",   id=3, attributes=[attr_talle, attr_material],father_categorie=cat_ropa)
        cat_deportiva= Category(name="Deportiva", id=4, attributes=[attr_talle],              father_categorie=cat_ropa)
        cat_vacia    = Category(name="Vacia",     id=5, attributes=[],                        father_categorie=cat_ropa)
        cat_moda.subcategories  = [cat_ropa]
        cat_ropa.subcategories  = [cat_remeras, cat_deportiva, cat_vacia]

        prod1 = Product(code="P001", title="Remera Lisa",    price=100.0, description="d", brand="Nike",   id=1, category=cat_remeras,
                        attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="M"),
                                                    AttributeImplementation(attribute=attr_material, value="algodon")])
        prod2 = Product(code="P002", title="Remera Rayada",  price=120.0, description="d", brand="Adidas", id=2, category=cat_remeras,
                        attributes=[attr_material],
                        attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="L")])
        prod3 = Product(code="P003", title="Remera Polo",    price=140.0, description="d", brand="Puma",   id=3, category=cat_remeras,
                        attributes=[attr_talle],
                        attributes_implementations=[AttributeImplementation(attribute=attr_material, value="poliester")])
        prod4 = Product(code="P004", title="Remera Premium", price=160.0, description="d", brand="Lacoste",id=4, category=cat_remeras,
                        attributes=[attr_talle, attr_material])
        cat_remeras.products = [prod1, prod2, prod3, prod4]

        prod5 = Product(code="P005", title="Camiseta",       price=90.0,  description="d", brand="Under",  id=5, category=cat_deportiva,
                        attributes_implementations=[AttributeImplementation(attribute=attr_talle, value="S")])
        cat_deportiva.products = [prod5]

        return cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5

    # ── TEST4-1: categoria no existe en subcategories → False ─────────────────
    print("=== TEST4-1: categoria no existe → False ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    cat_ajena = Category(name="Ajena", id=99, attributes=[])
    result = cat_ropa.del_categorie(cat_ajena, del_option=2)
    print("resultado (esperado False):", result)

    # ── TEST4-2: sin atributos sobrantes (Vacia) → elimina directo ────────────
    print()
    print("=== TEST4-2: categoria sin atributos sobrantes → elimina sin impacto ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, *_ = build()
    result = cat_ropa.del_categorie(cat_vacia, del_option=2)
    print("resultado (esperado []):", result)
    print("Vacia en subcategories de Ropa (esperado False):", cat_vacia in cat_ropa.subcategories)
    print("father_categorie de Vacia (esperado None):", cat_vacia.father_categorie)

    # ── TEST4-3: atributos cubiertos por ancestro (color en cat_ropa) ─────────
    # si cat_ropa tiene attr_color y queremos borrar una sub que solo tiene color → sin sobrantes
    print()
    print("=== TEST4-3: todos los atributos de la categoria cubiertos por padre → elimina sin impacto ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, *_ = build()
    cat_solo_color = Category(name="SoloColor", id=6, attributes=[attr_color], father_categorie=cat_ropa)
    cat_ropa.subcategories.append(cat_solo_color)
    result = cat_ropa.del_categorie(cat_solo_color, del_option=2)
    print("resultado (esperado []):", result)
    print("SoloColor en subcategories de Ropa (esperado False):", cat_solo_color in cat_ropa.subcategories)

    # ── TEST4-4: del_option=2 → retorna perjudicados sin modificar ────────────
    # Remeras tiene talle y material, Ropa solo tiene color → ambos sobrantes
    # perjudicados: prod1 (talle:impl, material:impl), prod2 (talle:impl), prod3 (material:impl)
    print()
    print("=== TEST4-4: del_option=2 - retorna perjudicados sin modificar ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    result = cat_ropa.del_categorie(cat_remeras, del_option=2)
    print("perjudicados (esperado [Remera Lisa, Remera Rayada, Remera Polo]):", sorted([p.title for p in result]))
    print("Remeras sigue en Ropa (esperado True):", cat_remeras in cat_ropa.subcategories)
    print("impl prod1 intactas (esperado 2):", len(prod1.attributes_implementations))

    # ── TEST4-5: del_option=1 → elimina impls de perjudicados y borra categoria
    print()
    print("=== TEST4-5: del_option=1 - elimina implementaciones y elimina categoria ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    result = cat_ropa.del_categorie(cat_remeras, del_option=1)
    print("resultado (esperado []):", result)
    print("Remeras en Ropa (esperado False):", cat_remeras in cat_ropa.subcategories)
    print("father_categorie Remeras (esperado None):", cat_remeras.father_categorie)
    print("impl prod1 (esperado []):", prod1.attributes_implementations)
    print("impl talle prod2 (esperado []):", [i.attribute.key for i in prod2.attributes_implementations if i.attribute.key == "talle"])
    print("impl material prod3 (esperado []):", [i.attribute.key for i in prod3.attributes_implementations if i.attribute.key == "material"])
    print("_attribute_keys prod4 intacto (esperado {talle, material}):", prod4._attribute_keys)

    # ── TEST4-6: del_option=0 → inyecta attrs sobrantes en perjudicados ───────
    print()
    print("=== TEST4-6: del_option=0 - inyecta atributos sobrantes en perjudicados ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    result = cat_ropa.del_categorie(cat_remeras, del_option=0)
    print("resultado (esperado []):", result)
    print("Remeras en Ropa (esperado False):", cat_remeras in cat_ropa.subcategories)
    print("talle en prod1._attribute_keys (esperado True):", attr_talle.key in prod1._attribute_keys)
    print("material en prod1._attribute_keys (esperado True):", attr_material.key in prod1._attribute_keys)
    print("talle en prod2._attribute_keys (esperado True):", attr_talle.key in prod2._attribute_keys)
    print("material en prod2._attribute_keys intacto (esperado True):", attr_material.key in prod2._attribute_keys)
    print("talle en prod3._attribute_keys intacto (esperado True):", attr_talle.key in prod3._attribute_keys)
    print("material en prod3._attribute_keys (esperado True):", attr_material.key in prod3._attribute_keys)
    print("prod4 sin duplicados (esperado {talle, material}):", prod4._attribute_keys)

    # ── TEST4-7: del_option=1 con un solo atributo sobrante (Deportiva/talle) ─
    print()
    print("=== TEST4-7: del_option=1 Deportiva/talle - un solo attr sobrante ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    result = cat_ropa.del_categorie(cat_deportiva, del_option=1)
    print("resultado (esperado []):", result)
    print("Deportiva en Ropa (esperado False):", cat_deportiva in cat_ropa.subcategories)
    print("impl talle prod5 (esperado []):", prod5.attributes_implementations)
    print("_impl_keys prod5 (esperado set()):", prod5._impl_keys)

    # ── TEST4-8: del_option=0 con Deportiva → inyecta talle en prod5 ──────────
    print()
    print("=== TEST4-8: del_option=0 Deportiva - inyecta talle en prod5 ===")
    cat_moda, cat_ropa, cat_remeras, cat_deportiva, cat_vacia, prod1, prod2, prod3, prod4, prod5 = build()
    result = cat_ropa.del_categorie(cat_deportiva, del_option=0)
    print("resultado (esperado []):", result)
    print("talle en prod5._attribute_keys (esperado True):", attr_talle.key in prod5._attribute_keys)
    print("Deportiva en Ropa (esperado False):", cat_deportiva in cat_ropa.subcategories)

#test4()

def test5():
    # ── jerarquia ──────────────────────────────────────────────────────────────
    # Base [attr_talle (dynamic)]
    #   └── Ropa [] (hereda talle)
    #
    # prod1: attributes=[attr_lavado (static), attr_color (dynamic)]
    #        attributes_implementations=[impl_lavado]
    #        variants: var1(color=rojo), var2(color=azul)
    #
    # prod2: attributes=[attr_talle (dynamic)] <-- cubierto por ancestro Base
    #        variants: var3(talle=M)
    #
    # prod3: attributes=[attr_material (static)] sin implementacion
    #
    # prod4: attributes=[attr_temporada (dynamic)] sin variantes

    attr_talle     = Attribute(key="talle",     name="Talle",     data_type="text",    id=1)
    attr_lavado    = Attribute(key="lavado",     name="Lavado",    data_type="boolean", id=2, is_static=True)
    attr_color     = Attribute(key="color",      name="Color",     data_type="enum",    id=3)
    attr_color.add_enum_value("rojo"); attr_color.add_enum_value("azul")
    attr_material  = Attribute(key="material",   name="Material",  data_type="text",    id=4, is_static=True)
    attr_temporada = Attribute(key="temporada",  name="Temporada", data_type="text",    id=5)

    def build():
        cat_base = Category(name="Base", id=1, attributes=[attr_talle])
        cat_ropa = Category(name="Ropa", id=2, attributes=[], father_categorie=cat_base)

        var1 = Variant(id=1, attribute_implementations=[AttributeImplementation(attribute=attr_color, value="rojo")])
        var2 = Variant(id=2, attribute_implementations=[AttributeImplementation(attribute=attr_color, value="azul")])
        prod1 = Product(code="P001", title="Remera", price=100.0, description="d", brand="Nike", id=1,
                        category=cat_ropa,
                        attributes=[attr_lavado, attr_color],
                        attributes_implementations=[AttributeImplementation(attribute=attr_lavado, value=True)],
                        variants=[var1, var2])

        var3 = Variant(id=3, attribute_implementations=[AttributeImplementation(attribute=attr_talle, value="M")])
        prod2 = Product(code="P002", title="Jean", price=200.0, description="d", brand="Levi", id=2,
                        category=cat_ropa,
                        attributes=[attr_talle],
                        variants=[var3])

        prod3 = Product(code="P003", title="Buzo", price=150.0, description="d", brand="Puma", id=3,
                        category=cat_ropa,
                        attributes=[attr_material])

        prod4 = Product(code="P004", title="Gorra", price=50.0, description="d", brand="Under", id=4,
                        category=cat_ropa,
                        attributes=[attr_temporada])

        return cat_base, cat_ropa, prod1, prod2, prod3, prod4, var1, var2, var3

    # ── TEST5-1: atributo no esta en el producto → False ─────────────────────
    print("=== TEST5-1: atributo no en producto → False ===")
    _, _, prod1, *_ = build()
    attr_ajena = Attribute(key="ajena", name="Ajena", data_type="text", id=99)
    result = prod1.del_attribute(attr_ajena)
    print("resultado (esperado False):", result)

    # ── TEST5-2: ancestro cubre el atributo → borra sin impacto ──────────────
    print()
    print("=== TEST5-2: ancestro (cat_base) ya cubre attr_talle → borra del producto sin impacto ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod2.del_attribute(attr_talle)
    print("resultado (esperado []):", result)
    print("talle en prod2._attribute_keys (esperado False):", attr_talle.key in prod2._attribute_keys)
    print("impl talle en var3 intacta (esperado True):", any(i.attribute.key == "talle" for i in var3.attribute_implementations))

    # ── TEST5-3: sin ancestro, atributo estatico sin implementacion → borra ───
    print()
    print("=== TEST5-3: sin ancestro, atributo estatico sin impl → borra directo ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod3.del_attribute(attr_material)
    print("resultado (esperado []):", result)
    print("material en prod3._attribute_keys (esperado False):", attr_material.key in prod3._attribute_keys)

    # ── TEST5-4: sin ancestro, atributo dinamico sin variantes → borra ───────
    print()
    print("=== TEST5-4: sin ancestro, atributo dinamico sin variantes → borra directo ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod4.del_attribute(attr_temporada)
    print("resultado (esperado []):", result)
    print("temporada en prod4._attribute_keys (esperado False):", attr_temporada.key in prod4._attribute_keys)

    # ── TEST5-5: estatico con impl, delete_opt=0 → retorna impls sin borrar ──
    print()
    print("=== TEST5-5: estatico con impl, delete_opt=0 → retorna impls afectadas ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod1.del_attribute(attr_lavado, delete_opt=0)
    print("cantidad impactadas (esperado 1):", len(result))
    print("key de la impl (esperado lavado):", result[0].attribute.key)
    print("lavado sigue en prod1._attribute_keys (esperado True):", attr_lavado.key in prod1._attribute_keys)
    print("impl sigue en prod1 (esperado True):", any(i.attribute.key == "lavado" for i in prod1.attributes_implementations))

    # ── TEST5-6: estatico con impl, delete_opt=1 → elimina impl y atributo ───
    print()
    print("=== TEST5-6: estatico con impl, delete_opt=1 → elimina impl y atributo ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod1.del_attribute(attr_lavado, delete_opt=1)
    print("resultado (esperado []):", result)
    print("lavado en prod1._attribute_keys (esperado False):", attr_lavado.key in prod1._attribute_keys)
    print("lavado en prod1._impl_keys (esperado False):", attr_lavado.key in prod1._impl_keys)
    print("impl lavado en prod1 (esperado []):", [i.attribute.key for i in prod1.attributes_implementations if i.attribute.key == "lavado"])

    # ── TEST5-7: dinamico con impls en variantes, delete_opt=0 → retorna variantes
    print()
    print("=== TEST5-7: dinamico con impls en variantes, delete_opt=0 → retorna variantes afectadas ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod1.del_attribute(attr_color, delete_opt=0)
    print("variantes impactadas (esperado 2):", len(result))
    print("ids (esperado {1,2}):", {v.id for v in result})
    print("color sigue en prod1._attribute_keys (esperado True):", attr_color.key in prod1._attribute_keys)
    print("impls en var1 intactas (esperado True):", any(i.attribute.key == "color" for i in var1.attribute_implementations))

    # ── TEST5-8: dinamico con impls en variantes, delete_opt=1 → elimina todo ─
    print()
    print("=== TEST5-8: dinamico con impls en variantes, delete_opt=1 → elimina impls y atributo ===")
    _, _, prod1, prod2, prod3, prod4, var1, var2, var3 = build()
    result = prod1.del_attribute(attr_color, delete_opt=1)
    print("resultado (esperado []):", result)
    print("color en prod1._attribute_keys (esperado False):", attr_color.key in prod1._attribute_keys)
    print("impls color en var1 (esperado []):", [i.attribute.key for i in var1.attribute_implementations if i.attribute.key == "color"])
    print("impls color en var2 (esperado []):", [i.attribute.key for i in var2.attribute_implementations if i.attribute.key == "color"])

test5()