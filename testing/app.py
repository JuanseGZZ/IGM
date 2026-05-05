import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from models import Category, Product, Variant, Attribute, AttributeImplementation, DataTypes

# ─── Demo data ────────────────────────────────────────────────────────────────

def build_demo():
    color = Attribute(key="color", name="Color", data_type="enum", id=1)
    for v in ["Rojo", "Azul", "Verde", "Negro"]:
        color.enum_values.append(v)

    talle = Attribute(key="talle", name="Talle", data_type="enum", id=2)
    for v in ["S", "M", "L", "XL"]:
        talle.enum_values.append(v)

    material = Attribute(key="material", name="Material", data_type="text", id=3, is_static=True)
    peso     = Attribute(key="peso",     name="Peso (g)",  data_type="number", id=4, is_static=True)

    root    = Category(name="Catálogo", id=1)
    ropa    = Category(name="Ropa",     id=2)
    calzado = Category(name="Calzado",  id=3)
    remeras = Category(name="Remeras",  id=4)
    pantas  = Category(name="Pantalones", id=5)

    # Atributos asignados directo: el modelo no tiene add_attribute en Category
    ropa.attributes    = [color, talle]
    remeras.attributes = [material]

    root.add_subcategory(ropa)
    root.add_subcategory(calzado)
    ropa.add_subcategory(remeras)
    ropa.add_subcategory(pantas)

    def make_impl(attr, val): return AttributeImplementation(attribute=attr, value=val)

    # Estáticos van en el producto. Dinámicos (Color, Talle) van en cada variante.
    p1 = Product(code="REM001", title="Remera Básica", price=1500, description="Algodón 100%", brand="Nike", id=1, category=remeras,
                 attributes_implementations=[make_impl(material, "Algodón")])
    p1.add_variant(Variant(id=1, attribute_implementations=[make_impl(color,"Rojo"), make_impl(talle,"M")]))
    p1.add_variant(Variant(id=2, attribute_implementations=[make_impl(color,"Azul"), make_impl(talle,"L")]))
    remeras.add_product(p1)

    p2 = Product(code="REM002", title="Polo Premium", price=2800, description="Piqué francés", brand="Lacoste", id=2, category=remeras,
                 attributes_implementations=[make_impl(material, "Piqué")])
    p2.add_variant(Variant(id=3, attribute_implementations=[make_impl(color,"Verde"), make_impl(talle,"S")]))
    remeras.add_product(p2)

    return root, [color, talle, material, peso]

# ─── Palette ──────────────────────────────────────────────────────────────────

BG      = "#12121E"
BG2     = "#1E1E30"
BG3     = "#2A2A40"
ACCENT  = "#5B7FFF"
GREEN   = "#3DDC84"
PURPLE  = "#B06EFF"
GOLD    = "#FFD166"
TEXT    = "#E8E8F0"
SUBTEXT = "#888AAA"

NODE_COLORS = {
    "category": {"fill": "#2C3E6B", "outline": ACCENT,  "text": TEXT,   "badge": ACCENT},
    "product":  {"fill": "#1E4A30", "outline": GREEN,   "text": TEXT,   "badge": GREEN},
    "variant":  {"fill": "#3A1E5A", "outline": PURPLE,  "text": TEXT,   "badge": PURPLE},
}

NODE_W  = 170
NODE_H  = 50
H_GAP   = 40
V_GAP   = 80

# ─── Helpers ──────────────────────────────────────────────────────────────────

def rounded_rect(canvas, x0, y0, x1, y1, r=12, **kw):
    pts = [
        x0+r,y0,  x1-r,y0,  x1,y0,  x1,y0+r,
        x1,y1-r,  x1,y1,    x1-r,y1, x0+r,y1,
        x0,y1,    x0,y1-r,  x0,y0+r, x0,y0,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def entry_field(parent, label, initial="", label_kw=None, entry_kw=None):
    lkw = {"bg": BG2, "fg": SUBTEXT, "anchor": "w", "font": ("Inter", 9)}
    ekw = {"bg": BG3, "fg": TEXT, "insertbackground": TEXT, "relief": tk.FLAT,
           "highlightthickness": 1, "highlightbackground": BG3,
           "highlightcolor": ACCENT, "font": ("Inter", 10)}
    if label_kw: lkw.update(label_kw)
    if entry_kw: ekw.update(entry_kw)
    tk.Label(parent, text=label, **lkw).pack(fill=tk.X, pady=(8, 1))
    e = tk.Entry(parent, **ekw)
    e.insert(0, initial)
    e.pack(fill=tk.X, ipady=5, padx=1)
    return e

# ─── Main App ─────────────────────────────────────────────────────────────────

class OrgApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IGM Catalog Manager")
        self.geometry("1400x860")
        self.configure(bg=BG)

        self.root_cat, self.all_attrs = build_demo()
        self._key_map: dict[str, object] = {}
        self._positions: dict[str, tuple] = {}
        self._drag_state = None
        self._ghost_items = []
        self._next_attr_id = max(a.id for a in self.all_attrs) + 1
        self._next_cat_id  = 10
        self._next_prod_id = 10
        self._next_var_id  = 10

        self._style()
        self._build_ui()
        self.after(120, self._render_tree)

    # ── Style ─────────────────────────────────────────────────────────────────

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab", background=BG2, foreground=SUBTEXT,
                    padding=[16, 8], font=("Inter", 10), borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", BG3)],
              foreground=[("selected", TEXT)])
        s.configure("Treeview", background=BG2, foreground=TEXT,
                    fieldbackground=BG2, rowheight=28, font=("Inter", 10))
        s.configure("Treeview.Heading", background=BG3, foreground=SUBTEXT,
                    font=("Inter", 9, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", ACCENT)], foreground=[("selected", "white")])

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self._build_tree_tab()
        self._build_attr_tab()

    # ── Tree tab ──────────────────────────────────────────────────────────────

    def _build_tree_tab(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="  Árbol  ")

        # Toolbar
        bar = tk.Frame(tab, bg=BG2, height=48)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        def btn(text, cmd, color=ACCENT):
            b = tk.Label(bar, text=text, bg=color, fg="white",
                         font=("Inter", 9, "bold"), padx=14, pady=0,
                         cursor="hand2", relief=tk.FLAT)
            b.pack(side=tk.LEFT, padx=6, pady=10, ipady=4)
            b.bind("<Button-1>", lambda e: cmd())
            return b

        btn("＋ Categoría",  self._add_category)
        btn("＋ Producto",   self._add_product,  "#2A7A4A")
        btn("＋ Variante",   self._add_variant,  "#5A2A8A")

        # Legend
        for label, color in [("Categoría", ACCENT), ("Producto", GREEN), ("Variante", PURPLE)]:
            tk.Label(bar, text="●", fg=color, bg=BG2, font=("Inter", 14)).pack(side=tk.RIGHT, padx=2, pady=14)
            tk.Label(bar, text=label, fg=SUBTEXT, bg=BG2, font=("Inter", 9)).pack(side=tk.RIGHT, pady=14)

        # Canvas
        cf = tk.Frame(tab, bg=BG)
        cf.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(cf, bg=BG, highlightthickness=0)
        hbar = tk.Scrollbar(cf, orient=tk.HORIZONTAL, command=self.canvas.xview, bg=BG2)
        vbar = tk.Scrollbar(cf, orient=tk.VERTICAL,   command=self.canvas.yview, bg=BG2)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT,  fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_release)
        self.canvas.bind("<Double-Button-1>",  self._on_dbl)
        self.canvas.bind("<MouseWheel>",        lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.canvas.bind("<Shift-MouseWheel>",  lambda e: self.canvas.xview_scroll(int(-1*(e.delta/120)), "units"))

        # Hint
        tk.Label(tab, text="Doble clic → editar  |  Arrastrar → reparentar",
                 bg=BG, fg=SUBTEXT, font=("Inter", 9)).pack(pady=4)

    # ── Attributes tab ────────────────────────────────────────────────────────

    def _build_attr_tab(self):
        tab = tk.Frame(self.nb, bg=BG)
        self.nb.add(tab, text="  Atributos  ")

        bar = tk.Frame(tab, bg=BG2, height=48)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        def btn(text, cmd, color=ACCENT):
            b = tk.Label(bar, text=text, bg=color, fg="white",
                         font=("Inter", 9, "bold"), padx=14, cursor="hand2")
            b.pack(side=tk.LEFT, padx=6, pady=10, ipady=4)
            b.bind("<Button-1>", lambda e: cmd())

        btn("＋ Nuevo atributo", self._new_attr)
        btn("✎ Editar",          self._edit_attr, "#3A5A9A")
        btn("✕ Eliminar",        self._del_attr,  "#8A2020")

        cols = ("ID", "Key", "Nombre", "Tipo", "Estático", "Valores enum")
        self.attr_tv = ttk.Treeview(tab, columns=cols, show="headings", selectmode="browse")
        widths = {"ID": 50, "Key": 120, "Nombre": 140, "Tipo": 90, "Estático": 80, "Valores enum": 300}
        for c in cols:
            self.attr_tv.heading(c, text=c)
            self.attr_tv.column(c, width=widths[c], anchor="w")
        self.attr_tv.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.attr_tv.bind("<Double-1>", lambda e: self._edit_attr())

        self._refresh_attrs()

    def _refresh_attrs(self):
        self.attr_tv.delete(*self.attr_tv.get_children())
        for a in self.all_attrs:
            ev = ", ".join(str(v) for v in a.enum_values) if a.data_type == "enum" else "—"
            self.attr_tv.insert("", tk.END, iid=str(a.id),
                                values=(a.id, a.key, a.name, a.data_type,
                                        "Sí" if a.is_static else "No", ev))

    def _new_attr(self):  self._attr_modal(None)
    def _edit_attr(self):
        sel = self.attr_tv.selection()
        if not sel: return messagebox.showwarning("Sin selección", "Seleccioná un atributo.", parent=self)
        attr = next((a for a in self.all_attrs if str(a.id) == sel[0]), None)
        if attr: self._attr_modal(attr)

    def _del_attr(self):
        sel = self.attr_tv.selection()
        if not sel: return
        attr = next((a for a in self.all_attrs if str(a.id) == sel[0]), None)
        if attr is None: return

        using_cats = self._cats_using_attr(attr)
        using_prods, using_vars = self._impls_using_attr(attr)

        if using_cats or using_prods or using_vars:
            lines = []
            if using_cats:
                lines.append(f"Categorías: {', '.join(c.name for c in using_cats)}")
            if using_prods:
                lines.append(f"Productos: {', '.join(p.code for p in using_prods)}")
            if using_vars:
                affected_codes = sorted({p.code for _, p in using_vars})
                lines.append(f"Variantes en: {', '.join(affected_codes)}")
            detail = "\n".join(lines)
            if not messagebox.askyesno(
                "Atributo en uso",
                f"'{attr.name}' está siendo usado:\n{detail}\n\n"
                "¿Eliminar todas las implementaciones y el atributo?",
                parent=self
            ):
                return
            for cat in using_cats:
                cat.attributes = [a for a in cat.attributes if a != attr]
            for prod in using_prods:
                prod.attributes_implementations = [
                    impl for impl in prod.attributes_implementations
                    if impl.attribute != attr
                ]
            affected_prods = {p for _, p in using_vars}
            for prod in affected_prods:
                for var in prod.variants:
                    var.attribute_implementations = [
                        impl for impl in var.attribute_implementations
                        if impl.attribute != attr
                    ]
                prod.variants = [v for v in prod.variants if v.attribute_implementations]
        else:
            if not messagebox.askyesno("Eliminar", f"¿Eliminar '{attr.name}'?", parent=self):
                return

        self.all_attrs = [a for a in self.all_attrs if a != attr]
        self._refresh_attrs()
        self._render_tree()

    def _attr_modal(self, attr):
        m = tk.Toplevel(self)
        m.title("Nuevo atributo" if attr is None else f"Editar: {attr.name}")
        m.geometry("500x540")
        m.configure(bg=BG2)
        m.grab_set()
        m.resizable(False, False)

        tk.Label(m, text="Nuevo atributo" if attr is None else "Editar atributo",
                 bg=BG2, fg=TEXT, font=("Inter", 13, "bold")).pack(pady=(20, 4))

        f = tk.Frame(m, bg=BG2)
        f.pack(fill=tk.BOTH, expand=True, padx=24, pady=4)

        e_key  = entry_field(f, "Key *",    attr.key  if attr else "")
        e_name = entry_field(f, "Nombre *", attr.name if attr else "")

        tk.Label(f, text="Tipo de dato *", bg=BG2, fg=SUBTEXT, font=("Inter", 9), anchor="w").pack(fill=tk.X, pady=(8,1))
        dtype_var = tk.StringVar(value=attr.data_type if attr else "text")
        cb = ttk.Combobox(f, textvariable=dtype_var, values=DataTypes, state="readonly", font=("Inter", 10))
        cb.pack(fill=tk.X)

        static_var = tk.BooleanVar(value=attr.is_static if attr else False)
        tk.Checkbutton(f, text="Es estático (informativo del producto)",
                       variable=static_var, bg=BG2, fg=TEXT,
                       selectcolor=BG3, activebackground=BG2,
                       font=("Inter", 10)).pack(anchor="w", pady=(10, 0))

        tk.Label(f, text="Valores enum (uno por línea):", bg=BG2, fg=SUBTEXT,
                 font=("Inter", 9), anchor="w").pack(fill=tk.X, pady=(10, 1))
        ev_text = tk.Text(f, height=5, bg=BG3, fg=TEXT, insertbackground=TEXT,
                          relief=tk.FLAT, font=("Inter", 10))
        ev_text.pack(fill=tk.X)

        if attr and attr.enum_values:
            ev_text.insert("1.0", "\n".join(str(v) for v in attr.enum_values))

        def _toggle(*_):
            ev_text.configure(state="normal" if dtype_var.get() == "enum" else "disabled")
        dtype_var.trace_add("write", _toggle); _toggle()

        def _save():
            key  = e_key.get().strip()
            name = e_name.get().strip()
            if not key or not name:
                return messagebox.showerror("Error", "Key y nombre son obligatorios.", parent=m)

            # AC-5: enum requiere al menos un valor
            enum_values = []
            if dtype_var.get() == "enum":
                enum_values = [v.strip() for v in ev_text.get("1.0", tk.END).strip().splitlines() if v.strip()]
                if not enum_values:
                    return messagebox.showerror("Error", "Un atributo enum debe tener al menos un valor.", parent=m)

            # AC-4: is_static no se puede cambiar si el attr ya está en uso
            if attr is not None and attr.is_static != static_var.get():
                cats_in_use = self._cats_using_attr(attr)
                prods_in_use, vars_in_use = self._impls_using_attr(attr)
                if cats_in_use or prods_in_use or vars_in_use:
                    return messagebox.showerror(
                        "No permitido",
                        "No se puede cambiar 'Estático' de un atributo en uso.\n"
                        "Creá un nuevo atributo.",
                        parent=m
                    )

            if attr is None:
                na = Attribute(key=key, name=name, data_type=dtype_var.get(),
                               id=self._next_attr_id, is_static=static_var.get())
                self._next_attr_id += 1
                if dtype_var.get() == "enum":
                    na.enum_values = enum_values
                self.all_attrs.append(na)
            else:
                attr.key = key; attr.name = name
                attr.data_type = dtype_var.get(); attr.is_static = static_var.get()
                if dtype_var.get() == "enum":
                    attr.enum_values = enum_values
            self._refresh_attrs(); m.destroy()

        tk.Label(m, bg=BG2, height=1).pack()
        save_btn = tk.Label(m, text="  Guardar  ", bg=ACCENT, fg="white",
                            font=("Inter", 10, "bold"), cursor="hand2", padx=6)
        save_btn.pack(pady=(0, 20), ipady=6)
        save_btn.bind("<Button-1>", lambda e: _save())

    # ── Layout algorithm ──────────────────────────────────────────────────────

    def _visual_children(self, obj):
        if isinstance(obj, Category):
            return list(obj.subcategories) + list(obj.products)
        if isinstance(obj, Product):
            return list(obj.variants)
        return []

    def _obj_key(self, obj):
        if isinstance(obj, Category): return f"cat_{obj.id}"
        if isinstance(obj, Product):  return f"prod_{obj.id}"
        if isinstance(obj, Variant):  return f"var_{obj.id}"
        return str(id(obj))

    def _subtree_width(self, obj):
        children = self._visual_children(obj)
        if not children:
            return NODE_W
        total = sum(self._subtree_width(c) for c in children)
        return max(NODE_W, total + H_GAP * max(0, len(children) - 1))

    def _assign_positions(self, obj, cx, depth, positions):
        key = self._obj_key(obj)
        cy  = depth * (NODE_H + V_GAP) + NODE_H // 2 + 30
        positions[key] = (cx, cy)
        self._key_map[key] = obj

        children = self._visual_children(obj)
        if not children:
            return

        total_w = sum(self._subtree_width(c) for c in children)
        gaps    = H_GAP * max(0, len(children) - 1)
        x = cx - (total_w + gaps) / 2

        for child in children:
            w = self._subtree_width(child)
            self._assign_positions(child, x + w / 2, depth + 1, positions)
            x += w + H_GAP

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render_tree(self):
        self.canvas.delete("all")
        self._key_map.clear()
        self._positions.clear()

        w = self.canvas.winfo_width() or 1200
        self._assign_positions(self.root_cat, w / 2, 0, self._positions)

        # Edges
        for key, (cx, cy) in self._positions.items():
            obj = self._key_map[key]
            for child in self._visual_children(obj):
                ck = self._obj_key(child)
                if ck in self._positions:
                    x2, y2 = self._positions[ck]
                    self.canvas.create_line(
                        cx, cy + NODE_H // 2,
                        x2, y2 - NODE_H // 2,
                        fill="#3A3A5A", width=1.5, smooth=True, arrow=tk.LAST,
                        arrowshape=(8, 10, 4)
                    )

        # Nodes
        for key, (cx, cy) in self._positions.items():
            self._draw_node(key, self._key_map[key], cx, cy)

        self.canvas.configure(scrollregion=self.canvas.bbox("all") or (0, 0, 1200, 800))

    def _draw_node(self, key, obj, cx, cy):
        if   isinstance(obj, Category): kind, label = "category", obj.name
        elif isinstance(obj, Product):  kind, label = "product",  f"{obj.code}\n{obj.title}"
        else:
            kind = "variant"
            parts = [f"{i.attribute.name}: {i.value}" for i in obj.attribute_implementations[:2]]
            label = "\n".join(parts) or f"Variante {obj.id}"

        c  = NODE_COLORS[kind]
        x0 = cx - NODE_W // 2
        y0 = cy - NODE_H // 2
        x1 = cx + NODE_W // 2
        y1 = cy + NODE_H // 2

        # Shadow
        rounded_rect(self.canvas, x0+3, y0+3, x1+3, y1+3, r=10,
                     fill="#08080F", outline="", tags=(key, "node"))
        # Body
        rounded_rect(self.canvas, x0, y0, x1, y1, r=10,
                     fill=c["fill"], outline=c["outline"], width=1.5,
                     tags=(key, "node", kind))
        # Badge stripe (left edge)
        rounded_rect(self.canvas, x0, y0, x0+6, y1, r=4,
                     fill=c["badge"], outline="", tags=(key, "node"))
        # Label
        self.canvas.create_text(cx + 3, cy, text=label, fill=c["text"],
                                font=("Inter", 9, "bold"), justify=tk.CENTER,
                                width=NODE_W - 24, tags=(key, "node", kind))

    # ── Canvas interaction helpers ────────────────────────────────────────────

    def _cxy(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _node_at(self, cx, cy):
        items = self.canvas.find_overlapping(cx-2, cy-2, cx+2, cy+2)
        for item in reversed(items):
            for tag in self.canvas.gettags(item):
                if tag in self._key_map:
                    return tag, self._key_map[tag]
        return None, None

    # ── Drag & drop ───────────────────────────────────────────────────────────

    def _on_press(self, event):
        cx, cy = self._cxy(event)
        key, obj = self._node_at(cx, cy)
        if key:
            self._drag_state = {"key": key, "obj": obj, "start": (cx, cy)}

    def _on_drag(self, event):
        if not self._drag_state:
            return
        cx, cy = self._cxy(event)
        sx, sy = self._drag_state["start"]
        for item in self._ghost_items:
            self.canvas.delete(item)
        self._ghost_items.clear()

        if abs(cx - sx) > 6 or abs(cy - sy) > 6:
            npos = self._positions.get(self._drag_state["key"])
            if npos:
                g = self.canvas.create_line(*npos, cx, cy,
                                            fill=GOLD, width=2, dash=(8, 4),
                                            arrow=tk.LAST, arrowshape=(10, 12, 4))
                self._ghost_items.append(g)
                # Highlight target
                tk_key, _ = self._node_at(cx, cy)
                if tk_key and tk_key != self._drag_state["key"]:
                    tpos = self._positions[tk_key]
                    h = rounded_rect(self.canvas,
                                     tpos[0]-NODE_W//2-4, tpos[1]-NODE_H//2-4,
                                     tpos[0]+NODE_W//2+4, tpos[1]+NODE_H//2+4,
                                     r=13, fill="", outline=GOLD, width=2.5)
                    self._ghost_items.append(h)

    def _on_release(self, event):
        if not self._drag_state:
            return
        cx, cy  = self._cxy(event)
        sx, sy  = self._drag_state["start"]
        src_key = self._drag_state["key"]
        src_obj = self._drag_state["obj"]

        for item in self._ghost_items:
            self.canvas.delete(item)
        self._ghost_items.clear()
        self._drag_state = None

        if abs(cx - sx) < 8 and abs(cy - sy) < 8:
            return

        tgt_key, tgt_obj = self._node_at(cx, cy)
        if tgt_key and tgt_key != src_key:
            self._reparent(src_obj, tgt_obj)

    def _reparent(self, src, tgt):
        try:
            if isinstance(src, Category) and isinstance(tgt, Category):
                if src is tgt or src is self.root_cat:
                    return

                # Modelo valida ciclo y exclusividad antes de mostrar nada
                impact_out, impact_in = src.impact_on_change_father(tgt)

                if not self._impact_preview(
                    title=f"Mover categoría '{src.name}' → '{tgt.name}'",
                    lose_pairs=impact_out,
                    gain_pairs=impact_in,
                ):
                    return

                # Aplicar lo que el modelo dijo
                self._apply_remove_impls(impact_out)
                self._apply_add_impls(impact_in)
                if impact_in:
                    self._fill_added_attrs_modal(impact_in)

                # Mover en el árbol — modelo no tiene remove_subcategory
                if src.father_categorie:
                    src.father_categorie.subcategories.remove(src)  # GAP del modelo
                tgt.add_subcategory(src)  # setea father_categorie via modelo
                self._render_tree()

            elif isinstance(src, Product) and isinstance(tgt, Category):
                to_add, to_remove = src.impact_on_change_category(tgt)

                if not self._impact_preview(
                    title=f"Mover producto '{src.code}' → '{tgt.name}'",
                    lose_pairs=[(to_remove, [src])],
                    gain_pairs=[(to_add,    [src])],
                ):
                    return

                # Quitar lo que sale
                src.attributes_implementations = [
                    impl for impl in src.attributes_implementations
                    if impl.attribute not in to_remove
                ]
                src.clean_variants_after_attr_removal(to_remove)  # E8: modelo

                # Agregar placeholders vacíos para lo que entra
                for attr in to_add:
                    if attr.is_static:
                        src.attributes_implementations.append(
                            AttributeImplementation(attribute=attr, value="")
                        )
                    else:
                        for var in src.variants:
                            var_keys = {impl.attribute.key for impl in var.attribute_implementations}
                            if attr.key not in var_keys:
                                var.attribute_implementations.append(
                                    AttributeImplementation(attribute=attr, value="")
                                )

                # Formulario para completar los valores nuevos
                if to_add:
                    self._fill_added_attrs_modal([(to_add, [src])])

                # Mover en el árbol — modelo no tiene remove_product
                if src.category:
                    src.category.products.remove(src)  # GAP del modelo
                src.category = tgt     # actualizar ANTES de add_product para que
                tgt.add_product(src)   # _check_product_completeness valide contra la cat nueva
                self._render_tree()

            else:
                messagebox.showwarning("No permitido",
                                       "Solo podés mover:\n• Categoría → Categoría\n• Producto → Categoría",
                                       parent=self)
        except ValueError as e:
            messagebox.showerror("Error al mover", str(e), parent=self)

    # ── Impact helpers ────────────────────────────────────────────────────────

    def _apply_add_impls(self, impact_pairs):
        """Aplica lo que impact_on_* dijo.
        Estáticos → agrega AttributeImplementation vacío al producto.
        Dinámicos → agrega AttributeImplementation vacío a cada variante del producto."""
        for attrs, products in impact_pairs:
            for prod in products:
                static_keys = {impl.attribute.key for impl in prod.attributes_implementations}
                for attr in attrs:
                    if attr.is_static:
                        if attr.key not in static_keys:
                            prod.attributes_implementations.append(
                                AttributeImplementation(attribute=attr, value="")
                            )
                    else:
                        for var in prod.variants:
                            var_keys = {impl.attribute.key for impl in var.attribute_implementations}
                            if attr.key not in var_keys:
                                var.attribute_implementations.append(
                                    AttributeImplementation(attribute=attr, value="")
                                )

    def _apply_remove_impls(self, impact_pairs):
        """Aplica lo que impact_on_* dijo: quita AttributeImplementation del producto
        y delega al modelo la limpieza de variantes (E8)."""
        for attrs, products in impact_pairs:
            keys = {a.key for a in attrs}
            for prod in products:
                prod.attributes_implementations = [
                    impl for impl in prod.attributes_implementations
                    if impl.attribute.key not in keys
                ]
                prod.clean_variants_after_attr_removal(attrs)  # E8: modelo

    def _impact_preview(self, title, lose_pairs, gain_pairs):
        """
        Muestra exactamente lo que devolvieron los métodos impact_on_* del modelo.
        Siempre muestra — nunca confirma silencioso — para que se pueda verificar.
        Retorna True si el usuario confirma, False si cancela.
        """
        def fmt(pairs):
            lines = []
            for attrs, products in pairs:
                if not attrs or not products:
                    continue
                attr_str = ", ".join(a.name for a in sorted(attrs, key=lambda a: a.key))
                prod_str = ", ".join(
                    getattr(p, "title", None) or getattr(p, "name", f"id={p.id}")
                    for p in products
                )
                lines.append(f"  [{attr_str}]  →  {prod_str}")
            return "\n".join(lines) if lines else "  (sin impacto)"

        gain_text = fmt(gain_pairs)
        lose_text = fmt(lose_pairs)

        result = {"ok": False}

        m = tk.Toplevel(self)
        m.title("Impacto del modelo")
        m.configure(bg=BG2)
        m.grab_set()
        m.resizable(False, False)

        tk.Label(m, text=title, bg=BG2, fg=TEXT,
                 font=("Inter", 11, "bold"), wraplength=460).pack(pady=(18, 6), padx=20)
        tk.Label(m, text="Resultado de impact_on_* del modelo:",
                 bg=BG2, fg=SUBTEXT, font=("Inter", 8)).pack(padx=20)

        def section(label, color, text):
            tk.Label(m, text=label, bg=BG2, fg=color,
                     font=("Inter", 9, "bold"), anchor="w").pack(fill=tk.X, padx=20, pady=(10, 0))
            tk.Label(m, text=text, bg=BG3, fg=TEXT,
                     font=("Inter", 9), anchor="w", justify=tk.LEFT,
                     wraplength=440).pack(fill=tk.X, padx=20, pady=(2, 0), ipady=6)

        section("SE AGREGAN attrs a productos:", GREEN,     gain_text)
        section("SE QUITAN  attrs de productos:", "#FF6B6B", lose_text)

        tk.Label(m, text="Valores agregados quedan vacíos — completar en el nodo del producto.",
                 bg=BG2, fg=SUBTEXT, font=("Inter", 8), wraplength=440).pack(padx=20, pady=(8, 0))

        row = tk.Frame(m, bg=BG2)
        row.pack(pady=16)

        def _ok():
            result["ok"] = True
            m.destroy()

        _lbl_btn(row, "Confirmar y aplicar", _ok,       ACCENT).pack(side=tk.LEFT, padx=8, ipady=6)
        _lbl_btn(row, "Cancelar",            m.destroy, "#555577").pack(side=tk.LEFT, padx=8, ipady=6)

        m.geometry("500x360")
        self.wait_window(m)
        return result["ok"]

    def _fill_added_attrs_modal(self, impact_pairs) -> None:
        """Formulario para completar valores de implementaciones recién agregadas.
        impact_pairs: [(set[Attribute], list[Product])] — mismo formato que impact_on_*.
        Agrupa por atributo y muestra producto/variante por fila.
        Sin cancelar — el cambio ya fue confirmado en el paso anterior."""
        # Armar lista plana (attr, prod, var_or_None), sin duplicados
        to_fill = []
        seen = set()
        for attrs, products in impact_pairs:
            for attr in sorted(attrs, key=lambda a: a.key):
                for prod in products:
                    if attr.is_static:
                        k = (attr.key, id(prod), None)
                        if k not in seen:
                            seen.add(k); to_fill.append((attr, prod, None))
                    else:
                        for var in prod.variants:
                            k = (attr.key, id(prod), id(var))
                            if k not in seen:
                                seen.add(k); to_fill.append((attr, prod, var))

        if not to_fill:
            return

        # Agrupar por attr.key para mostrar una sección por atributo
        by_attr = {}
        for attr, prod, var in to_fill:
            by_attr.setdefault(attr.key, []).append((attr, prod, var))

        m = tk.Toplevel(self)
        m.title("Completar atributos nuevos")
        m.configure(bg=BG2)
        m.grab_set()
        m.resizable(False, True)
        m.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(m, text="Completar valores para atributos nuevos",
                 bg=BG2, fg=TEXT, font=("Inter", 11, "bold")).pack(pady=(18, 4), padx=20)
        tk.Label(m, text="El cambio ya fue confirmado. Completá los valores antes de continuar.",
                 bg=BG2, fg=SUBTEXT, font=("Inter", 8), wraplength=440).pack(padx=20)

        f = tk.Frame(m, bg=BG2)
        f.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        # entries: lista de (widget, prod, var_or_None, attr_key) para el _apply
        entries = []

        for attr_key, items in by_attr.items():
            attr = items[0][0]
            kind  = "estático" if attr.is_static else "dinámico"
            color = ACCENT if attr.is_static else PURPLE
            tk.Label(f, text=f"  {attr.name}  [{attr.data_type} · {kind}]",
                     bg=BG2, fg=color, font=("Inter", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(10, 2))

            for _, prod, var in items:
                if var is None:
                    label    = f"Prod. {prod.code}"
                    existing = next((i.value for i in prod.attributes_implementations if i.attribute == attr), "")
                else:
                    label    = f"Prod. {prod.code} — Var. #{var.id}"
                    existing = next((i.value for i in var.attribute_implementations  if i.attribute == attr), "")

                row = tk.Frame(f, bg=BG3); row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=label + ":", bg=BG3, fg=SUBTEXT,
                         font=("Inter", 9), width=26, anchor="w").pack(side=tk.LEFT, padx=8, pady=4)

                if attr.data_type == "enum" and attr.enum_values:
                    sv = tk.StringVar(value=existing if existing in attr.enum_values else attr.enum_values[0])
                    cb = ttk.Combobox(row, textvariable=sv, values=attr.enum_values,
                                      state="readonly", font=("Inter", 9))
                    cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
                    entries.append((sv, prod, var, attr_key))
                else:
                    e = tk.Entry(row, bg=BG3, fg=TEXT, insertbackground=TEXT,
                                 relief=tk.FLAT, font=("Inter", 9))
                    e.insert(0, existing)
                    e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
                    entries.append((e, prod, var, attr_key))

        def _apply():
            for widget, prod, var, attr_key in entries:
                value = widget.get()
                impl_list = prod.attributes_implementations if var is None else var.attribute_implementations
                for impl in impl_list:
                    if impl.attribute.key == attr_key:
                        impl.value = value; break
            m.destroy()

        m.geometry(f"560x{min(660, 200 + len(to_fill) * 48)}")
        _lbl_btn(m, "Completar", _apply, ACCENT).pack(pady=16, ipady=6)
        self.wait_window(m)

    # ── Double-click edit ─────────────────────────────────────────────────────

    def _on_dbl(self, event):
        cx, cy = self._cxy(event)
        key, obj = self._node_at(cx, cy)
        if obj:
            self._edit_modal(key, obj)

    def _edit_modal(self, key, obj):
        m = tk.Toplevel(self)
        m.configure(bg=BG2)
        m.grab_set()
        m.resizable(False, False)

        if isinstance(obj, Category):
            m.title(f"Categoría — {obj.name}")
            m.geometry("420x320")
            tk.Label(m, text=f"Categoría: {obj.name}", bg=BG2, fg=TEXT,
                     font=("Inter", 13, "bold")).pack(pady=(20, 4))
            f = tk.Frame(m, bg=BG2); f.pack(fill=tk.X, padx=24)
            e_name = entry_field(f, "Nombre", obj.name)

            # Attributes assigned
            tk.Label(f, text="Atributos asignados:", bg=BG2, fg=SUBTEXT,
                     font=("Inter", 9), anchor="w").pack(fill=tk.X, pady=(12, 2))
            attr_frame = tk.Frame(f, bg=BG3); attr_frame.pack(fill=tk.X)

            attr_vars = {}
            for a in self.all_attrs:
                var = tk.BooleanVar(value=a in obj.attributes)
                attr_vars[a] = var
                tk.Checkbutton(attr_frame, text=f"{a.name} ({a.key})", variable=var,
                               bg=BG3, fg=TEXT, selectcolor=BG2,
                               activebackground=BG3,
                               font=("Inter", 9)).pack(anchor="w", padx=8, pady=1)

            def _save_cat():
                obj.name = e_name.get().strip() or obj.name

                old_attr_set = set(obj.attributes)
                new_attr_set = {a for a, v in attr_vars.items() if v.get()}
                added   = new_attr_set - old_attr_set
                removed = old_attr_set - new_attr_set

                # Compute impact before mutating obj.attributes
                gain_pairs = []
                lose_pairs = []
                for attr in added:
                    gain_pairs.extend(obj.impact_on_add_attribute(attr))
                for attr in removed:
                    lose_pairs.extend(obj.impact_on_remove_attribute(attr))

                if gain_pairs or lose_pairs:
                    confirmed = self._impact_preview(
                        title=f"Cambios en atributos de '{obj.name}'",
                        gain_pairs=gain_pairs,
                        lose_pairs=lose_pairs,
                    )
                    if not confirmed:
                        return

                # Mutar la categoría — modelo no tiene setter de attributes
                obj.attributes = list(new_attr_set)

                # Aplicar a productos descendientes lo que el modelo reportó
                self._apply_add_impls(gain_pairs)
                self._apply_remove_impls(lose_pairs)
                if gain_pairs:
                    self._fill_added_attrs_modal(gain_pairs)

                self._render_tree()
                m.destroy()

            def _del_cat():
                if obj is self.root_cat:
                    return messagebox.showerror("Error", "No podés eliminar la raíz.", parent=m)
                subcats, prods, var_count = self._collect_descendants(obj)
                if subcats or prods:
                    lines = []
                    if subcats:
                        lines.append(f"• {len(subcats)} categoría(s): {', '.join(c.name for c in subcats)}")
                    if prods:
                        lines.append(f"• {len(prods)} producto(s): {', '.join(p.code for p in prods)}")
                    if var_count:
                        lines.append(f"• {var_count} variante(s)")
                    if not messagebox.askyesno(
                        "Eliminar en cascada",
                        f"Eliminar '{obj.name}' también eliminará:\n" + "\n".join(lines) + "\n\n¿Confirmar?",
                        parent=m
                    ):
                        return
                elif not messagebox.askyesno("Eliminar", f"¿Eliminar '{obj.name}'?", parent=m):
                    return
                self._cascade_delete_cat(obj)
                m.destroy(); self._render_tree()

            row = tk.Frame(m, bg=BG2); row.pack(pady=16)
            _lbl_btn(row, "Guardar", _save_cat, ACCENT).pack(side=tk.LEFT, padx=6, ipady=6)
            _lbl_btn(row, "Eliminar", _del_cat, "#8A2020").pack(side=tk.LEFT, padx=6, ipady=6)

        elif isinstance(obj, Product):
            m.title(f"Producto — {obj.title}")
            impl_count = len(obj.attributes_implementations)
            m.geometry(f"480x{600 + impl_count * 34}")
            tk.Label(m, text=f"Producto: {obj.code}", bg=BG2, fg=TEXT,
                     font=("Inter", 13, "bold")).pack(pady=(20, 4))
            f = tk.Frame(m, bg=BG2); f.pack(fill=tk.X, padx=24)
            e_code  = entry_field(f, "Código",      obj.code)
            e_title = entry_field(f, "Título",       obj.title)
            e_price = entry_field(f, "Precio",       str(obj.price))
            e_brand = entry_field(f, "Marca",        obj.brand)
            e_desc  = entry_field(f, "Descripción",  obj.description)

            # Atributos implementados (estáticos)
            tk.Label(f, text="Atributos del producto:", bg=BG2, fg=SUBTEXT,
                     font=("Inter", 9), anchor="w").pack(fill=tk.X, pady=(12, 2))

            impl_entries = {}
            if obj.attributes_implementations:
                for impl in obj.attributes_implementations:
                    row = tk.Frame(f, bg=BG3); row.pack(fill=tk.X, pady=2)
                    tk.Label(row, text=impl.attribute.name + ":", bg=BG3, fg=SUBTEXT,
                             font=("Inter", 9), width=14, anchor="w").pack(side=tk.LEFT, padx=8, pady=4)
                    if impl.attribute.data_type == "enum" and impl.attribute.enum_values:
                        sv = tk.StringVar(value=impl.value if impl.value in impl.attribute.enum_values else impl.attribute.enum_values[0])
                        cb = ttk.Combobox(row, textvariable=sv, values=impl.attribute.enum_values,
                                          state="readonly", font=("Inter", 10))
                        cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
                        impl_entries[impl] = sv
                    else:
                        e = tk.Entry(row, bg=BG3, fg=TEXT, insertbackground=TEXT,
                                     relief=tk.FLAT, font=("Inter", 10))
                        e.insert(0, impl.value)
                        e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
                        impl_entries[impl] = e
            else:
                tk.Label(f, text="  (ninguno)", bg=BG3, fg=SUBTEXT,
                         font=("Inter", 9)).pack(fill=tk.X, ipady=4)

            # Variantes
            tk.Label(f, text=f"Variantes: {len(obj.variants)}", bg=BG2, fg=SUBTEXT,
                     font=("Inter", 9)).pack(anchor="w", pady=(10, 0))

            def _save_prod():
                obj.code  = e_code.get().strip()  or obj.code
                obj.title = e_title.get().strip()  or obj.title
                obj.brand = e_brand.get().strip()
                obj.description = e_desc.get().strip()
                try: obj.price = float(e_price.get())
                except ValueError: pass
                for impl, e in impl_entries.items():
                    impl.value = e.get().strip()
                self._render_tree(); m.destroy()

            _lbl_btn(m, "Guardar", _save_prod, ACCENT).pack(pady=16, ipady=6)

        elif isinstance(obj, Variant):
            m.title(f"Variante {obj.id}")
            m.geometry("420x380")
            tk.Label(m, text=f"Variante #{obj.id}", bg=BG2, fg=TEXT,
                     font=("Inter", 13, "bold")).pack(pady=(20, 4))
            f = tk.Frame(m, bg=BG2); f.pack(fill=tk.BOTH, expand=True, padx=24)

            tk.Label(f, text="Atributos implementados:", bg=BG2, fg=SUBTEXT,
                     font=("Inter", 9), anchor="w").pack(fill=tk.X, pady=(0, 8))

            entries = {}
            for impl in obj.attribute_implementations:
                row = tk.Frame(f, bg=BG3); row.pack(fill=tk.X, pady=2)
                tk.Label(row, text=impl.attribute.name + ":", bg=BG3, fg=SUBTEXT,
                         font=("Inter", 9), width=14, anchor="w").pack(side=tk.LEFT, padx=8, pady=4)
                if impl.attribute.data_type == "enum" and impl.attribute.enum_values:
                    sv = tk.StringVar(value=impl.value if impl.value in impl.attribute.enum_values else impl.attribute.enum_values[0])
                    cb = ttk.Combobox(row, textvariable=sv, values=impl.attribute.enum_values,
                                      state="readonly", font=("Inter", 10))
                    cb.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
                    entries[impl] = sv
                else:
                    e = tk.Entry(row, bg=BG3, fg=TEXT, insertbackground=TEXT,
                                 relief=tk.FLAT, font=("Inter", 10))
                    e.insert(0, impl.value)
                    e.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
                    entries[impl] = e

            def _save_var():
                for impl, widget in entries.items():
                    impl.value = widget.get().strip() or impl.value
                self._render_tree(); m.destroy()

            _lbl_btn(m, "Guardar", _save_var, ACCENT).pack(pady=16, ipady=6)

    # ── Add dialogs ───────────────────────────────────────────────────────────

    def _add_category(self):
        d = _QuickDialog(self, "Nueva Categoría", [
            ("Nombre", ""),
            ("Padre (nombre, vacío = raíz)", ""),
        ])
        if not d.result: return
        name, parent_name = d.result
        name = name.strip()
        if not name: return messagebox.showwarning("Error", "Nombre requerido.", parent=self)

        parent = self._find_cat(parent_name.strip()) if parent_name.strip() else self.root_cat
        if parent is None:
            return messagebox.showerror("Error", f"Categoría '{parent_name}' no encontrada.", parent=self)

        new_cat = Category(name=name, id=self._next_cat_id)
        self._next_cat_id += 1
        try:
            parent.add_subcategory(new_cat)
            self._render_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _add_product(self):
        d = _QuickDialog(self, "Nuevo Producto", [
            ("Categoría (nombre)", ""),
            ("Código", ""),
            ("Título", ""),
            ("Precio", "0"),
            ("Marca", ""),
        ])
        if not d.result: return
        cat_name, code, title, price_s, brand = d.result
        cat = self._find_cat(cat_name.strip())
        if cat is None:
            return messagebox.showerror("Error", f"Categoría '{cat_name}' no encontrada.", parent=self)
        try:
            price = float(price_s) if price_s else 0.0
            p = Product(code=code.strip(), title=title.strip(), price=price,
                        description="", brand=brand.strip(),
                        id=self._next_prod_id, category=cat)
            self._next_prod_id += 1
            cat.add_product(p)
            self._render_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _add_variant(self):
        d = _QuickDialog(self, "Nueva Variante", [
            ("Producto (código)", ""),
        ])
        if not d.result: return
        code = d.result[0].strip()
        prod = self._find_prod(code)
        if prod is None:
            return messagebox.showerror("Error", f"Producto '{code}' no encontrado.", parent=self)

        req_attrs = prod.get_required_dynamic_attrs()
        if not req_attrs:
            return messagebox.showinfo("Sin atributos", "Este producto no tiene atributos dinámicos requeridos.", parent=self)

        # Ask values per attribute
        fields = [(f"{a.name} ({', '.join(str(v) for v in a.enum_values) if a.enum_values else a.data_type})", "")
                  for a in sorted(req_attrs, key=lambda a: a.key)]
        d2 = _QuickDialog(self, f"Variante de {prod.code}", fields)
        if not d2.result: return

        impls = [AttributeImplementation(attribute=a, value=v.strip())
                 for a, v in zip(sorted(req_attrs, key=lambda a: a.key), d2.result)]
        var = Variant(id=self._next_var_id, attribute_implementations=impls)
        self._next_var_id += 1
        try:
            prod.add_variant(var)
            self._render_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_cat(self, name, node=None):
        if node is None: node = self.root_cat
        if node.name.lower() == name.lower(): return node
        for s in node.subcategories:
            r = self._find_cat(name, s)
            if r: return r
        return None

    def _find_prod(self, code, node=None):
        if node is None: node = self.root_cat
        for p in node.products:
            if p.code.lower() == code.lower(): return p
        for s in node.subcategories:
            r = self._find_prod(code, s)
            if r: return r
        return None

    def _collect_descendants(self, cat):
        """Retorna (subcats_list, products_list, variant_count) de toda la descendencia de cat."""
        subcats, products, var_count = [], [], [0]
        def _walk(node):
            for sub in node.subcategories:
                subcats.append(sub)
                _walk(sub)
            for prod in node.products:
                products.append(prod)
                var_count[0] += len(prod.variants)
        _walk(cat)
        return subcats, products, var_count[0]

    def _cascade_delete_cat(self, cat):
        """Elimina cat y toda su descendencia del árbol."""
        for sub in list(cat.subcategories):
            self._cascade_delete_cat(sub)
        cat.subcategories.clear()
        cat.products.clear()
        if cat.father_categorie:
            cat.father_categorie.subcategories.remove(cat)
            cat.father_categorie = None

    def _cats_using_attr(self, attr):
        """Lista de categorías que tienen attr en sus atributos propios."""
        result = []
        def _walk(node):
            if attr in node.attributes:
                result.append(node)
            for sub in node.subcategories:
                _walk(sub)
        _walk(self.root_cat)
        return result

    def _impls_using_attr(self, attr):
        """Retorna (prod_list, [(var, prod)]) con todos los lugares donde attr está implementado."""
        prod_usages = []
        var_usages  = []
        def _walk(node):
            for prod in node.products:
                if any(impl.attribute == attr for impl in prod.attributes_implementations):
                    prod_usages.append(prod)
                for var in prod.variants:
                    if any(impl.attribute == attr for impl in var.attribute_implementations):
                        var_usages.append((var, prod))
            for sub in node.subcategories:
                _walk(sub)
        _walk(self.root_cat)
        return prod_usages, var_usages


# ─── Reusable label-button ────────────────────────────────────────────────────

def _lbl_btn(parent, text, cmd, color):
    b = tk.Label(parent, text=f"  {text}  ", bg=color, fg="white",
                 font=("Inter", 10, "bold"), cursor="hand2")
    b.bind("<Button-1>", lambda e: cmd())
    return b


# ─── Quick multi-field dialog ─────────────────────────────────────────────────

class _QuickDialog(tk.Toplevel):
    def __init__(self, parent, title, fields):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG2)
        self.resizable(False, False)
        self.grab_set()
        self.result = None

        tk.Label(self, text=title, bg=BG2, fg=TEXT,
                 font=("Inter", 12, "bold")).pack(pady=(18, 4))

        f = tk.Frame(self, bg=BG2)
        f.pack(fill=tk.X, padx=24)

        self._entries = []
        for label, default in fields:
            e = entry_field(f, label, default)
            self._entries.append(e)

        btn = tk.Label(self, text="  Confirmar  ", bg=ACCENT, fg="white",
                       font=("Inter", 10, "bold"), cursor="hand2")
        btn.pack(pady=16, ipady=6)
        btn.bind("<Button-1>", lambda e: self._confirm())

        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())

        self.geometry(f"380x{100 + len(fields)*62}")
        self.wait_window()

    def _confirm(self):
        self.result = [e.get() for e in self._entries]
        self.destroy()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = OrgApp()
    app.mainloop()
