"""
example.py — Ejemplo completo de uso de models.py + crud.py

Muestra el flujo completo desde cero:
    1. Crear tablas
    2. Crear categoría y atributos
    3. Crear producto con opciones
    4. Generar variantes automáticamente
    5. Cargar atributos descriptivos al producto
    6. Buscar una variante por combinación de opciones
    7. Actualizar stock
    8. Filtrar productos por atributos

Para correr:
    python example.py

Requiere Postgres corriendo con las variables de crud.py configuradas.
"""

from models import (
    ProductAttributeValue,
    VariantGenerator,
    ProductOption,
    ProductOptionValue,
)
from crud import Database


def main():
    db = Database()

    # ────────────────────────────────────────
    # Setup — crear tablas si no existen
    # ────────────────────────────────────────
    print("→ Creando tablas...")
    db.create_tables()


    # ────────────────────────────────────────
    # 1. Categoría
    # ────────────────────────────────────────
    print("\n→ Creando categoría...")
    cat_id = db.categories.create("Zapatillas")

    # El repo devuelve un objeto Category del modelo
    cat = db.categories.get(cat_id)
    print(f"  {cat}")


    # ────────────────────────────────────────
    # 2. Atributos descriptivos
    # Definimos qué atributos existen en el sistema
    # ────────────────────────────────────────
    print("\n→ Creando atributos...")
    peso_id     = db.attributes.create(key="peso_g",      name="Peso (g)",    data_type="number")
    material_id = db.attributes.create(key="material",    name="Material",    data_type="text")
    wp_id       = db.attributes.create(key="waterproof",  name="Impermeable", data_type="boolean")
    pais_id     = db.attributes.create(key="pais_origen", name="País",        data_type="enum")

    for attr in db.attributes.list():
        print(f"  {attr}")


    # ────────────────────────────────────────
    # 3. Valores permitidos para el enum pais_origen
    # ────────────────────────────────────────
    print("\n→ Cargando valores enum para pais_origen...")
    arg_id = db.attribute_enum_values.create(pais_id, "Argentina", sort_order=0)
    bra_id = db.attribute_enum_values.create(pais_id, "Brasil",    sort_order=1)
    chn_id = db.attribute_enum_values.create(pais_id, "China",     sort_order=2)

    for ev in db.attribute_enum_values.list(pais_id):
        print(f"  {ev}")


    # ────────────────────────────────────────
    # 4. Configurar qué atributos aplican a la categoría
    #    y cómo se comportan en filtros
    # ────────────────────────────────────────
    print("\n→ Configurando atributos de la categoría Zapatillas...")

    db.category_attributes.set(
        category_id=cat_id, attribute_id=peso_id,
        is_filterable=True, is_required=False,
        filter_type="range", ui_control="slider",
    )
    db.category_attributes.set(
        category_id=cat_id, attribute_id=material_id,
        is_filterable=False, is_required=True,
    )
    db.category_attributes.set(
        category_id=cat_id, attribute_id=wp_id,
        is_filterable=True, is_required=False,
        filter_type="toggle", ui_control="toggle",
    )
    db.category_attributes.set(
        category_id=cat_id, attribute_id=pais_id,
        is_filterable=True, is_required=True,
        filter_type="enum_multi", ui_control="chips",
    )

    filtrables = db.category_attributes.list_filterable(cat_id)
    print(f"  Atributos filtrables: {[f['key'] for f in filtrables]}")


    # ────────────────────────────────────────
    # 5. Producto
    # ────────────────────────────────────────
    print("\n→ Creando producto...")
    prod_id = db.products.create(
        category_id=cat_id,
        title="Air Max 90",
        brand="Nike",
        description="Clásico desde 1990",
    )

    prod = db.products.get(prod_id)
    print(f"  {prod}")


    # ────────────────────────────────────────
    # 6. Opciones del producto
    # Cada opción es una dimensión que genera variantes
    # ────────────────────────────────────────
    print("\n→ Creando opciones del producto...")
    color_opt_id = db.product_options.create(prod_id, "Color", position=0)
    talla_opt_id = db.product_options.create(prod_id, "Talla", position=1)

    # Valores de cada opción
    neg_id = db.product_option_values.create(color_opt_id, "Negro",  sort_order=0)
    bla_id = db.product_option_values.create(color_opt_id, "Blanco", sort_order=1)
    t42_id = db.product_option_values.create(talla_opt_id, "42",     sort_order=0)
    t43_id = db.product_option_values.create(talla_opt_id, "43",     sort_order=1)
    t44_id = db.product_option_values.create(talla_opt_id, "44",     sort_order=2)

    for opt in db.product_options.list(prod_id):
        values = db.product_option_values.list(opt.id)
        print(f"  {opt} → {[v.value for v in values]}")


    # ────────────────────────────────────────
    # 7. Generar variantes automáticamente
    # El crud hace el producto cartesiano y crea todos los registros
    # 2 colores × 3 tallas = 6 variantes
    # ────────────────────────────────────────
    print("\n→ Generando variantes (2 colores × 3 tallas)...")
    variants = db.variants.generate(
        product_id=prod_id,
        base_price_cents=15000,
        sku_prefix="AM90",
    )

    for v in variants:
        combo = db.variant_option_values.list(v.id)
        combo_str = " / ".join(f"{c['option_name']}:{c['value']}" for c in combo)
        print(f"  {v.sku:20}  {combo_str}  →  ${v.price:.2f}")


    # ────────────────────────────────────────
    # 8. Atributos descriptivos del producto
    # Construimos objetos del modelo y los pasamos al repo
    # ────────────────────────────────────────
    print("\n→ Cargando atributos descriptivos del producto...")

    pavs = [
        ProductAttributeValue(
            product_id=prod_id, attribute_id=peso_id,
            value=310.0,
        ),
        ProductAttributeValue(
            product_id=prod_id, attribute_id=material_id,
            value="Cuero sintético",
        ),
        ProductAttributeValue(
            product_id=prod_id, attribute_id=wp_id,
            value=False,
        ),
        ProductAttributeValue(
            product_id=prod_id, attribute_id=pais_id,
            value="Argentina",
            enum_value_id=arg_id,   # FK al enum — requerido para tipo enum
        ),
    ]

    for pav in pavs:
        db.product_attributes.set(pav)  # upsert — crea o actualiza
        print(f"  guardado → {pav}  (jsonb: {pav.to_jsonb()})")


    # ────────────────────────────────────────
    # 9. Leer atributos del producto desde la DB
    # El repo reconstruye los objetos del modelo desde el jsonb
    # ────────────────────────────────────────
    print("\n→ Leyendo atributos desde DB...")
    atributos = db.product_attributes.list(prod_id)
    for a in atributos:
        print(f"  {a}")


    # ────────────────────────────────────────
    # 10. Buscar variante por combinación de opciones
    # Simula lo que pasa cuando el usuario elige Color y Talla en la tienda
    # ────────────────────────────────────────
    print("\n→ Buscando variante Negro + Talla 43...")
    variante = db.variants.find_by_options(prod_id, [neg_id, t43_id])
    if variante:
        combo = db.variant_option_values.list(variante.id)
        combo_str = " / ".join(f"{c['option_name']}:{c['value']}" for c in combo)
        print(f"  Encontrada: {variante.sku}  ({combo_str})")
    else:
        print("  No encontrada")


    # ────────────────────────────────────────
    # 11. Actualizar stock
    # delta positivo = entrada, delta negativo = venta
    # ────────────────────────────────────────
    print("\n→ Actualizando stock...")
    stock_nuevo = db.variants.update_stock(variante.id, delta=+10)
    print(f"  Stock tras entrada de 10:  {stock_nuevo}")

    stock_nuevo = db.variants.update_stock(variante.id, delta=-3)
    print(f"  Stock tras venta de 3:     {stock_nuevo}")


    # ────────────────────────────────────────
    # 12. Filtrar productos por atributos descriptivos
    # Simula los filtros del catálogo de la tienda
    # ────────────────────────────────────────
    print("\n→ Filtrando productos de Zapatillas...")

    # Producto 2 para que el filtro tenga más para comparar
    prod2_id = db.products.create(
        category_id=cat_id,
        title="Ultra Boost",
        brand="Adidas",
    )
    db.product_attributes.set(ProductAttributeValue(prod2_id, peso_id,     value=280.0))
    db.product_attributes.set(ProductAttributeValue(prod2_id, material_id, value="Mesh"))
    db.product_attributes.set(ProductAttributeValue(prod2_id, wp_id,       value=True))
    db.product_attributes.set(ProductAttributeValue(prod2_id, pais_id,     value="China", enum_value_id=chn_id))

    # Filtro 1: impermeables
    resultado = db.product_attributes.filter_products(
        category_id=cat_id,
        filters={"waterproof": True},
    )
    print(f"  Impermeables:               {[p.title for p in resultado]}")

    # Filtro 2: peso menor a 300g
    resultado = db.product_attributes.filter_products(
        category_id=cat_id,
        filters={"peso_g": {"max": 300}},
    )
    print(f"  Peso < 300g:                {[p.title for p in resultado]}")

    # Filtro 3: país = Argentina
    resultado = db.product_attributes.filter_products(
        category_id=cat_id,
        filters={"pais_origen": "Argentina"},
    )
    print(f"  País Argentina:             {[p.title for p in resultado]}")

    # Filtro 4: combinado — no impermeables y peso entre 200 y 350g
    resultado = db.product_attributes.filter_products(
        category_id=cat_id,
        filters={
            "waterproof": False,
            "peso_g": {"min": 200, "max": 350},
        },
    )
    print(f"  No waterproof + 200-350g:   {[p.title for p in resultado]}")


    # ────────────────────────────────────────
    # 13. Listar todos los productos de la categoría
    # ────────────────────────────────────────
    print("\n→ Todos los productos de Zapatillas:")
    todos = db.products.list(category_id=cat_id)
    for p in todos:
        print(f"  {p}")

    input("\nPresiona Enter para limpiar tablas y salir...")

    # ────────────────────────────────────────
    # Cleanup — opcional, comenta si querés ver los datos en la DB
    # ────────────────────────────────────────
    print("\n→ Limpiando tablas...")
    db.drop_tables()
    print("  Listo.")

    db.close()


if __name__ == "__main__":
    main()
