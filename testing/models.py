from typing import List
#modelo de jerarquia de atributos
DataTypes = ["text", "number", "boolean", "enum"]
# Buenas parcticas locales
# text y number son simbre de producto
# boolean es siempre de variante
# enum puede ser de producto o de variante, si es de producto se muestra como info, si es de variante se muestra como una opcion para elegir.

class Attribute:
    def __init__(self, 
        key:str, 
        name:str, 
        data_type:str,
        id:int=None, 
        is_static:bool=False
        ):
        self.id = id
        self.key = key
        self.name = name
        self.data_type = data_type
        self.is_static = is_static # el atributo estatico es aquel que se muestra como informacion del producto.
        self.enum_values = [] # si el tipo de dato es enum, esta lista va a contener los valores posibles, va a ser una lista de objetos EnumValue

    def add_enum_value(self, value): # esto es una class pero en el repositorio va a mantener los estados y actualizar las lineas.
        if self.data_type != "enum":
            raise ValueError("El atributo no es de tipo enum.")
        if value not in self.enum_values:
            self.enum_values.append(value)
        else:
            raise ValueError("El valor ya existe en la lista de valores posibles.")

    def check_value(self, value):
        if self.data_type == "text":
            return isinstance(value, str)
        elif self.data_type == "number":
            return isinstance(value, (int, float))
        elif self.data_type == "boolean":
            return isinstance(value, bool)
        elif self.data_type == "enum":
            return value in self.enum_values
        else:
            raise ValueError("Tipo de dato no reconocido.")

    def __eq__(self, other):
        if not isinstance(other, Attribute):
            return NotImplemented
        return self.id == other.id if self.id is not None else self is other

    def __hash__(self):
        return hash(self.id) if self.id is not None else id(self)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "data_type": self.data_type,
            "is_static": self.is_static,
            "enum_values": [
                ev.to_json() if hasattr(ev, "to_json") else ev
                for ev in self.enum_values
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        attr = cls(
            key=data.get("key"),
            name=data.get("name"),
            data_type=data.get("data_type"),
            id=data.get("id"),
            is_static=data.get("is_static", False)
        )
        for ev in data.get("enum_values", []):
            attr.enum_values.append(ev)
        return attr

class Attribute_factory:
    _instances: dict = {}

    @classmethod
    def get(cls, key: str, name: str, data_type: str, id: int = None, is_static: bool = False) -> "Attribute":
        if key not in cls._instances:
            cls._instances[key] = Attribute(key=key, name=name, data_type=data_type, id=id, is_static=is_static)
        return cls._instances[key]

    @classmethod
    def clear(cls):
        cls._instances.clear()

class AttributeImplementation: # esta clase representa la implementacion de un atributo, lo va a contener toda variant que le competa
    def __init__(self, attribute:Attribute, value:str, id:int = None):
        self.id = id
        self.attribute = attribute # objeto Attribute referencia.
        self.value = value

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "attribute": self.attribute.to_json() if self.attribute else None,
            "value": self.value
        }

    @classmethod
    def from_json(cls, data: dict):
        attribute_data = data.get("attribute")

        attribute = (
            Attribute.from_json(attribute_data)
            if isinstance(attribute_data, dict)
            else attribute_data
        )

        return cls(
            attribute=attribute,
            value=data.get("value"),
            id=data.get("id")
        )

class Category:
    def __init__(self,
        name:str,
        id:int=None,
        attributes: list[Attribute] = None,
        subcategories: list[Category] = None,
        father_categorie: Category = None,
        products: list[Product] = None
        ):
        self.id = id
        self.name = name
        self.attributes = attributes or []
        self._attribute_keys = {a.key for a in self.attributes}
        self.subcategories = subcategories or []
        self.father_categorie = father_categorie or None
        self.products = products or []
        self._product_codes = {p.code for p in self.products}

    # ── Validadores ───────────────────────────────────────────────────────────

    def _check_no_cycle(self, candidate_child: 'Category') -> None:
        """Raises ValueError si candidate_child ya es ancestro de self (crearia ciclo)."""
        node = self
        while node is not None:
            if node is candidate_child:
                raise ValueError(
                    f"Ciclo detectado: '{candidate_child.name}' ya es ancestro de '{self.name}'."
                )
            node = node.father_categorie

    def _check_exclusive_children(self, adding: str) -> None:
        """
        adding: 'subcategory' | 'product'
        Raises ValueError si agregar ese tipo mezclaría hijos de distinto tipo.
        """
        if adding == 'subcategory' and self.products:
            raise ValueError(
                f"'{self.name}' ya tiene productos, no puede tener subcategorias."
            )
        if adding == 'product' and self.subcategories:
            raise ValueError(
                f"'{self.name}' ya tiene subcategorias, no puede tener productos."
            )

    # ── Mutaciones seguras ────────────────────────────────────────────────────

    def add_subcategory(self, cat: 'Category') -> None:
        self._check_exclusive_children('subcategory')
        self._check_no_cycle(cat)
        self.subcategories.append(cat)
        cat.father_categorie = self

    def add_product(self, product: 'Product') -> None:
        self._check_exclusive_children('product')
        product._check_product_completeness()
        self.products.append(product)
        self._product_codes.add(product.code)

    def set_father(self, father: 'Category | None') -> None:
        if father is not None:
            father._check_no_cycle(self)
        self.father_categorie = father

    # ── Eventos de padre ──────────────────────────────────────────────────────
    # Todos retornan el impacto sin mutar estado.
    # El llamador revisa el resultado y luego llama set_father / add_subcategory.

    def impact_on_add_father(self, new_father: 'Category') -> list[tuple[set, list]]:
        """E1: que productos se ven impactados si self gana new_father como padre."""
        new_father._check_no_cycle(self)
        new_inherited = (new_father.get_ancestor_attrs() | set(new_father.attributes)) - set(self.attributes)
        return self.compute_impact(new_inherited)

    def impact_on_remove_father(self) -> list[tuple[set, list]]:
        """E3: que productos pierden atributos si self pierde su padre actual.
        Debe llamarse ANTES de mutar father_categorie."""
        return self.compute_impact(self.get_effective_inherited_attrs())

    def impact_on_change_father(self, new_father: 'Category') -> tuple[list, list]:
        """E2: delta neto al cambiar de padre.
        Compara lo que se hereda actualmente vs lo que se heredaría con new_father.
        Si un attr sigue llegando por otra rama (ej: hermano que también hereda del abuelo),
        no aparece en el delta — no hay impacto real.
        Retorna (impact_out, impact_in)."""
        new_father._check_no_cycle(self)
        current_inherited = self.get_effective_inherited_attrs()
        new_inherited = (new_father.get_ancestor_attrs() | set(new_father.attributes)) - set(self.attributes)
        losing  = current_inherited - new_inherited
        gaining = new_inherited - current_inherited
        impact_out = self.compute_impact(losing)  if losing  else []
        impact_in  = self.compute_impact(gaining) if gaining else []
        return impact_out, impact_in

    def impact_on_add_attribute(self, attr: 'Attribute') -> list[tuple[set, list]]:
        """E4: que productos deben implementar attr porque self lo acaba de agregar."""
        return self.compute_impact({attr})

    def impact_on_remove_attribute(self, attr: 'Attribute') -> list[tuple[set, list]]:
        """E5: que productos deben quitar la implementacion de attr porque self lo elimino.
        Si una subcategoria descendiente define el mismo attr, sus productos no se ven afectados.
        Si un ancestro de self ya define attr, el attr seguira propagandose — sin impacto."""
        if attr in self.get_ancestor_attrs():
            return []
        return self.compute_impact({attr})

    def get_ancestor_attrs(self) -> set:
        """Sube por father_categorie acumulando todos los atributos de la ascendencia."""
        attrs = set()
        current = self.father_categorie
        while current is not None:
            attrs.update(current.attributes)
            current = current.father_categorie
        return attrs

    def get_effective_inherited_attrs(self) -> set:
        """Attrs que realmente llegan a self desde arriba: ancestros menos lo que self ya define."""
        return self.get_ancestor_attrs() - set(self.attributes)

    def get_full_attr_set(self) -> set:
        """Todos los atributos visibles en este nivel: propios + los que llegan de ancestros."""
        return self.get_ancestor_attrs() | set(self.attributes)

    def compute_impact(self, attrs: set) -> list[tuple[set, list]]:
        """
        Dado un conjunto de atributos, retorna una lista de pares (attrs_sobrevivientes, productos).
        Cada par representa los atributos que llegan a impactar a ese grupo de productos
        tras filtrar lo que las ramas intermedias ya definen.
        Sirve tanto para agregar como para quitar atributos: el llamador decide que hacer con el resultado.
        """
        if not attrs:
            return []
        return self._descend_impact(set(attrs))

    def _descend_impact(self, attrs: set) -> list[tuple[set, list]]:
        if self.products:
            return [(attrs, list(self.products))]
        results = []
        for sub in self.subcategories:
            sub_remaining = attrs - set(sub.attributes)
            if sub_remaining:
                results.extend(sub._descend_impact(sub_remaining))
        return results



class Variant: # hereda todas las propiedades por asociacion con el producto, y implementa obligatoriamente los atributos del producto y de la categoria.
    def __init__(self, attribute_implementations:List[AttributeImplementation]=None, id:int=None,):
        self.id = id
        self.attribute_implementations = attribute_implementations or [] # lista de objetos AttributeImplementation, implementamos atributos no staticos, es decir, los que no se muestran como informacion del producto, sino que son opciones para elegir.

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "attribute_implementations": [
                ai.to_json() if hasattr(ai, "to_json") else ai
                for ai in self.attribute_implementations
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        attribute_implementations = [
            AttributeImplementation.from_json(ai) if isinstance(ai, dict) else ai
            for ai in data.get("attribute_implementations", [])
        ]

        return cls(
            attribute_implementations=attribute_implementations,
            id=data.get("id")
        )

class Product:
    def __init__(self, 
    code:str, 
    title:str, 
    price:float, 
    description:str,
    brand:str, 
    id:int = None, 
    category: Category = None,
    attributes_implementations: List[AttributeImplementation] = None, 
    variants: List[Variant] = None
    ):
        #agregar los otros ifs de los obligatorios
        if category is None:
            raise ValueError("Product must have a category") 
        
        self.id = id
        self.code = code
        self.title = title
        self.price = price
        self.description = description
        self.brand = brand
        self.category = category
        self.attributes_implementations = attributes_implementations or []
        self._impl_keys = {i.attribute.key for i in self.attributes_implementations}
        self.variants = variants or []

    def _check_product_completeness(self) -> None:
        """Valida que el producto implemente exactamente los atributos estáticos
        que exige su categoría (ni faltan ni sobran)."""
        required    = {a for a in self.category.get_full_attr_set() if a.is_static}
        implemented = {impl.attribute for impl in self.attributes_implementations}
        missing = required - implemented
        extra   = implemented - required
        errors  = []
        if missing:
            errors.append(f"faltan: {sorted(a.key for a in missing)}")
        if extra:
            errors.append(f"de mas: {sorted(a.key for a in extra)}")
        if errors:
            raise ValueError(f"Producto incompleto — {', '.join(errors)}")

    def _current_static_attrs(self) -> set:
        return {impl.attribute for impl in self.attributes_implementations if impl.attribute.is_static}

    def _current_dynamic_attrs(self) -> set:
        return {impl.attribute for impl in self.attributes_implementations if not impl.attribute.is_static}

    def impact_on_change_category(self, new_category: 'Category') -> tuple[set, set]:
        """E6: delta de atributos al mover el producto a new_category (estaticos y dinamicos).
        Compara lo que exige la categoria actual vs lo que exige la nueva.
        Retorna (to_add, to_remove).
        Debe llamarse ANTES de mutar self.category."""
        current_required = self.category.get_full_attr_set()
        new_required     = new_category.get_full_attr_set()
        return new_required - current_required, current_required - new_required

    # ── E7: variantes ─────────────────────────────────────────────────────────

    def get_required_dynamic_attrs(self) -> set:
        """Attrs dinamicos (is_static=False) que toda variante de este producto debe implementar."""
        return {a for a in self.category.get_full_attr_set() if not a.is_static}

    def _variant_signature(self, variant: 'Variant') -> frozenset:
        return frozenset(
            (impl.attribute.key, impl.value)
            for impl in variant.attribute_implementations
        )

    def _check_variant_completeness(self, variant: 'Variant') -> None:
        required    = self.get_required_dynamic_attrs()
        implemented = {impl.attribute for impl in variant.attribute_implementations}
        missing = required - implemented
        extra   = implemented - required
        errors  = []
        if missing:
            errors.append(f"faltan: {sorted(a.key for a in missing)}")
        if extra:
            errors.append(f"de mas: {sorted(a.key for a in extra)}")
        if errors:
            raise ValueError(f"Variante invalida — {', '.join(errors)}")

    def _check_variant_uniqueness(self, variant: 'Variant') -> None:
        new_sig = self._variant_signature(variant)
        for existing in self.variants:
            if self._variant_signature(existing) == new_sig:
                raise ValueError("Ya existe una variante con la misma combinacion de valores.")

    def add_variant(self, variant: 'Variant') -> None:
        """E7a: agrega una variante validando completitud y unicidad."""
        self._check_variant_completeness(variant)
        self._check_variant_uniqueness(variant)
        self.variants.append(variant)

    def remove_variant(self, variant: 'Variant') -> None:
        """E7b: quita una variante del producto."""
        if variant not in self.variants:
            raise ValueError("La variante no pertenece a este producto.")
        self.variants.remove(variant)

    def clean_variants_after_attr_removal(self, removed_attrs: set) -> tuple[int, int]:
        """E8: limpia las variantes luego de que ciertos attrs dejaron de aplicar.
        1. Quita las implementaciones de removed_attrs de cada variante.
        2. Elimina variantes que queden sin implementaciones.
        3. Elimina variantes duplicadas que surjan tras la limpieza (conserva la primera).
        Retorna (vaciadas_eliminadas, duplicadas_eliminadas).
        Llamar DESPUÉS de mutar self.category si el cambio fue por E6."""
        keys = {a.key for a in removed_attrs}

        for var in self.variants:
            var.attribute_implementations = [
                impl for impl in var.attribute_implementations
                if impl.attribute.key not in keys
            ]

        before = len(self.variants)
        self.variants = [v for v in self.variants if v.attribute_implementations]
        empty_removed = before - len(self.variants)

        seen: set[frozenset] = set()
        unique = []
        for v in self.variants:
            sig = self._variant_signature(v)
            if sig not in seen:
                seen.add(sig)
                unique.append(v)
        dup_removed = len(self.variants) - len(unique)
        self.variants = unique

        return empty_removed, dup_removed
