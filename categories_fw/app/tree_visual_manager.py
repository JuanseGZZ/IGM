import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox

from models import Attribute, AttributeImplementation, Category, Product, Variant


class TreeVisualManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor Visual de Arbol")
        self.geometry("1100x680")
        self.minsize(960, 560)

        self.root_category = Category(name="Catalogo Principal")

        self.ui_to_obj = {}
        self.node_labels = []
        self.label_to_obj = {}
        self.attributes_by_key = {}
        self.canvas_item_to_obj = {}

        self._build_demo_data()
        self._build_ui()
        self.refresh_tree()

    def _build_demo_data(self):
        ropa = Category(name="Ropa")
        calzado = Category(name="Calzado")
        self.root_category.add_subcategory(ropa)
        self.root_category.add_subcategory(calzado)

        talle = Attribute(key="talle", name="Talle", data_type="enum", is_static=False)
        talle.add_enum_value("S")
        talle.add_enum_value("M")
        talle.add_enum_value("L")

        material = Attribute(key="material", name="Material", data_type="text", is_static=True)
        hombre = Category(name="Hombre")
        mujer = Category(name="Mujer")
        ropa.add_subcategory(hombre)
        ropa.add_subcategory(mujer)

        ropa.attributes.append(material)
        ropa._attribute_keys.add(material.key)
        mujer.attributes.append(talle)
        mujer._attribute_keys.add(talle.key)

        self.attributes_by_key[talle.key] = talle
        self.attributes_by_key[material.key] = material

        calzado.add_product(
            Product(
                code="ZAP001",
                title="Zapatilla Urbana",
                price=10.0,
                description="",
                brand="Demo",
                category=calzado,
            )
        )

    def _build_ui(self):
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ===== PESTAÑA 1: Árbol Visual =====
        tree_tab = tk.Frame(notebook)
        notebook.add(tree_tab, text="Árbol Visual")
        self._build_tree_tab(tree_tab)

        # ===== PESTAÑA 2: Gestión de Productos =====
        products_tab = tk.Frame(notebook)
        notebook.add(products_tab, text="Productos")
        self._build_products_tab(products_tab)

        # ===== PESTAÑA 3: Gestión de Atributos =====
        attributes_tab = tk.Frame(notebook)
        notebook.add(attributes_tab, text="Atributos")
        self._build_attributes_tab(attributes_tab)

    def _build_tree_tab(self, parent):
        container = parent
        top_frame = tk.PanedWindow(container, sashrelief=tk.RAISED, orient=tk.HORIZONTAL)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 6))

        tree_frame = tk.Frame(top_frame)
        top_frame.add(tree_frame, minsize=420)

        self.tree = ttk.Treeview(tree_frame, columns=("kind", "path"), show="tree headings")
        self.tree.heading("#0", text="Nodo")
        self.tree.heading("kind", text="Tipo")
        self.tree.heading("path", text="Path")
        self.tree.column("#0", width=280)
        self.tree.column("kind", width=130, anchor=tk.CENTER)
        self.tree.column("path", width=600)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        graph_frame = tk.LabelFrame(top_frame, text="Vista de nodos")
        top_frame.add(graph_frame, minsize=420)

        graph_canvas_frame = tk.Frame(graph_frame)
        graph_canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.graph_canvas = tk.Canvas(graph_canvas_frame, bg="#f7fafc", highlightthickness=0)
        self.graph_canvas.grid(row=0, column=0, sticky="nsew")

        self.graph_y_scroll = ttk.Scrollbar(graph_canvas_frame, orient="vertical", command=self.graph_canvas.yview)
        self.graph_y_scroll.grid(row=0, column=1, sticky="ns")
        self.graph_x_scroll = ttk.Scrollbar(graph_canvas_frame, orient="horizontal", command=self.graph_canvas.xview)
        self.graph_x_scroll.grid(row=1, column=0, sticky="ew")

        graph_canvas_frame.rowconfigure(0, weight=1)
        graph_canvas_frame.columnconfigure(0, weight=1)

        self.graph_canvas.configure(
            yscrollcommand=self.graph_y_scroll.set,
            xscrollcommand=self.graph_x_scroll.set,
        )

        self.graph_canvas.bind("<Button-1>", self._on_canvas_click)
        self.graph_canvas.bind("<Shift-ButtonPress-1>", self._start_canvas_pan)
        self.graph_canvas.bind("<Shift-B1-Motion>", self._do_canvas_pan)
        self.graph_canvas.bind("<ButtonPress-2>", self._start_canvas_pan)
        self.graph_canvas.bind("<B2-Motion>", self._do_canvas_pan)
        self.graph_canvas.bind("<ButtonPress-3>", self._start_canvas_pan)
        self.graph_canvas.bind("<B3-Motion>", self._do_canvas_pan)
        self.graph_canvas.bind("<MouseWheel>", self._on_canvas_wheel)
        self.graph_canvas.bind("<Button-4>", self._on_canvas_wheel)
        self.graph_canvas.bind("<Button-5>", self._on_canvas_wheel)

        action_frame = tk.LabelFrame(parent, text="Panel de acciones")
        action_frame.pack(fill=tk.X, padx=10, pady=(0, 6))

        tk.Label(action_frame, text="Accion").grid(row=0, column=0, padx=6, pady=8, sticky="w")
        self.action_var = tk.StringVar(value="crear_categoria")
        self.action_combo = ttk.Combobox(
            action_frame,
            textvariable=self.action_var,
            state="readonly",
            width=24,
            values=[
                "crear_categoria",
                "crear_producto",
                "editar_nombre",
                "mover",
                "eliminar",
                "crear_atributo",
                "agregar_atributo",
                "quitar_atributo",
                "agregar_variante",
            ],
        )
        self.action_combo.grid(row=0, column=1, padx=6, pady=8, sticky="w")
        self.action_combo.bind("<<ComboboxSelected>>", self._on_action_change)

        tk.Label(action_frame, text="Nodo origen").grid(row=0, column=2, padx=6, pady=8, sticky="w")
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(action_frame, textvariable=self.source_var, width=36)
        self.source_combo.grid(row=0, column=3, padx=6, pady=8, sticky="we")

        tk.Label(action_frame, text="Nodo destino").grid(row=0, column=4, padx=6, pady=8, sticky="w")
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(action_frame, textvariable=self.target_var, width=36)
        self.target_combo.grid(row=0, column=5, padx=6, pady=8, sticky="we")

        tk.Label(action_frame, text="Atributo").grid(row=0, column=6, padx=6, pady=8, sticky="w")
        self.attr_var = tk.StringVar()
        self.attr_combo = ttk.Combobox(action_frame, textvariable=self.attr_var, width=28)
        self.attr_combo.grid(row=0, column=7, padx=6, pady=8, sticky="we")

        tk.Label(action_frame, text="Valor").grid(row=1, column=0, padx=6, pady=8, sticky="w")
        self.value_var = tk.StringVar()
        self.value_entry = tk.Entry(action_frame, textvariable=self.value_var, width=38)
        self.value_entry.grid(row=1, column=1, columnspan=3, padx=6, pady=8, sticky="we")

        tk.Label(action_frame, text="Detalle").grid(row=1, column=4, padx=6, pady=8, sticky="w")
        self.extra_var = tk.StringVar()
        self.extra_entry = tk.Entry(action_frame, textvariable=self.extra_var, width=38)
        self.extra_entry.grid(row=1, column=5, columnspan=3, padx=6, pady=8, sticky="we")

        self.execute_btn = tk.Button(action_frame, text="Ejecutar", command=self.execute_action)
        self.execute_btn.grid(row=2, column=7, padx=6, pady=8, sticky="e")

        action_frame.columnconfigure(3, weight=1)
        action_frame.columnconfigure(5, weight=1)
        action_frame.columnconfigure(7, weight=1)

        self.help_label = tk.Label(
            parent,
            anchor="w",
            justify=tk.LEFT,
            fg="#333",
            text="",
        )
        self.help_label.pack(fill=tk.X, padx=10)

        self.status_var = tk.StringVar(value="Listo.")
        self.status_label = tk.Label(parent, textvariable=self.status_var, anchor="w", fg="#2d6a4f")
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

        self._on_action_change()

    def _build_products_tab(self, parent):
        container = parent
        # No hacer pack en container, ya está manejado por el notebook

        # ===== FORMULARIO DE CREACIÓN =====
        form_frame = tk.LabelFrame(container, text="Crear nuevo producto", padx=10, pady=10)
        form_frame.pack(fill=tk.X, padx=10, pady=(10, 10))

        tk.Label(form_frame, text="Categoría:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.prod_category_var = tk.StringVar()
        self.prod_category_combo = ttk.Combobox(form_frame, textvariable=self.prod_category_var, state="readonly", width=35)
        self.prod_category_combo.grid(row=0, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Código:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.prod_code_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.prod_code_var, width=38).grid(row=1, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Título:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.prod_title_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.prod_title_var, width=38).grid(row=2, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Precio:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.prod_price_var = tk.StringVar(value="0.0")
        tk.Entry(form_frame, textvariable=self.prod_price_var, width=38).grid(row=3, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Marca:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.prod_brand_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.prod_brand_var, width=38).grid(row=4, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Descripción:").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
        self.prod_desc_var = tk.StringVar()
        desc_entry = tk.Text(form_frame, width=38, height=3)
        desc_entry.grid(row=5, column=1, sticky="we", padx=5, pady=5)
        self.prod_desc_text = desc_entry

        tk.Button(form_frame, text="Crear Producto", bg="#4CAF50", fg="white", command=self._create_product_from_form).grid(row=6, column=1, sticky="e", padx=5, pady=10)

        form_frame.columnconfigure(1, weight=1)

        # ===== LISTADO DE PRODUCTOS =====
        list_frame = tk.LabelFrame(container, text="Productos existentes", padx=0, pady=0)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=("code", "title", "price", "brand", "category", "variantes"),
            show="headings",
            height=15
        )
        self.products_tree.heading("#0", text="ID")
        self.products_tree.heading("code", text="Código")
        self.products_tree.heading("title", text="Título")
        self.products_tree.heading("price", text="Precio")
        self.products_tree.heading("brand", text="Marca")
        self.products_tree.heading("category", text="Categoría")
        self.products_tree.heading("variantes", text="Variantes")

        self.products_tree.column("#0", width=40)
        self.products_tree.column("code", width=80)
        self.products_tree.column("title", width=180)
        self.products_tree.column("price", width=80)
        self.products_tree.column("brand", width=100)
        self.products_tree.column("category", width=120)
        self.products_tree.column("variantes", width=80)

        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.products_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.products_tree.configure(yscrollcommand=scroll.set)

        # ===== ACCIONES SOBRE PRODUCTOS =====
        actions_frame = tk.Frame(container)
        actions_frame.pack(fill=tk.X, padx=0, pady=(10, 0))

        tk.Button(actions_frame, text="Editar seleccionado", command=self._edit_product_from_list).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Gestionar variantes", command=self._manage_variants_from_list).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Eliminar", bg="#f44336", fg="white", command=self._delete_product_from_list).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Refrescar", command=self._refresh_products_list).pack(side=tk.LEFT, padx=5)

    def _update_product_categories_combo(self):
        cats = []
        for node in self._collect_nodes():
            if isinstance(node, Category):
                cats.append(self._node_label(node))
        self.prod_category_combo["values"] = cats
        if cats and not self.prod_category_var.get():
            self.prod_category_var.set(cats[0])

    def _create_product_from_form(self):
        try:
            cat_label = self.prod_category_var.get().strip()
            if not cat_label:
                raise ValueError("Debes seleccionar una categoría.")
            category = self.label_to_obj.get(cat_label)
            if not isinstance(category, Category):
                raise ValueError("Selecciona una categoría válida.")

            code = self.prod_code_var.get().strip()
            title = self.prod_title_var.get().strip()
            if not code:
                raise ValueError("El código no puede estar vacío.")
            if not title:
                raise ValueError("El título no puede estar vacío.")

            try:
                price = float(self.prod_price_var.get().strip())
            except ValueError:
                raise ValueError("El precio debe ser un número válido.")

            brand = self.prod_brand_var.get().strip() or ""
            description = self.prod_desc_text.get("1.0", "end").strip() or ""

            product = Product(
                code=code,
                title=title,
                price=price,
                description=description,
                brand=brand,
                category=category,
            )
            category.add_product(product)

            messagebox.showinfo("Éxito", f"Producto '{title}' creado correctamente en '{category.name}'.")
            self._clear_product_form()
            self._refresh_products_list()
            self.refresh_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _clear_product_form(self):
        self.prod_code_var.set("")
        self.prod_title_var.set("")
        self.prod_price_var.set("0.0")
        self.prod_brand_var.set("")
        self.prod_desc_text.delete("1.0", "end")

    def _refresh_products_list(self):
        self._update_product_categories_combo()
        self.products_tree.delete(*self.products_tree.get_children())

        all_products = []
        for node in self._collect_nodes():
            if isinstance(node, Product):
                all_products.append(node)

        for idx, prod in enumerate(sorted(all_products, key=lambda p: p.code), start=1):
            self.products_tree.insert(
                "",
                "end",
                iid=f"prod_{idx}",
                text=str(idx),
                values=(
                    prod.code,
                    prod.title,
                    f"{prod.price:.2f}",
                    prod.brand,
                    prod.category.name,
                    len(prod.variants),
                ),
            )

    def _get_selected_product_from_list(self):
        selected = self.products_tree.selection()
        if not selected:
            raise ValueError("Debes seleccionar un producto en la lista.")
        iid = selected[0]
        # Extraemos el código de la fila seleccionada
        values = self.products_tree.item(iid)["values"]
        code = values[0]
        for node in self._collect_nodes():
            if isinstance(node, Product) and node.code == code:
                return node
        raise ValueError("Producto no encontrado.")

    def _edit_product_from_list(self):
        try:
            product = self._get_selected_product_from_list()
            self.prod_code_var.set(product.code)
            self.prod_title_var.set(product.title)
            self.prod_price_var.set(str(product.price))
            self.prod_brand_var.set(product.brand)
            self.prod_desc_text.delete("1.0", "end")
            self.prod_desc_text.insert("1.0", product.description)
            messagebox.showinfo("Edición", f"Datos del producto '{product.title}' cargados en el formulario.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _manage_variants_from_list(self):
        try:
            product = self._get_selected_product_from_list()
            self._show_variant_dialog(product)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _delete_product_from_list(self):
        try:
            product = self._get_selected_product_from_list()
            if messagebox.askyesno("Confirmar", f"¿Eliminar producto '{product.title}'?"):
                category = product.category
                category.products.remove(product)
                category._product_codes.discard(product.code)
                messagebox.showinfo("Éxito", "Producto eliminado.")
                self._refresh_products_list()
                self.refresh_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _build_attributes_tab(self, parent):
        container = parent

        # ===== FORMULARIO DE CREACIÓN DE ATRIBUTOS =====
        form_frame = tk.LabelFrame(container, text="Crear nuevo atributo", padx=10, pady=10)
        form_frame.pack(fill=tk.X, padx=10, pady=(10, 10))

        tk.Label(form_frame, text="Key (identificador):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.attr_key_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.attr_key_var, width=35).grid(row=0, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Nombre:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.attr_name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.attr_name_var, width=35).grid(row=1, column=1, sticky="we", padx=5, pady=5)

        tk.Label(form_frame, text="Tipo de dato:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.attr_type_var = tk.StringVar(value="text")
        type_combo = ttk.Combobox(
            form_frame, textvariable=self.attr_type_var, state="readonly", width=32,
            values=["text", "number", "boolean", "enum"]
        )
        type_combo.grid(row=2, column=1, sticky="we", padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_attr_type_change)

        tk.Label(form_frame, text="Estático (solo info):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.attr_static_var = tk.StringVar(value="0")
        frame_static = tk.Frame(form_frame)
        frame_static.grid(row=3, column=1, sticky="we", padx=5, pady=5)
        tk.Radiobutton(frame_static, text="No", variable=self.attr_static_var, value="0").pack(side=tk.LEFT)
        tk.Radiobutton(frame_static, text="Sí", variable=self.attr_static_var, value="1").pack(side=tk.LEFT)

        tk.Label(form_frame, text="Valores enum (si aplica):").grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        self.attr_enum_var = tk.StringVar()
        enum_entry = tk.Text(form_frame, width=38, height=2)
        enum_entry.grid(row=4, column=1, sticky="we", padx=5, pady=5)
        enum_entry.insert("1.0", "valor1,valor2,valor3")
        self.attr_enum_text = enum_entry
        tk.Label(form_frame, text="(separados por coma)", font=("Arial", 8), fg="#666").grid(row=5, column=1, sticky="w", padx=5)

        tk.Button(form_frame, text="Crear Atributo", bg="#4CAF50", fg="white", command=self._create_attribute_from_form).grid(row=6, column=1, sticky="e", padx=5, pady=10)

        form_frame.columnconfigure(1, weight=1)

        # ===== LISTADO DE ATRIBUTOS =====
        list_frame = tk.LabelFrame(container, text="Atributos existentes", padx=0, pady=0)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        tree_frame = tk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.attributes_tree = ttk.Treeview(
            tree_frame,
            columns=("key", "name", "type", "static", "values"),
            show="headings",
            height=12
        )
        self.attributes_tree.heading("key", text="Key")
        self.attributes_tree.heading("name", text="Nombre")
        self.attributes_tree.heading("type", text="Tipo")
        self.attributes_tree.heading("static", text="Estático")
        self.attributes_tree.heading("values", text="Valores/Detalles")

        self.attributes_tree.column("key", width=100)
        self.attributes_tree.column("name", width=120)
        self.attributes_tree.column("type", width=90)
        self.attributes_tree.column("static", width=80)
        self.attributes_tree.column("values", width=300)

        self.attributes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.attributes_tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.attributes_tree.configure(yscrollcommand=scroll.set)

        # ===== ACCIONES SOBRE ATRIBUTOS =====
        actions_frame = tk.Frame(container)
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(actions_frame, text="Eliminar seleccionado", bg="#f44336", fg="white", command=self._delete_attribute_from_list).pack(side=tk.LEFT, padx=5)
        tk.Button(actions_frame, text="Refrescar", command=self._refresh_attributes_list).pack(side=tk.LEFT, padx=5)

    def _on_attr_type_change(self, _event=None):
        attr_type = self.attr_type_var.get()
        if attr_type == "enum":
            self.attr_enum_text.configure(state="normal")
        else:
            self.attr_enum_text.configure(state="disabled")

    def _create_attribute_from_form(self):
        try:
            key = self.attr_key_var.get().strip()
            name = self.attr_name_var.get().strip()
            data_type = self.attr_type_var.get()
            is_static = self.attr_static_var.get() == "1"

            if not key:
                raise ValueError("La key del atributo no puede estar vacía.")
            if not name:
                raise ValueError("El nombre del atributo no puede estar vacío.")
            if key in self.attributes_by_key:
                raise ValueError(f"Ya existe un atributo con key '{key}'.")

            attr = Attribute(key=key, name=name, data_type=data_type, is_static=is_static)

            if data_type == "enum":
                enum_text = self.attr_enum_text.get("1.0", "end").strip()
                if enum_text:
                    values = [v.strip() for v in enum_text.split(",") if v.strip()]
                    for val in values:
                        attr.add_enum_value(val)
                else:
                    raise ValueError("Para tipo enum, debes ingresar al menos un valor.")

            self.attributes_by_key[key] = attr
            messagebox.showinfo("Éxito", f"Atributo '{key}' creado correctamente.")
            self._clear_attribute_form()
            self._refresh_attributes_list()
            self._update_attribute_selector()
            self.refresh_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _clear_attribute_form(self):
        self.attr_key_var.set("")
        self.attr_name_var.set("")
        self.attr_type_var.set("text")
        self.attr_static_var.set("0")
        self.attr_enum_text.delete("1.0", "end")
        self.attr_enum_text.insert("1.0", "valor1,valor2,valor3")
        self.attr_enum_text.configure(state="disabled")

    def _refresh_attributes_list(self):
        self.attributes_tree.delete(*self.attributes_tree.get_children())

        attrs = list(self.attributes_by_key.values())
        for idx, attr in enumerate(sorted(attrs, key=lambda a: a.key), start=1):
            static_text = "Sí" if attr.is_static else "No"
            if attr.data_type == "enum":
                values_text = ", ".join(attr.enum_values)
            else:
                values_text = "-"

            self.attributes_tree.insert(
                "",
                "end",
                iid=f"attr_{idx}",
                values=(attr.key, attr.name, attr.data_type, static_text, values_text),
            )

    def _get_selected_attribute_from_list(self):
        selected = self.attributes_tree.selection()
        if not selected:
            raise ValueError("Debes seleccionar un atributo en la lista.")
        iid = selected[0]
        values = self.attributes_tree.item(iid)["values"]
        key = values[0]
        attr = self.attributes_by_key.get(key)
        if attr is None:
            raise ValueError("Atributo no encontrado.")
        return attr

    def _delete_attribute_from_list(self):
        try:
            attr = self._get_selected_attribute_from_list()
            if messagebox.askyesno("Confirmar", f"¿Eliminar atributo '{attr.key}'?"):
                # Remover de todas las categorías que lo tengan
                for node in self._collect_nodes():
                    if isinstance(node, Category):
                        node.attributes = [a for a in node.attributes if a.key != attr.key]
                        node._attribute_keys.discard(attr.key)

                del self.attributes_by_key[attr.key]
                messagebox.showinfo("Éxito", "Atributo eliminado.")
                self._refresh_attributes_list()
                self._update_attribute_selector()
                self.refresh_tree()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _set_status_ok(self, msg):
        self.status_label.config(fg="#2d6a4f")
        self.status_var.set(msg)

    def _set_status_error(self, msg):
        self.status_label.config(fg="#b00020")
        self.status_var.set(msg)

    def _node_label(self, obj):
        if isinstance(obj, Category):
            return f"CAT:{obj.name}#{obj.id if obj.id is not None else id(obj)}"
        return f"PROD:{obj.title}#{obj.code}#{obj.id if obj.id is not None else id(obj)}"

    def _attribute_label(self, attr):
        static_text = "static" if attr.is_static else "dynamic"
        return f"{attr.key} | {attr.name} | {attr.data_type} | {static_text}"

    def _path_for(self, obj):
        if isinstance(obj, Category):
            names = []
            node = obj
            while node is not None:
                names.append(node.name)
                node = node.father_categorie
            return " / ".join(reversed(names))

        names = []
        node = obj.category
        while node is not None:
            names.append(node.name)
            node = node.father_categorie
        return " / ".join(reversed(names)) + f" / {obj.title}"

    def _collect_nodes(self):
        out = [self.root_category]

        def walk(cat):
            for sub in cat.subcategories:
                out.append(sub)
                walk(sub)
            for prod in cat.products:
                out.append(prod)

        walk(self.root_category)
        return out

    def _collect_known_attributes(self):
        out = dict(self.attributes_by_key)

        def walk(cat):
            for attr in cat.attributes:
                out[attr.key] = attr
            for sub in cat.subcategories:
                walk(sub)

        walk(self.root_category)
        self.attributes_by_key = out
        return out

    def _update_node_selectors(self):
        self.node_labels.clear()
        self.label_to_obj.clear()
        for node in self._collect_nodes():
            label = self._node_label(node)
            self.node_labels.append(label)
            self.label_to_obj[label] = node

        self.source_combo["values"] = self.node_labels
        self.target_combo["values"] = self.node_labels

        if not self.source_var.get() and self.node_labels:
            self.source_var.set(self.node_labels[0])

    def _update_attribute_selector(self):
        attrs = self._collect_known_attributes()
        values = [self._attribute_label(attr) for attr in attrs.values()]
        self.attr_combo["values"] = values
        if values and not self.attr_var.get():
            self.attr_var.set(values[0])

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.ui_to_obj.clear()

        root_ui = "root"
        self.ui_to_obj[root_ui] = self.root_category
        self.tree.insert(
            "",
            "end",
            iid=root_ui,
            text=f"[CAT] {self.root_category.name}",
            values=("Categoria", self._path_for(self.root_category)),
            open=True,
        )

        self._draw_category(root_ui, self.root_category)
        self._update_node_selectors()
        self._update_attribute_selector()
        self._draw_graph()
        self._refresh_products_list()

    def _draw_category(self, parent_ui, category):
        for sub in category.subcategories:
            iid = self._node_label(sub)
            self.ui_to_obj[iid] = sub
            self.tree.insert(
                parent_ui,
                "end",
                iid=iid,
                text=f"[CAT] {sub.name}",
                values=("Categoria", self._path_with_attrs(sub)),
                open=True,
            )
            self._draw_category(iid, sub)

        for prod in category.products:
            iid = self._node_label(prod)
            self.ui_to_obj[iid] = prod
            self.tree.insert(
                parent_ui,
                "end",
                iid=iid,
                text=f"[PROD] {prod.title} ({prod.code}) | variantes: {len(prod.variants)}",
                values=("Producto", self._path_for(prod)),
                open=True,
            )
            for idx, variant in enumerate(prod.variants, start=1):
                variant_parts = []
                for impl in variant.attribute_implementations:
                    variant_parts.append(f"{impl.attribute.key}={impl.value}")
                variant_text = ", ".join(variant_parts) if variant_parts else "sin valores"
                self.tree.insert(
                    iid,
                    "end",
                    text=f"[VAR {idx}] {variant_text}",
                    values=("Variante", f"{self._path_for(prod)} / VAR-{idx}"),
                    open=True,
                )

    def _path_with_attrs(self, category):
        attrs = ", ".join(sorted(attr.key for attr in category.attributes)) or "sin atributos"
        return f"{self._path_for(category)} | attrs: {attrs}"

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        obj = self.ui_to_obj.get(selected[0])
        if obj is None:
            return
        self.source_var.set(self._node_label(obj))

    def _on_canvas_click(self, event):
        current = self.graph_canvas.find_withtag("current")
        if not current:
            return
        obj = self.canvas_item_to_obj.get(current[0])
        if obj is None:
            return
        self.source_var.set(self._node_label(obj))
        self._set_status_ok(f"Nodo seleccionado desde vista grafica: {self._node_label(obj)}")

    def _start_canvas_pan(self, event):
        self.graph_canvas.scan_mark(event.x, event.y)

    def _do_canvas_pan(self, event):
        self.graph_canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_canvas_wheel(self, event):
        # Zoom de vista grafica: Ctrl + rueda para evitar zoom accidental.
        ctrl_mask = 0x0004
        if not (event.state & ctrl_mask) and getattr(event, "num", None) is None:
            return

        if getattr(event, "num", None) == 4:
            factor = 1.1
        elif getattr(event, "num", None) == 5:
            factor = 0.9
        else:
            factor = 1.1 if event.delta > 0 else 0.9

        x = self.graph_canvas.canvasx(event.x)
        y = self.graph_canvas.canvasy(event.y)
        self.graph_canvas.scale("all", x, y, factor, factor)
        self._update_graph_scrollregion()

    def _on_action_change(self, _event=None):
        action = self.action_var.get()
        if action == "crear_categoria":
            self.help_label.config(
                text="Selecciona una categoria en 'Nodo origen'. En 'Valor' escribe el nombre de la nueva categoria."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="normal")
            self.extra_entry.configure(state="disabled")
            self.extra_var.set("")
        elif action == "crear_producto":
            self.help_label.config(
                text="Selecciona una categoria en 'Nodo origen'. En 'Valor' escribe el titulo del producto (codigo automatico)."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="normal")
            self.extra_entry.configure(state="disabled")
            self.extra_var.set("")
        elif action == "editar_nombre":
            self.help_label.config(
                text="Selecciona el nodo en 'Nodo origen'. En 'Valor' escribe el nuevo nombre/titulo."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="normal")
            self.extra_entry.configure(state="disabled")
            self.extra_var.set("")
        elif action == "mover":
            self.help_label.config(
                text="Selecciona en 'Nodo origen' el nodo a mover y en 'Nodo destino' una categoria destino."
            )
            self.target_combo.configure(state="readonly")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="disabled")
            self.extra_entry.configure(state="disabled")
            self.value_var.set("")
            self.extra_var.set("")
        elif action == "eliminar":
            self.help_label.config(
                text="Selecciona en 'Nodo origen' el nodo a eliminar."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="disabled")
            self.extra_entry.configure(state="disabled")
            self.value_var.set("")
            self.extra_var.set("")
        elif action == "crear_atributo":
            self.help_label.config(
                text="Crear atributo global. Valor=key. Detalle=nombre|tipo(text/number/boolean/enum)|is_static(0/1)|enum1,enum2 (opcional)."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="normal")
            self.extra_entry.configure(state="normal")
        elif action == "agregar_atributo":
            self.help_label.config(
                text="Selecciona categoria en origen y el atributo en el combo 'Atributo'. Se ejecuta impacto del modelo E4."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="readonly")
            self.value_entry.configure(state="disabled")
            self.extra_entry.configure(state="disabled")
            self.value_var.set("")
            self.extra_var.set("")
        elif action == "agregar_variante":
            self.help_label.config(
                text="Selecciona producto en origen. En 'Valor': atributo=valor,atributo=valor (ej: talle=M,color=rojo)."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="disabled")
            self.value_entry.configure(state="normal")
            self.extra_entry.configure(state="disabled")
            self.extra_var.set("")
        else:
            self.help_label.config(
                text="Selecciona categoria en origen y el atributo en el combo 'Atributo'. Se ejecuta impacto del modelo E5."
            )
            self.target_combo.configure(state="disabled")
            self.attr_combo.configure(state="readonly")
            self.value_entry.configure(state="disabled")
            self.extra_entry.configure(state="disabled")
            self.value_var.set("")
            self.extra_var.set("")

    def _get_selected_attribute(self):
        selected = self.attr_var.get().strip()
        if not selected:
            raise ValueError("Debes seleccionar un atributo.")
        key = selected.split("|")[0].strip()
        attr = self.attributes_by_key.get(key)
        if attr is None:
            raise ValueError("Atributo invalido.")
        return attr

    def _create_attribute(self):
        key = self.value_var.get().strip()
        detail = self.extra_var.get().strip()
        if not key:
            raise ValueError("Para crear atributo, 'Valor' debe contener la key.")
        if key in self.attributes_by_key:
            raise ValueError(f"Ya existe un atributo con key '{key}'.")
        if not detail:
            raise ValueError("Debes completar 'Detalle' con nombre|tipo|is_static.")

        parts = [p.strip() for p in detail.split("|")]
        if len(parts) < 3:
            raise ValueError("Formato invalido en Detalle. Usa nombre|tipo|is_static(0/1)|enum1,enum2(opcional).")
        name = parts[0]
        data_type = parts[1]
        if data_type not in ["text", "number", "boolean", "enum"]:
            raise ValueError("Tipo invalido. Debe ser text, number, boolean o enum.")
        is_static = parts[2] in ["1", "true", "True", "si", "yes"]

        attr = Attribute(key=key, name=name, data_type=data_type, is_static=is_static)

        if data_type == "enum" and len(parts) > 3 and parts[3]:
            enum_values = [v.strip() for v in parts[3].split(",") if v.strip()]
            for enum_value in enum_values:
                attr.add_enum_value(enum_value)

        self.attributes_by_key[key] = attr
        self._set_status_ok(f"Atributo '{key}' creado.")

    def _apply_attribute_to_category(self, category, attr):
        if attr.key in category._attribute_keys:
            raise ValueError(f"La categoria ya tiene el atributo '{attr.key}'.")
        impact = category.impact_on_add_attribute(attr)
        category.attributes.append(attr)
        category._attribute_keys.add(attr.key)
        self._set_status_ok(f"Atributo '{attr.key}' agregado. Impacto: {self._format_impact(impact)}")

    def _remove_attribute_from_category(self, category, attr):
        if attr.key not in category._attribute_keys:
            raise ValueError(f"La categoria no tiene el atributo '{attr.key}'.")
        impact = category.impact_on_remove_attribute(attr)
        category.attributes = [existing for existing in category.attributes if existing.key != attr.key]
        category._attribute_keys.discard(attr.key)
        self._set_status_ok(f"Atributo '{attr.key}' removido. Impacto: {self._format_impact(impact)}")

    def _format_impact(self, impact):
        if not impact:
            return "sin productos afectados"
        pieces = []
        for attrs, products in impact:
            attr_keys = sorted(attr.key for attr in attrs)
            product_codes = [prod.code for prod in products]
            pieces.append(f"attrs={attr_keys} -> productos={product_codes}")
        return " ; ".join(pieces)

    def _parse_variant_map(self, raw_text):
        mapping = {}
        if not raw_text.strip():
            return mapping

        parts = [part.strip() for part in raw_text.split(",") if part.strip()]
        for part in parts:
            if "=" not in part:
                raise ValueError(f"Par invalido '{part}'. Usa formato atributo=valor.")
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if not key:
                raise ValueError("La clave del atributo no puede estar vacia.")
            mapping[key] = value
        return mapping

    def _cast_variant_value(self, attr, raw_value):
        if attr.data_type in ["text", "enum"]:
            return raw_value
        if attr.data_type == "number":
            if "." in raw_value:
                return float(raw_value)
            return int(raw_value)
        if attr.data_type == "boolean":
            value_lower = raw_value.lower()
            if value_lower in ["true", "1", "si", "yes"]:
                return True
            if value_lower in ["false", "0", "no"]:
                return False
            raise ValueError(f"Valor booleano invalido para '{attr.key}': {raw_value}")
        raise ValueError(f"Tipo de dato no soportado en variante: {attr.data_type}")

    def _add_variant_to_product(self, product):
        required = product.get_required_dynamic_attrs()
        value_map = self._parse_variant_map(self.value_var.get().strip())

        impls = []
        for attr in required:
            if attr.key not in value_map:
                continue
            typed_value = self._cast_variant_value(attr, value_map[attr.key])
            if not attr.check_value(typed_value):
                raise ValueError(f"Valor invalido para '{attr.key}': {value_map[attr.key]}")
            impls.append(AttributeImplementation(attribute=attr, value=typed_value))

        # Si hay claves de mas, se dejan para que add_variant reporte 'de mas'.
        for extra_key, raw_value in value_map.items():
            if any(attr.key == extra_key for attr in required):
                continue
            extra_attr = self.attributes_by_key.get(extra_key)
            if extra_attr is None:
                raise ValueError(f"El atributo '{extra_key}' no existe.")
            typed_value = self._cast_variant_value(extra_attr, raw_value)
            if not extra_attr.check_value(typed_value):
                raise ValueError(f"Valor invalido para '{extra_key}': {raw_value}")
            impls.append(AttributeImplementation(attribute=extra_attr, value=typed_value))

        variant = Variant(attribute_implementations=impls)
        product.add_variant(variant)
        self._set_status_ok(f"Variante agregada al producto '{product.title}'.")

    def _get_selected_source(self):
        src_label = self.source_var.get().strip()
        if not src_label:
            raise ValueError("Debes indicar un nodo origen.")
        src = self.label_to_obj.get(src_label)
        if src is None:
            raise ValueError("Nodo origen invalido.")
        return src

    def execute_action(self):
        action = self.action_var.get()

        try:
            source = self._get_selected_source()

            if action == "crear_categoria":
                value = self.value_var.get().strip()
                if not value:
                    raise ValueError("Debes escribir el nombre de la categoria a crear.")
                if not isinstance(source, Category):
                    raise ValueError("Solo una categoria puede contener subcategorias.")
                source.add_subcategory(Category(name=value))
                self._set_status_ok(f"Categoria '{value}' creada.")

            elif action == "crear_producto":
                value = self.value_var.get().strip()
                if not value:
                    raise ValueError("Debes escribir el titulo del producto a crear.")
                if not isinstance(source, Category):
                    raise ValueError("Solo una categoria puede contener productos.")

                code = self._generate_product_code(value, source)
                product = Product(
                    code=code,
                    title=value,
                    price=0.0,
                    description="",
                    brand="",
                    category=source,
                )
                source.add_product(product)
                self._set_status_ok(f"Producto '{value}' creado en '{source.name}'.")

            elif action == "editar_nombre":
                value = self.value_var.get().strip()
                if not value:
                    raise ValueError("Debes escribir el nuevo nombre.")
                if source is self.root_category:
                    raise ValueError("No se puede renombrar la categoria raiz.")

                if isinstance(source, Category):
                    old = source.name
                    source.name = value
                    self._set_status_ok(f"Categoria renombrada: '{old}' -> '{value}'.")
                else:
                    old = source.title
                    source.title = value
                    self._set_status_ok(f"Producto renombrado: '{old}' -> '{value}'.")

            elif action == "mover":
                dst_label = self.target_var.get().strip()
                if not dst_label:
                    raise ValueError("Debes indicar el nodo destino.")
                destination = self.label_to_obj.get(dst_label)
                if destination is None:
                    raise ValueError("Nodo destino invalido.")
                if not isinstance(destination, Category):
                    raise ValueError("El nodo destino debe ser una categoria.")
                if source is self.root_category:
                    raise ValueError("No se puede mover la categoria raiz.")
                if source is destination:
                    raise ValueError("No puedes mover un nodo dentro de si mismo.")

                self._move_node(source, destination)
                self._set_status_ok("Nodo movido correctamente.")

            elif action == "eliminar":
                if source is self.root_category:
                    raise ValueError("No se puede eliminar la categoria raiz.")
                self._delete_node(source)
                self._set_status_ok("Nodo eliminado correctamente.")

            elif action == "crear_atributo":
                self._create_attribute()

            elif action == "agregar_atributo":
                if not isinstance(source, Category):
                    raise ValueError("Solo una categoria puede recibir atributos.")
                attr = self._get_selected_attribute()
                self._apply_attribute_to_category(source, attr)

            elif action == "quitar_atributo":
                if not isinstance(source, Category):
                    raise ValueError("Solo una categoria puede perder atributos.")
                attr = self._get_selected_attribute()
                self._remove_attribute_from_category(source, attr)

            elif action == "agregar_variante":
                if not isinstance(source, Product):
                    raise ValueError("Debes seleccionar un producto en 'Nodo origen'.")
                self._show_variant_dialog(source)

            else:
                raise ValueError("Accion no soportada.")

            self.refresh_tree()

        except ValueError as err:
            self._set_status_error(str(err))
        except Exception as err:
            self._set_status_error(f"Error inesperado: {err}")

    def _move_node(self, source, destination):
        if isinstance(source, Category):
            old_parent = source.father_categorie
            if old_parent is None:
                raise ValueError("La categoria no tiene padre para moverla.")

            # Se deja que models valide ciclos y exclusividad de hijos.
            destination.add_subcategory(source)
            old_parent.subcategories.remove(source)

        else:
            old_parent = source.category
            if old_parent is None:
                raise ValueError("El producto no tiene categoria padre.")

            destination.add_product(source)
            old_parent.products.remove(source)
            old_parent._product_codes.discard(source.code)
            source.category = destination

    def _delete_node(self, source):
        if isinstance(source, Category):
            parent = source.father_categorie
            if parent is None:
                raise ValueError("La categoria no tiene padre, no se puede eliminar.")
            parent.subcategories.remove(source)
            source.father_categorie = None
            return

        parent = source.category
        if parent is None:
            raise ValueError("El producto no tiene categoria padre, no se puede eliminar.")
        parent.products.remove(source)
        parent._product_codes.discard(source.code)
        source.category = None

    def _generate_product_code(self, title, category):
        base = "".join(ch for ch in title.upper() if ch.isalnum())[:5] or "PROD"
        idx = 1
        code = f"{base}{idx:03d}"
        while code in category._product_codes:
            idx += 1
            code = f"{base}{idx:03d}"
        return code

    def _draw_graph(self):
        self.graph_canvas.delete("all")
        self.canvas_item_to_obj.clear()

        self.update_idletasks()
        width = max(420, self.graph_canvas.winfo_width())
        height = max(400, self.graph_canvas.winfo_height())

        cx = width // 2
        cy = height // 2
        self._draw_node_box(cx, cy, self.root_category, is_category=True)

        top_children = list(self.root_category.subcategories)
        left = top_children[::2]
        right = top_children[1::2]

        left_y = 50
        for cat in left:
            left_y = self._draw_branch(cat, cx, cy, side=-1, depth=1, next_y=left_y)

        right_y = 50
        for cat in right:
            right_y = self._draw_branch(cat, cx, cy, side=1, depth=1, next_y=right_y)

        # Si raiz tiene productos, los dibuja debajo.
        prod_y = cy + 80
        for prod in self.root_category.products:
            x = cx
            y = prod_y
            self.graph_canvas.create_line(cx, cy + 22, x, y - 18, fill="#6c757d", width=1)
            self._draw_node_box(x, y, prod, is_category=False)
            prod_y += 56

        self._update_graph_scrollregion()

    def _update_graph_scrollregion(self):
        bbox = self.graph_canvas.bbox("all")
        if not bbox:
            self.graph_canvas.configure(scrollregion=(0, 0, 100, 100))
            return
        pad = 60
        self.graph_canvas.configure(
            scrollregion=(bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        )

    def _draw_branch(self, category, parent_x, parent_y, side, depth, next_y):
        x_step = 170
        x = parent_x + (side * x_step)
        y = next_y

        self.graph_canvas.create_line(parent_x, parent_y + 22, x, y - 20, fill="#6c757d", width=1)
        self._draw_node_box(x, y, category, is_category=True)

        y_cursor = y + 70
        for sub in category.subcategories:
            y_cursor = self._draw_branch(sub, x, y, side, depth + 1, y_cursor)

        for prod in category.products:
            prod_x = x + (side * 140)
            prod_y = y_cursor
            self.graph_canvas.create_line(x, y + 22, prod_x, prod_y - 18, fill="#94a3b8", width=1)
            self._draw_node_box(prod_x, prod_y, prod, is_category=False)
            y_cursor += 56

        return y_cursor

    def _draw_node_box(self, x, y, obj, is_category):
        if is_category:
            fill = "#d9eaf7"
            border = "#2f6f9f"
            title = obj.name
            attrs = ", ".join(sorted(attr.key for attr in obj.attributes))
            subtitle = f"attrs: {attrs}" if attrs else "attrs: -"
        else:
            fill = "#dff7df"
            border = "#2f8f4e"
            title = f"{obj.title} ({obj.code})"
            subtitle = "producto"

        w = 148
        h = 44
        rect = self.graph_canvas.create_rectangle(
            x - w // 2,
            y - h // 2,
            x + w // 2,
            y + h // 2,
            fill=fill,
            outline=border,
            width=2,
        )
        txt = self.graph_canvas.create_text(x, y - 8, text=title, font=("Helvetica", 9, "bold"))
        sub_txt = self.graph_canvas.create_text(x, y + 10, text=subtitle, font=("Helvetica", 8), fill="#334155")

        self.canvas_item_to_obj[rect] = obj
        self.canvas_item_to_obj[txt] = obj
        self.canvas_item_to_obj[sub_txt] = obj

    def _show_variant_dialog(self, product):
        """Muestra dialog para crear variante pidiendo todos los atributos dinámicos."""
        required = product.get_required_dynamic_attrs()
        if not required:
            messagebox.showwarning("Sin atributos", f"El producto '{product.title}' no tiene atributos dinámicos requeridos.")
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Crear variante para {product.title}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)

        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(main_frame, text=f"Producto: {product.title}", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 10))
        tk.Label(main_frame, text="Ingresa valores para cada atributo dinámico:", font=("Arial", 10)).pack(anchor="w", pady=(0, 10))

        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=1, highlightbackground="#ccc")
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        attr_inputs = {}
        for attr in sorted(required, key=lambda a: a.key):
            frame = tk.Frame(scrollable_frame, bg="white")
            frame.pack(fill=tk.X, padx=10, pady=8)

            tk.Label(frame, text=f"{attr.name} ({attr.data_type}):", bg="white", font=("Arial", 9, "bold")).pack(anchor="w")

            if attr.data_type == "enum":
                var = tk.StringVar()
                combo = ttk.Combobox(frame, textvariable=var, state="readonly", width=40, values=attr.enum_values)
                combo.pack(anchor="w", fill=tk.X)
                attr_inputs[attr.key] = var
            elif attr.data_type == "boolean":
                var = tk.StringVar(value="false")
                frame_bool = tk.Frame(frame, bg="white")
                frame_bool.pack(anchor="w")
                tk.Radiobutton(frame_bool, text="Verdadero", variable=var, value="true", bg="white").pack(side=tk.LEFT)
                tk.Radiobutton(frame_bool, text="Falso", variable=var, value="false", bg="white").pack(side=tk.LEFT)
                attr_inputs[attr.key] = var
            else:
                var = tk.StringVar()
                entry = tk.Entry(frame, width=43)
                entry.pack(anchor="w", fill=tk.X)
                entry.bind("<KeyRelease>", lambda e, v=var, w=entry: v.set(w.get()))
                var.set("")
                attr_inputs[attr.key] = var

        canvas.pack(fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=15, pady=(10, 15))

        def on_create():
            mapping = {}
            for key, var in attr_inputs.items():
                value = var.get().strip()
                if not value:
                    messagebox.showerror("Falta valor", f"Debes completar el valor para '{key}'.")
                    return
                mapping[key] = value

            try:
                impls = []
                for attr in required:
                    if attr.key in mapping:
                        typed_value = self._cast_variant_value(attr, mapping[attr.key])
                        if not attr.check_value(typed_value):
                            raise ValueError(f"Valor invalido para '{attr.key}': {mapping[attr.key]}")
                        impls.append(AttributeImplementation(attribute=attr, value=typed_value))

                variant = Variant(attribute_implementations=impls)
                product.add_variant(variant)
                messagebox.showinfo("Exito", f"Variante creada correctamente.")
                dialog.destroy()
                self.refresh_tree()
            except ValueError as e:
                messagebox.showerror("Error del modelo", str(e))

        tk.Button(btn_frame, text="Crear Variante", bg="#4CAF50", fg="white", command=on_create).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)


if __name__ == "__main__":
    app = TreeVisualManager()
    app.mainloop()