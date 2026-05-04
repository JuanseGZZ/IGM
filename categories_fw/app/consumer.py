"""
tree_explorer.py
Visor interactivo del árbol de Categorías / Productos / Variantes definido en models.py
Usa Textual para la TUI y Rich para el render del árbol.
"""
from __future__ import annotations
import sys
import traceback
from typing import Optional

from app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Tree, Log, Input, Label, Button, Select
)
from textual.widget import Widget
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import on
from rich.text import Text

from models import (
    Attribute, AttributeImplementation, Category, Product, Variant, DataTypes
)

# ── Datos de demostración ──────────────────────────────────────────────────────

def build_demo() -> tuple[list[Category], list[Attribute]]:
    # Atributos
    color  = Attribute(key="color",  name="Color",     data_type="enum")
    color.add_enum_value("Rojo"); color.add_enum_value("Azul"); color.add_enum_value("Verde")
    size   = Attribute(key="size",   name="Talla",     data_type="enum")
    size.add_enum_value("S"); size.add_enum_value("M"); size.add_enum_value("L")
    brand_attr = Attribute(key="brand_info", name="Marca Info", data_type="text", is_static=True)
    weight = Attribute(key="weight", name="Peso (kg)",  data_type="number", is_static=True)

    # Árbol de categorías
    root = Category(name="Tienda", id=1)

    ropa = Category(name="Ropa", id=2, attributes=[color, size])
    electro = Category(name="Electrónica", id=3, attributes=[weight])

    remeras = Category(name="Remeras", id=4)
    pantalones = Category(name="Pantalones", id=5)

    root.add_subcategory(ropa)
    root.add_subcategory(electro)
    ropa.add_subcategory(remeras)
    ropa.add_subcategory(pantalones)

    # Productos
    p1 = Product(code="R001", title="Remera Clásica", price=29.99,
                 description="Algodón 100%", brand="BasicBrand", category=remeras)
    p1.attributes_implementations.append(AttributeImplementation(brand_attr, "BasicBrand"))

    v1 = Variant(attribute_implementations=[
        AttributeImplementation(color, "Rojo"),
        AttributeImplementation(size, "M"),
    ])
    v2 = Variant(attribute_implementations=[
        AttributeImplementation(color, "Azul"),
        AttributeImplementation(size, "L"),
    ])
    p1.variants.append(v1)
    p1.variants.append(v2)
    remeras.add_product(p1)

    p2 = Product(code="P001", title="Jean Slim", price=59.99,
                 description="Denim", brand="DenimCo", category=pantalones)
    pantalones.add_product(p2)

    all_attrs = [color, size, brand_attr, weight]
    all_cats  = [root, ropa, electro, remeras, pantalones]
    return all_cats, all_attrs

ALL_CATS: list[Category] = []
ALL_ATTRS: list[Attribute] = []
ROOT_CAT: Category | None = None

# ── Helpers ────────────────────────────────────────────────────────────────────

def find_cat(name: str) -> Category | None:
    for c in ALL_CATS:
        if c.name.lower() == name.lower():
            return c
    return None

def find_attr(key: str) -> Attribute | None:
    for a in ALL_ATTRS:
        if a.key.lower() == key.lower():
            return a
    return None

def find_product(code: str) -> tuple[Product | None, Category | None]:
    for cat in ALL_CATS:
        for p in cat.products:
            if p.code.lower() == code.lower():
                return p, cat
    return None, None

def all_products() -> list[Product]:
    result = []
    for cat in ALL_CATS:
        result.extend(cat.products)
    return result

# ── Acciones ───────────────────────────────────────────────────────────────────

def do_action(cmd: str, args: list[str]) -> str:
    """Ejecuta una acción y retorna mensaje de resultado (o lanza excepción)."""
    cmd = cmd.lower().strip()

    # ── Categorías ──
    if cmd == "crear_cat":
        # crear_cat <nombre> [padre]
        name = args[0] if args else ""
        if not name:
            raise ValueError("Uso: crear_cat <nombre> [padre]")
        padre_name = args[1] if len(args) > 1 else None
        nueva = Category(name=name, id=len(ALL_CATS) + 100)
        if padre_name:
            padre = find_cat(padre_name)
            if not padre:
                raise ValueError(f"Padre '{padre_name}' no encontrado.")
            padre.add_subcategory(nueva)
        else:
            # Sin padre: lo agregamos como hijo de root
            ROOT_CAT.add_subcategory(nueva)
        ALL_CATS.append(nueva)
        return f"✅ Categoría '{name}' creada."

    elif cmd == "eliminar_cat":
        # eliminar_cat <nombre>
        name = args[0] if args else ""
        cat = find_cat(name)
        if not cat:
            raise ValueError(f"Categoría '{name}' no encontrada.")
        if cat is ROOT_CAT:
            raise ValueError("No se puede eliminar la raíz.")
        if cat.subcategories or cat.products:
            raise ValueError("La categoría tiene hijos o productos. Eliminá primero.")
        padre = cat.father_categorie
        if padre:
            padre.subcategories.remove(cat)
        ALL_CATS.remove(cat)
        return f"✅ Categoría '{name}' eliminada."

    elif cmd == "mover_cat":
        # mover_cat <nombre> <nuevo_padre>
        if len(args) < 2:
            raise ValueError("Uso: mover_cat <nombre> <nuevo_padre>")
        cat = find_cat(args[0])
        new_padre = find_cat(args[1])
        if not cat:
            raise ValueError(f"Categoría '{args[0]}' no encontrada.")
        if not new_padre:
            raise ValueError(f"Padre '{args[1]}' no encontrado.")
        # Impact info
        impact = cat.impact_on_change_father(new_padre)
        # Desvincular del padre anterior
        old_padre = cat.father_categorie
        if old_padre:
            old_padre.subcategories.remove(cat)
        new_padre.add_subcategory(cat)
        return f"✅ Categoría '{cat.name}' movida a '{new_padre.name}'.\nImpacto salida: {impact[0]}\nImpacto entrada: {impact[1]}"

    elif cmd == "editar_cat":
        # editar_cat <nombre> <nuevo_nombre>
        if len(args) < 2:
            raise ValueError("Uso: editar_cat <nombre> <nuevo_nombre>")
        cat = find_cat(args[0])
        if not cat:
            raise ValueError(f"Categoría '{args[0]}' no encontrada.")
        cat.name = args[1]
        return f"✅ Categoría renombrada a '{args[1]}'."

    # ── Atributos en categoría ──
    elif cmd == "agregar_attr":
        # agregar_attr <cat> <attr_key>
        if len(args) < 2:
            raise ValueError("Uso: agregar_attr <categoria> <attr_key>")
        cat = find_cat(args[0])
        attr = find_attr(args[1])
        if not cat:
            raise ValueError(f"Categoría '{args[0]}' no encontrada.")
        if not attr:
            raise ValueError(f"Atributo '{args[1]}' no encontrado. Attrs disponibles: {[a.key for a in ALL_ATTRS]}")
        if attr in cat.attributes:
            raise ValueError(f"La categoría ya tiene el atributo '{attr.key}'.")
        impact = cat.impact_on_add_attribute(attr)
        cat.attributes.append(attr)
        return f"✅ Atributo '{attr.key}' agregado a '{cat.name}'.\nImpacto: {impact}"

    elif cmd == "quitar_attr":
        # quitar_attr <cat> <attr_key>
        if len(args) < 2:
            raise ValueError("Uso: quitar_attr <categoria> <attr_key>")
        cat = find_cat(args[0])
        attr = find_attr(args[1])
        if not cat:
            raise ValueError(f"Categoría '{args[0]}' no encontrada.")
        if not attr:
            raise ValueError(f"Atributo '{args[1]}' no encontrado.")
        if attr not in cat.attributes:
            raise ValueError(f"La categoría no tiene el atributo '{attr.key}'.")
        impact = cat.impact_on_remove_attribute(attr)
        cat.attributes.remove(attr)
        return f"✅ Atributo '{attr.key}' quitado de '{cat.name}'.\nImpacto: {impact}"

    # ── Productos ──
    elif cmd == "crear_prod":
        # crear_prod <cat> <code> <titulo> <precio>
        if len(args) < 4:
            raise ValueError("Uso: crear_prod <categoria> <code> <titulo> <precio>")
        cat = find_cat(args[0])
        if not cat:
            raise ValueError(f"Categoría '{args[0]}' no encontrada.")
        prod = Product(
            code=args[1], title=args[2], price=float(args[3]),
            description="", brand="", category=cat
        )
        cat.add_product(prod)
        return f"✅ Producto '{args[2]}' ({args[1]}) creado en '{cat.name}'."

    elif cmd == "eliminar_prod":
        # eliminar_prod <code>
        code = args[0] if args else ""
        prod, cat = find_product(code)
        if not prod:
            raise ValueError(f"Producto '{code}' no encontrado.")
        cat.products.remove(prod)
        return f"✅ Producto '{prod.title}' eliminado."

    elif cmd == "editar_prod":
        # editar_prod <code> <campo> <valor>  campo: title|price|description|brand
        if len(args) < 3:
            raise ValueError("Uso: editar_prod <code> <campo> <valor>  (campo: title/price/description/brand)")
        prod, _ = find_product(args[0])
        if not prod:
            raise ValueError(f"Producto '{args[0]}' no encontrado.")
        campo, valor = args[1].lower(), args[2]
        if campo == "title":       prod.title = valor
        elif campo == "price":     prod.price = float(valor)
        elif campo == "description": prod.description = valor
        elif campo == "brand":     prod.brand = valor
        else:
            raise ValueError(f"Campo '{campo}' no reconocido. Usá: title, price, description, brand")
        return f"✅ Producto '{prod.code}' actualizado: {campo} = {valor}"

    elif cmd == "mover_prod":
        # mover_prod <code> <nueva_cat>
        if len(args) < 2:
            raise ValueError("Uso: mover_prod <code> <nueva_categoria>")
        prod, old_cat = find_product(args[0])
        new_cat = find_cat(args[1])
        if not prod:
            raise ValueError(f"Producto '{args[0]}' no encontrado.")
        if not new_cat:
            raise ValueError(f"Categoría '{args[1]}' no encontrada.")
        to_add, to_remove = prod.impact_on_change_category(new_cat)
        old_cat.products.remove(prod)
        prod.category = new_cat
        new_cat.add_product(prod)
        return (f"✅ Producto '{prod.title}' movido a '{new_cat.name}'.\n"
                f"Attrs a agregar: {[a.key for a in to_add]}\n"
                f"Attrs a quitar: {[a.key for a in to_remove]}")

    elif cmd == "ayuda":
        return HELP_TEXT

    else:
        raise ValueError(f"Comando '{cmd}' no reconocido. Escribí 'ayuda' para ver los comandos.")


HELP_TEXT = """\
COMANDOS DISPONIBLES
────────────────────────────────────────────────
Categorías:
  crear_cat <nombre> [padre]
  eliminar_cat <nombre>
  mover_cat <nombre> <nuevo_padre>
  editar_cat <nombre> <nuevo_nombre>

Atributos en categoría:
  agregar_attr <categoria> <attr_key>
  quitar_attr  <categoria> <attr_key>

Atributos disponibles (keys):
  color, size, brand_info, weight

Productos:
  crear_prod  <categoria> <code> <titulo> <precio>
  eliminar_prod <code>
  editar_prod <code> <campo> <valor>
              campo: title | price | description | brand
  mover_prod  <code> <nueva_categoria>

  ayuda       → este texto

EJEMPLOS:
  crear_cat Accesorios Ropa
  agregar_attr Remeras weight
  crear_prod Remeras R002 Musculosa 19.99
  mover_prod R001 Pantalones
  editar_cat Remeras Camisetas
"""

# ── Widgets ────────────────────────────────────────────────────────────────────

class TreePanel(Widget):
    DEFAULT_CSS = """
    TreePanel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Tree("🏪 Árbol", id="cat_tree")

    def rebuild(self) -> None:
        tree: Tree = self.query_one("#cat_tree", Tree)
        tree.clear()
        if ROOT_CAT:
            self._add_node(tree.root, ROOT_CAT)
        tree.root.expand_all()

    def _add_node(self, parent_node, cat: Category):
        attrs_str = ""
        if cat.attributes:
            attrs_str = " [dim]attrs:[/] " + ",".join(
                f"[yellow]{a.key}[/]{'[italic](S)[/]' if a.is_static else ''}"
                for a in cat.attributes
            )

        label = Text.from_markup(f"📁 [bold cyan]{cat.name}[/]{attrs_str}")
        node = parent_node.add(label)

        for prod in cat.products:
            var_count = len(prod.variants)
            plabel = Text.from_markup(
                f"📦 [green]{prod.title}[/] "
                f"[dim]({prod.code})[/] "
                f"[yellow]${prod.price:.2f}[/] "
                f"[dim]{var_count} var.[/]"
            )
            prod_node = node.add(plabel)
            for v in prod.variants:
                vals = ", ".join(
                    f"{ai.attribute.key}={ai.value}"
                    for ai in v.attribute_implementations
                )
                prod_node.add_leaf(Text.from_markup(f"  🔀 [dim]{vals}[/]"))

        for sub in cat.subcategories:
            self._add_node(node, sub)


class ActionBar(Widget):
    DEFAULT_CSS = """
    ActionBar {
        height: auto;
        border-top: solid $primary;
        padding: 1;
        background: $surface;
    }
    ActionBar Horizontal {
        height: auto;
    }
    ActionBar Input {
        width: 3fr;
    }
    ActionBar Button {
        width: auto;
        margin-left: 1;
    }
    ActionBar Label {
        padding: 0 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label("Comando: ")
            yield Input(placeholder="ej: crear_cat Zapatos Ropa", id="cmd_input")
            yield Button("Ejecutar ↵", id="btn_exec", variant="primary")
            yield Button("?  Ayuda", id="btn_help", variant="default")


class LogPanel(Widget):
    DEFAULT_CSS = """
    LogPanel {
        width: 1fr;
        height: 100%;
        border: solid $accent;
    }
    LogPanel Log {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Log(id="log", highlight=True, markup=True)

    def write(self, msg: str, error: bool = False) -> None:
        log: Log = self.query_one("#log", Log)
        prefix = "❌ " if error else "✅ "
        log.write_line(prefix + msg)


# ── App principal ──────────────────────────────────────────────────────────────

class TreeApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main_row {
        height: 1fr;
        layout: horizontal;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Salir"),
        ("ctrl+r", "refresh", "Refrescar árbol"),
        ("enter",  "execute", "Ejecutar"),
    ]

    TITLE = "Explorer de Categorías — models.py"

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main_row"):
            yield TreePanel(id="tree_panel")
            yield LogPanel(id="log_panel")
        yield ActionBar(id="action_bar")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(TreePanel).rebuild()
        log = self.query_one(LogPanel)
        log.write("App iniciada. Árbol de demo cargado.")
        log.write("Escribí 'ayuda' para ver todos los comandos.")
        # focus input
        self.query_one("#cmd_input", Input).focus()

    @on(Button.Pressed, "#btn_exec")
    def on_exec(self, event: Button.Pressed) -> None:
        self._run_command()

    @on(Button.Pressed, "#btn_help")
    def on_help(self, event: Button.Pressed) -> None:
        log = self.query_one(LogPanel)
        log.write(HELP_TEXT)

    @on(Input.Submitted, "#cmd_input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._run_command()

    def action_execute(self) -> None:
        self._run_command()

    def action_refresh(self) -> None:
        self.query_one(TreePanel).rebuild()

    def _run_command(self) -> None:
        inp: Input = self.query_one("#cmd_input", Input)
        raw = inp.value.strip()
        if not raw:
            return
        log = self.query_one(LogPanel)
        log.write(f"[dim]> {raw}[/]")

        parts = raw.split()
        cmd, args = parts[0], parts[1:]

        try:
            result = do_action(cmd, args)
            log.write(result)
        except Exception as e:
            log.write(str(e), error=True)

        # Refresh tree
        self.query_one(TreePanel).rebuild()
        inp.value = ""
        inp.focus()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cats, attrs = build_demo()
    ALL_CATS.extend(cats)
    ALL_ATTRS.extend(attrs)
    ROOT_CAT = cats[0]

    app = TreeApp()
    app.run()