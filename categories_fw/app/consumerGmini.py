import tkinter as tk
from tkinter import ttk
import uuid
# Importamos tus clases desde el archivo models.py
# (Asegurate de que tu archivo con las clases se llame models.py)
from models import Category, Product, Attribute, AttributeImplementation, Variant

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor Visual de Árboles (Categorías y Productos)")
        self.geometry("800x600")

        # Estado interno de la app
        # Creamos una categoría raíz invisible para colgar todo
        self.root_category = Category(name="Catálogo Principal")
        self.node_map = {} # Mapea ID del árbol de la UI -> Objeto (Category o Product)
        self.name_map = {} # Mapea Nombre del nodo -> Objeto (útil para buscar destinos al mover)

        self.setup_ui()
        self.refresh_tree()

    def setup_ui(self):
        # --- PANEL SUPERIOR: ÁRBOL VISUAL ---
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # --- PANEL INFERIOR: BARRA DE ACCIONES (CRUD) ---
        action_frame = tk.LabelFrame(self, text="Panel de Acciones (Seleccioná un nodo en el árbol arriba)", padx=10, pady=10)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # Controles
        tk.Label(action_frame, text="Acción:").grid(row=0, column=0, padx=5, pady=5)
        self.action_var = tk.StringVar(value="Crear Subcategoría")
        acciones = ["Crear Subcategoría", "Crear Producto", "Editar Nombre", "Mover a...", "Eliminar"]
        self.action_combo = ttk.Combobox(action_frame, textvariable=self.action_var, values=acciones, state="readonly", width=18)
        self.action_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(action_frame, text="Valor/Destino:").grid(row=0, column=2, padx=5, pady=5)
        self.input_entry = tk.Entry(action_frame, width=25)
        self.input_entry.grid(row=0, column=3, padx=5, pady=5)
        self.input_entry.insert(0, "Escribí acá...")

        self.btn_execute = tk.Button(action_frame, text="Ejecutar", bg="#4CAF50", fg="white", command=self.execute_action)
        self.btn_execute.grid(row=0, column=4, padx=15, pady=5)

        # --- PANEL DE ESTADO Y ERRORES ---
        self.status_label = tk.Label(self, text="Listo.", fg="gray", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def refresh_tree(self):
        """Limpia y redibuja todo el árbol leyendo el estado actual de los objetos."""
        self.tree.delete(*self.tree.get_children())
        self.node_map.clear()
        self.name_map.clear()
        
        # Mapeamos la raíz
        root_id = "root"
        self.node_map[root_id] = self.root_category
        self.name_map[self.root_category.name] = self.root_category
        
        self.tree.insert("", "end", root_id, text=f"📁 {self.root_category.name}", open=True)
        self._populate_tree(root_id, self.root_category)

    def _populate_tree(self, parent_ui_id, category_obj):
        # 1. Dibujar subcategorías
        for subcat in category_obj.subcategories:
            node_id = str(uuid.uuid4())
            self.node_map[node_id] = subcat
            self.name_map[subcat.name] = subcat
            
            self.tree.insert(parent_ui_id, "end", node_id, text=f"📁 {subcat.name}", open=True)
            self._populate_tree(node_id, subcat) # Recursivo
            
        # 2. Dibujar productos
        for prod in category_obj.products:
            node_id = str(uuid.uuid4())
            self.node_map[node_id] = prod
            self.name_map[prod.title] = prod
            
            self.tree.insert(parent_ui_id, "end", node_id, text=f"📦 {prod.title} (Cod: {prod.code})")

    def show_error(self, message):
        self.status_label.config(text=f"❌ ERROR: {message}", fg="red")

    def show_success(self, message):
        self.status_label.config(text=f"✅ {message}", fg="green")

    def execute_action(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.show_error("Por favor, seleccioná un nodo en el árbol primero.")
            return

        ui_node_id = selected_item[0]
        obj = self.node_map.get(ui_node_id)
        action = self.action_var.get()
        user_input = self.input_entry.get().strip()

        if not user_input:
            self.show_error("El campo Valor/Destino no puede estar vacío.")
            return

        # Vaciamos la consola visual de estado
        self.status_label.config(text="Procesando...", fg="black")

        try:
            # --- CREAR SUBCATEGORÍA ---
            if action == "Crear Subcategoría":
                if not isinstance(obj, Category):
                    raise ValueError("Solo podés agregar subcategorías a una Categoría.")
                
                nueva_cat = Category(name=user_input)
                # ¡Acá consume tu modelo! Si el modelo falla por exclusión, tira el error y salta al except.
                obj.add_subcategory(nueva_cat)
                self.show_success(f"Categoría '{user_input}' creada exitosamente.")

            # --- CREAR PRODUCTO ---
            elif action == "Crear Producto":
                if not isinstance(obj, Category):
                    raise ValueError("Solo podés agregar productos a una Categoría.")
                
                nuevo_prod = Product(code=user_input[:3].upper(), title=user_input, price=0.0, description="", brand="", category=obj)
                obj.add_product(nuevo_prod)
                self.show_success(f"Producto '{user_input}' creado exitosamente.")

            # --- EDITAR NOMBRE ---
            elif action == "Editar Nombre":
                if isinstance(obj, Category):
                    old_name = obj.name
                    obj.name = user_input
                    self.show_success(f"Categoría '{old_name}' renombrada a '{user_input}'.")
                elif isinstance(obj, Product):
                    obj.title = user_input
                    self.show_success("Nombre del producto actualizado.")

            # --- ELIMINAR ---
            elif action == "Eliminar":
                if ui_node_id == "root":
                    raise ValueError("No podés eliminar el Catálogo Principal.")
                
                if isinstance(obj, Category):
                    padre = obj.father_categorie
                    if padre and obj in padre.subcategories:
                        padre.subcategories.remove(obj)
                elif isinstance(obj, Product):
                    padre = obj.category
                    if padre and obj in padre.products:
                        padre.products.remove(obj)
                        padre._product_codes.discard(obj.code)
                self.show_success("Nodo eliminado correctamente.")

            # --- MOVER A (Drag & Drop lógico) ---
            elif action == "Mover a...":
                destino = self.name_map.get(user_input)
                
                if not destino:
                    raise ValueError(f"No existe un nodo con el nombre '{user_input}'. Revisá cómo está escrito.")
                if not isinstance(destino, Category):
                    raise ValueError("Solo podés mover elementos hacia una Categoría.")
                if obj == destino:
                    raise ValueError("No podés mover un nodo dentro de sí mismo.")
                
                # Desvincular del padre actual y vincular al nuevo
                if isinstance(obj, Category):
                    padre_actual = obj.father_categorie
                    # Validaciones nativas de tu models.py (ciclos, hijos exclusivos)
                    destino._check_no_cycle(obj) 
                    destino._check_exclusive_children('subcategory')
                    
                    if padre_actual:
                        padre_actual.subcategories.remove(obj)
                    destino.add_subcategory(obj)
                    
                elif isinstance(obj, Product):
                    padre_actual = obj.category
                    destino._check_exclusive_children('product')
                    
                    if padre_actual:
                        padre_actual.products.remove(obj)
                        padre_actual._product_codes.discard(obj.code)
                        
                    destino.add_product(obj)
                    obj.category = destino

                self.show_success(f"Nodo movido exitosamente hacia '{destino.name}'.")

            # Finalmente, si todo salió bien, redibujamos el árbol para reflejar tu models.py
            self.refresh_tree()

        # ACA ESTÁ LA MAGIA: Tu models tira ValueError por las validaciones lógicas.
        # Tkinter lo ataja e imprime lo que dice el modelo literalmente.
        except ValueError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Error inesperado: {str(e)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()