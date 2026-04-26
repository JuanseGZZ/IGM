import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from app.models import Attribute, AttributeImplementation, Category, Product

# ─── Atributos ────────────────────────────────────────────────────────────────
ram      = Attribute(key="ram",            name="RAM",            data_type="number", id=1, is_static=True)
pantalla = Attribute(key="pantalla",       name="Pantalla",       data_type="number", id=2, is_static=True)
peso     = Attribute(key="peso",           name="Peso",           data_type="number", id=3, is_static=True)
garantia = Attribute(key="garantia",       name="Garantia",       data_type="number", id=4, is_static=True)
color    = Attribute(key="color",          name="Color",          data_type="enum",   id=5, is_static=False)
almac    = Attribute(key="almacenamiento", name="Almacenamiento", data_type="enum",   id=6, is_static=False)

# ─── Categorias hoja ──────────────────────────────────────────────────────────
# Laptops ya tiene [garantia] → cuando Computadoras agregue garantia, esta rama lo absorbe
cat_laptops     = Category(name="Laptops",     id=3, attributes=[ram, pantalla, garantia])
cat_desktops    = Category(name="Desktops",    id=4, attributes=[ram, peso])
cat_smartphones = Category(name="Smartphones", id=5, attributes=[pantalla, color])
cat_basicos     = Category(name="Basicos",     id=6, attributes=[peso])

# ─── Productos ────────────────────────────────────────────────────────────────
p_macbook  = Product(code="MBA001", title="MacBook Air", price=1299, description="", brand="Apple",    category=cat_laptops)
p_thinkpad = Product(code="TP001",  title="ThinkPad X1", price=999,  description="", brand="Lenovo",   category=cat_laptops)
p_imac     = Product(code="IMA001", title="iMac",        price=1499, description="", brand="Apple",    category=cat_desktops)
p_dell     = Product(code="DEL001", title="Dell XPS",    price=1199, description="", brand="Dell",     category=cat_desktops)
p_iphone   = Product(code="IPH001", title="iPhone 15",   price=999,  description="", brand="Apple",    category=cat_smartphones)
p_samsung  = Product(code="SAM001", title="Galaxy S24",  price=799,  description="", brand="Samsung",  category=cat_smartphones)
p_nokia    = Product(code="NOK001", title="Nokia 3310",  price=49,   description="", brand="Nokia",    category=cat_basicos)
p_moto     = Product(code="MOT001", title="Moto E6",     price=89,   description="", brand="Motorola", category=cat_basicos)

cat_laptops.products     = [p_macbook, p_thinkpad]
cat_desktops.products    = [p_imac, p_dell]
cat_smartphones.products = [p_iphone, p_samsung]
cat_basicos.products     = [p_nokia, p_moto]

# ─── Categorias rama ──────────────────────────────────────────────────────────
cat_computadoras = Category(name="Computadoras", id=2, attributes=[],      subcategories=[cat_laptops, cat_desktops])
cat_celulares    = Category(name="Celulares",    id=7, attributes=[almac],  subcategories=[cat_smartphones, cat_basicos])
cat_root         = Category(name="Electronica",  id=1, attributes=[],       subcategories=[cat_computadoras, cat_celulares])

cat_laptops.father_categorie     = cat_computadoras
cat_desktops.father_categorie    = cat_computadoras
cat_smartphones.father_categorie = cat_celulares
cat_basicos.father_categorie     = cat_celulares
cat_computadoras.father_categorie = cat_root
cat_celulares.father_categorie    = cat_root


# ─── Construccion del grafo ───────────────────────────────────────────────────
def _build_graph(root_cat):
    G = nx.DiGraph()
    meta = {}

    def visit(cat, parent_id=None):
        nid = f"cat_{cat.id}"
        attr_str = "  ".join(f"[{a.key}]" for a in cat.attributes)
        label = f"{cat.name}\n{attr_str}" if attr_str else cat.name
        G.add_node(nid)
        meta[nid] = {"type": "category", "label": label, "ref": cat}
        if parent_id:
            G.add_edge(parent_id, nid)
        for sub in cat.subcategories:
            visit(sub, nid)
        for prod in cat.products:
            pid = f"prod_{prod.code}"
            G.add_node(pid)
            meta[pid] = {"type": "product", "label": prod.title, "ref": prod}
            G.add_edge(nid, pid)

    visit(root_cat)
    return G, meta


def _hierarchy_pos(G, root, width=1.0, gap=1.0, x=0.0, y=0.0, pos=None):
    if pos is None:
        pos = {}
    pos[root] = (x, y)
    children = list(G.successors(root))
    if children:
        dx = width / len(children)
        start = x - width / 2 + dx / 2
        for i, child in enumerate(children):
            _hierarchy_pos(G, child, width=dx, gap=gap, x=start + i * dx, y=y - gap, pos=pos)
    return pos


# ─── Dibujo ───────────────────────────────────────────────────────────────────
def draw_tree(ax, G, meta, root_id, impacted_codes=None, title=""):
    pos = _hierarchy_pos(G, root_id, width=10.0, gap=1.8)
    impacted_codes = impacted_codes or set()

    cat_nodes    = [n for n, m in meta.items() if m["type"] == "category"]
    prod_normal  = [n for n, m in meta.items() if m["type"] == "product" and m["ref"].code not in impacted_codes]
    prod_impact  = [n for n, m in meta.items() if m["type"] == "product" and m["ref"].code in impacted_codes]

    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=12,
                           edge_color="#999999", width=1.5)
    nx.draw_networkx_nodes(G, pos, nodelist=cat_nodes,   ax=ax,
                           node_color="#3A7EC6", node_size=2400, node_shape="s")
    nx.draw_networkx_nodes(G, pos, nodelist=prod_normal, ax=ax,
                           node_color="#4CAF78", node_size=1800, node_shape="o")
    nx.draw_networkx_nodes(G, pos, nodelist=prod_impact, ax=ax,
                           node_color="#E05C3A", node_size=2000, node_shape="o")

    labels = {n: m["label"] for n, m in meta.items()}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=7, font_color="white", font_weight="bold")

    legend = [
        mpatches.Patch(color="#3A7EC6", label="Categoria"),
        mpatches.Patch(color="#4CAF78", label="Producto"),
    ]
    if prod_impact:
        legend.append(mpatches.Patch(color="#E05C3A", label="Producto impactado"))
    ax.legend(handles=legend, loc="upper right", fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.axis("off")


# ─── Test ─────────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
fig.suptitle("compute_impact — agregar 'garantia' a Computadoras", fontsize=14, fontweight="bold")

G1, meta1 = _build_graph(cat_root)
draw_tree(ax1, G1, meta1, "cat_1", title="Estado inicial")

print("=" * 60)
print("EVENTO: Computadoras agrega atributo [garantia]")
print("  Laptops    ya tiene [garantia] → absorbe, no propaga")
print("  Desktops   no tiene [garantia] → propaga a sus productos")
print("=" * 60)

cat_computadoras.attributes.append(garantia)
impact_result = cat_computadoras.compute_impact({garantia})

impacted_codes = set()
print("\nResultados compute_impact:")
for attrs, products in impact_result:
    attr_names = ", ".join(a.name for a in attrs)
    prod_names = ", ".join(p.title for p in products)
    print(f"  [{attr_names}]  →  {prod_names}")
    for p in products:
        impacted_codes.add(p.code)

print(f"\nProductos impactados ({len(impacted_codes)}): {', '.join(meta1[f'prod_{c}']['label'] for c in impacted_codes)}")
print(f"Productos NO impactados: {', '.join(m['label'] for n, m in meta1.items() if m['type'] == 'product' and m['ref'].code not in impacted_codes)}")

G2, meta2 = _build_graph(cat_root)
draw_tree(ax2, G2, meta2, "cat_1", impacted_codes=impacted_codes,
          title="Despues de agregar [garantia] a Computadoras\n(rojo = impactado)")

plt.tight_layout()
plt.show()


# ─── Test get_ancestor_attrs / get_effective_inherited_attrs ──────────────────
print("\n" + "=" * 60)
print("TEST: get_ancestor_attrs y get_effective_inherited_attrs")
print("=" * 60)

# Arbol al momento de este test:
#   Electronica (sin attrs)
#   └── Computadoras [garantia]          ← le agregamos garantia arriba
#       ├── Laptops [ram, pantalla, garantia]
#       └── Desktops [ram, peso]

casos = [
    (cat_root,         "Electronica  (raiz, sin padre)"),
    (cat_computadoras, "Computadoras (padre: Electronica)"),
    (cat_laptops,      "Laptops      (padre: Computadoras, abuelo: Electronica)"),
    (cat_desktops,     "Desktops     (padre: Computadoras, abuelo: Electronica)"),
    (cat_celulares,    "Celulares    (padre: Electronica)"),
    (cat_smartphones,  "Smartphones  (padre: Celulares, abuelo: Electronica)"),
]

for cat, label in casos:
    ancestor  = {a.key for a in cat.get_ancestor_attrs()}
    effective = {a.key for a in cat.get_effective_inherited_attrs()}
    own       = {a.key for a in cat.attributes}
    print(f"\n  {label}")
    print(f"    propios   : {sorted(own)       or '—'}")
    print(f"    ancestros : {sorted(ancestor)  or '—'}")
    print(f"    efectivos : {sorted(effective) or '—'}   (ancestros que self no pisa)")


# ─── Test validadores ─────────────────────────────────────────────────────────
def _assert_raises(fn, msg_fragment, label):
    try:
        fn()
        print(f"  FALLO  {label} — deberia haber lanzado error")
    except ValueError as e:
        if msg_fragment.lower() in str(e).lower():
            print(f"  OK     {label}")
        else:
            print(f"  FALLO  {label} — error inesperado: {e}")

def _assert_ok(fn, label):
    try:
        fn()
        print(f"  OK     {label}")
    except Exception as e:
        print(f"  FALLO  {label} — no deberia lanzar error: {e}")

print("\n" + "=" * 60)
print("TEST: validadores")
print("=" * 60)

print("\n-- hijos exclusivos --")

cat_nueva = Category(name="NuevaHoja", id=99)
cat_nueva.products = [p_macbook]          # tiene productos
_assert_raises(
    lambda: cat_nueva.add_subcategory(cat_basicos),
    "ya tiene productos",
    "add_subcategory en categoria con productos → error"
)

cat_vacia = Category(name="VaciaConSubs", id=100)
cat_vacia.subcategories = [cat_basicos]   # tiene subcategorias
_assert_raises(
    lambda: cat_vacia.add_product(p_dell),
    "ya tiene subcategorias",
    "add_product en categoria con subcategorias → error"
)

cat_limpia = Category(name="Limpia", id=101)
_assert_ok(
    lambda: cat_limpia.add_subcategory(Category(name="SubLimpia", id=102)),
    "add_subcategory en categoria vacia → ok"
)
cat_limpia2 = Category(name="Limpia2", id=103)
_assert_ok(
    lambda: cat_limpia2.add_product(p_nokia),
    "add_product en categoria vacia → ok"
)

print("\n-- ciclos --")

# A → B → C, intentar que C agregue a A como subcategoria (ciclo directo)
cat_a = Category(name="A", id=200)
cat_b = Category(name="B", id=201)
cat_c = Category(name="C", id=202)
cat_a.add_subcategory(cat_b)
cat_b.add_subcategory(cat_c)

_assert_raises(
    lambda: cat_c.add_subcategory(cat_a),
    "ciclo",
    "C intenta agregar A como hijo (A es ancestro de C) → error"
)
_assert_raises(
    lambda: cat_c.add_subcategory(cat_b),
    "ciclo",
    "C intenta agregar B como hijo (B es ancestro de C) → error"
)
_assert_raises(
    lambda: cat_a.add_subcategory(cat_a),
    "ciclo",
    "A intenta agregarse a si mismo → error"
)
_assert_ok(
    lambda: cat_a.add_subcategory(Category(name="D", id=203)),
    "A agrega D (sin ciclo) → ok"
)


# ─── Test eventos de padre (E1 / E2 / E3) ────────────────────────────────────
#
# Arbol de prueba:
#
#   nueva_raiz  [almacenamiento, pantalla]
#   └── Computadoras [garantia]            ← le agregaremos nueva_raiz como padre
#       ├── Laptops  [ram, pantalla, garantia]   pantalla absorbida aqui
#       │   ├── MacBook Air
#       │   └── ThinkPad X1
#       └── Desktops [ram, peso]                 ninguno absorbido
#           ├── iMac
#           └── Dell XPS
#
# E1 esperado: Laptops absorbe pantalla → MacBook/ThinkPad reciben solo [almacenamiento]
#              Desktops no absorbe nada → iMac/Dell reciben [almacenamiento, pantalla]
#
print("\n" + "=" * 60)
print("TEST: eventos de padre (E1 / E2 / E3)")
print("=" * 60)

def _fmt(impact):
    lines = []
    for attrs, prods in impact:
        a = sorted(a.key for a in attrs)
        p = sorted(pr.title for pr in prods)
        lines.append(f"    attrs={a}  →  productos={p}")
    return "\n".join(lines) if lines else "    (sin impacto)"

nueva_raiz = Category(name="NuevaRaiz", id=300, attributes=[almac, pantalla])

print("\n-- E1: Computadoras agrega padre NuevaRaiz [almacenamiento, pantalla] --")
impacto_e1 = cat_computadoras.impact_on_add_father(nueva_raiz)
print(_fmt(impacto_e1))

# Aplicamos el cambio y verificamos coherencia
cat_computadoras.set_father(nueva_raiz)
nueva_raiz.subcategories.append(cat_computadoras)

print("\n-- E3: Computadoras elimina padre (NuevaRaiz) --")
impacto_e3 = cat_computadoras.impact_on_remove_father()
print(_fmt(impacto_e3))
# (no mutamos, solo mostramos que el impacto de salida es el mismo conjunto)

print("\n-- E2: Computadoras cambia de NuevaRaiz a OtroRaiz [peso] --")
otro_raiz = Category(name="OtroRaiz", id=301, attributes=[peso])
salida, entrada = cat_computadoras.impact_on_change_father(otro_raiz)
print("  impacto SALIDA (lo que se pierde):")
print(_fmt(salida))
print("  impacto ENTRADA (lo que se gana):")
print(_fmt(entrada))


# ─── Test E4 / E5 ─────────────────────────────────────────────────────────────
#
# Arbol de prueba:
#
#   Herramientas  [garantia, peso]
#   ├── Electricas  [garantia]        ← garantia absorbida aqui
#   │   ├── Taladro
#   │   └── Sierra
#   └── Manuales  []                  ← garantia no absorbida
#       ├── Martillo
#       └── Destornillador
#
# E4: Herramientas agrega [stock]
#   → llega a todos (ninguna rama lo absorbe)
#
# E5: Herramientas elimina [garantia]
#   → Electricas lo absorbe → Taladro/Sierra no se ven afectados
#   → Manuales no lo absorbe → Martillo/Destornillador lo pierden
#
print("\n" + "=" * 60)
print("TEST: E4 (agrega atributo) y E5 (elimina atributo)")
print("=" * 60)

stock    = Attribute(key="stock",    name="Stock",    data_type="number", id=7, is_static=True)

cat_herram    = Category(name="Herramientas", id=400, attributes=[garantia, peso])
cat_electr    = Category(name="Electricas",   id=401, attributes=[garantia])
cat_manual    = Category(name="Manuales",     id=402, attributes=[])

p_taladro = Product(code="TAL01", title="Taladro",          price=120, description="", brand="Bosch",   category=cat_electr)
p_sierra  = Product(code="SIE01", title="Sierra",           price=95,  description="", brand="DeWalt",  category=cat_electr)
p_martil  = Product(code="MAR01", title="Martillo",         price=15,  description="", brand="Stanley", category=cat_manual)
p_destorn = Product(code="DES01", title="Destornillador",   price=10,  description="", brand="Stanley", category=cat_manual)

cat_electr.products = [p_taladro, p_sierra]
cat_manual.products = [p_martil, p_destorn]
cat_herram.add_subcategory(cat_electr)
cat_herram.add_subcategory(cat_manual)

print("\n-- E4: Herramientas agrega [stock] --")
print("   (ninguna rama tiene stock → llega a todos)")
impacto_e4 = cat_herram.impact_on_add_attribute(stock)
print(_fmt(impacto_e4))

print("\n-- E5: Herramientas elimina [garantia] --")
print("   (Electricas ya la define → la absorbe, sus productos no se ven afectados)")
print("   (Manuales no la tiene → sus productos la pierden)")
impacto_e5 = cat_herram.impact_on_remove_attribute(garantia)
print(_fmt(impacto_e5))


# ─── Test E6: producto cambia de categoria ────────────────────────────────────
#
# Arbol de prueba:
#
#   Raiz [pantalla]
#   ├── CatOrigen  [ram, peso]          producto vive aqui
#   │   └── Notebook  impls: [ram*, peso*, pantalla*]   (* = is_static)
#   └── CatDestino [garantia, peso]     producto se mueve aqui
#
# La nueva herencia completa de CatDestino = [pantalla] + [garantia, peso]
#                                           = [pantalla, garantia, peso]  (todos static)
# Implementaciones actuales del producto   = [ram, peso, pantalla]
#
# to_add    = {pantalla, garantia, peso} - {ram, peso, pantalla} = {garantia}
# to_remove = {ram, peso, pantalla}      - {pantalla, garantia, peso} = {ram}
#
print("\n" + "=" * 60)
print("TEST: E6 — producto cambia de categoria")
print("=" * 60)

cat_raiz_e6   = Category(name="RaizE6",     id=500, attributes=[pantalla])
cat_origen    = Category(name="CatOrigen",  id=501, attributes=[ram, peso])
cat_destino   = Category(name="CatDestino", id=502, attributes=[garantia, peso])
cat_raiz_e6.add_subcategory(cat_origen)
cat_raiz_e6.add_subcategory(cat_destino)

impl_ram      = AttributeImplementation(attribute=ram,      value="16")
impl_peso_nb  = AttributeImplementation(attribute=peso,     value="1.5")
impl_pantalla = AttributeImplementation(attribute=pantalla, value="15.6")

p_notebook = Product(
    code="NB001", title="Notebook Pro", price=1500, description="", brand="Lenovo",
    category=cat_origen,
    attributes_implementations=[impl_ram, impl_peso_nb, impl_pantalla]
)

print(f"\n  Producto: {p_notebook.title}")
print(f"  Categoria origen : {cat_origen.name}  full_attrs={sorted(a.key for a in cat_origen.get_full_attr_set())}")
print(f"  Categoria destino: {cat_destino.name}  full_attrs={sorted(a.key for a in cat_destino.get_full_attr_set())}")
print(f"  Implementaciones actuales: {sorted(i.attribute.key for i in p_notebook.attributes_implementations)}")

to_add, to_remove = p_notebook.impact_on_change_category(cat_destino)
print(f"\n  to_add    (implementar): {sorted(a.key for a in to_add)}")
print(f"  to_remove (quitar)     : {sorted(a.key for a in to_remove)}")


# ─── Test E7: producto agrega / quita variantes ───────────────────────────────
#
# Arbol:
#   CatRopa [talle(enum,dynamic), color(enum,dynamic), marca(text,static)]
#   └── Remera  (producto, sin impls aun)
#
# Attrs dinamicos requeridos por variante: [talle, color]
# Casos:
#   - variante {talle=M,    color=rojo}  → OK
#   - variante {talle=M,    color=rojo}  → Error: duplicada
#   - variante {talle=L}                 → Error: falta color
#   - variante {talle=S,    color=azul, almacenamiento=128} → Error: attr de mas
#   - variante {talle=XL,   color=verde} → OK (segunda valida)
#   - quitar la primera variante         → OK
#   - quitar algo que no esta            → Error
#
print("\n" + "=" * 60)
print("TEST: E7 — agregar y quitar variantes")
print("=" * 60)

from app.models import Variant

talle  = Attribute(key="talle",  name="Talle",  data_type="enum", id=8,  is_static=False)
marca  = Attribute(key="marca",  name="Marca",  data_type="text", id=9,  is_static=True)

cat_ropa = Category(name="CatRopa", id=600, attributes=[talle, color, marca])
p_remera = Product(code="REM01", title="Remera", price=25, description="", brand="Nike", category=cat_ropa)

print(f"\n  Attrs dinamicos requeridos: {sorted(a.key for a in p_remera.get_required_dynamic_attrs())}")

def _make_variant(*pairs):
    impls = [AttributeImplementation(attribute=attr, value=val) for attr, val in pairs]
    return Variant(attribute_implementations=impls)

color.add_enum_value("rojo")
color.add_enum_value("azul")
color.add_enum_value("verde")
talle.add_enum_value("S")
talle.add_enum_value("M")
talle.add_enum_value("L")
talle.add_enum_value("XL")

v1 = _make_variant((talle, "M"),  (color, "rojo"))
v2 = _make_variant((talle, "M"),  (color, "rojo"))   # duplicada de v1
v3 = _make_variant((talle, "L"))                      # le falta color
v4 = _make_variant((talle, "S"),  (color, "azul"), (almac, "128GB"))  # attr de mas
v5 = _make_variant((talle, "XL"), (color, "verde"))

_assert_ok(    lambda: p_remera.add_variant(v1), "add v1 {talle=M, color=rojo} → ok")
_assert_raises(lambda: p_remera.add_variant(v2), "ya existe", "add v2 duplicada → error")
_assert_raises(lambda: p_remera.add_variant(v3), "faltan",    "add v3 sin color → error")
_assert_raises(lambda: p_remera.add_variant(v4), "de mas",    "add v4 con attr extra → error")
_assert_ok(    lambda: p_remera.add_variant(v5), "add v5 {talle=XL, color=verde} → ok")

print(f"\n  Variantes actuales ({len(p_remera.variants)}):")
for v in p_remera.variants:
    sig = sorted(f"{i.attribute.key}={i.value}" for i in v.attribute_implementations)
    print(f"    {sig}")

_assert_ok(    lambda: p_remera.remove_variant(v1),  "remove v1 → ok")
_assert_raises(lambda: p_remera.remove_variant(v1),  "no pertenece", "remove v1 de nuevo → error")

print(f"\n  Variantes tras quitar v1 ({len(p_remera.variants)}):")
for v in p_remera.variants:
    sig = sorted(f"{i.attribute.key}={i.value}" for i in v.attribute_implementations)
    print(f"    {sig}")
