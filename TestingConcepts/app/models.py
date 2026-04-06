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
        self.attributes = attributes or [] # lista de objetos Attribute
        self._attribute_keys = {a.key for a in self.attributes}
        self.subcategories = subcategories or [] # lista de subcategorias
        self.father_categorie = father_categorie or None # categoria padre
        self.products = products or [] # lista de productos que estan con esta categoria
        self._product_codes = {p.code for p in self.products}

    def get_attributes(self) -> list: # get recursivo, va a traer toda la rama genialogica y devolver atributos.
        attributes = self.attributes.copy()
        if (self.father_categorie):
            attributes += self.father_categorie.get_attributes()
        return attributes

    def get_attribute_keys(self) -> set: # version recursiva que devuelve solo los keys
        keys = {a.key for a in self.attributes}
        if self.father_categorie:
            keys |= self.father_categorie.get_attribute_keys()
        return keys

    # busca recursivamente para arriba si esta un attibute espesifico
    def _add_attribute_look_up(self,attribute:Attribute):
        #si lo tengo retorno true
        if attribute.key in self._attribute_keys:
            return True
        #si no tengo padre y no lo tengo retorno false
        if self.father_categorie == None:
            return False
        #si no lo tengo pero tengo padre se lo piedo a mi padre y retorno lo que me diga
        return self.father_categorie._add_attribute_look_up(attribute=attribute)

    # busca para a bajo el attr
    def _add_attribute_look_down(self, attribute:Attribute):
        #miro que soy, si una categoria padre de categorias o de productos
        # lo hago recursivo en padre de categoria, y lo hago retornate en padre de productos
        # chequeo que tenga el attributo y corto busqueda
        if attribute.key in self._attribute_keys:
            return []
        # si no tengo el attributo busco hijos
        products = []
        if len(self.subcategories) > 0:
            for c in self.subcategories: #recorremos todas las categorias hijo llamando recursivamente a sus busquedas
                products.extend(c._add_attribute_look_down(attribute=attribute))
            return products
        if len(self.products) > 0:
            return list(self.products)
        # si no hay nada retornamos nada
        return []
            
    #retorna productos impactados pendiendes de implementacion
    def _add_attribute_product_check_family_impact(self,
        attribute:Attribute,
        ):
        #miramos si aca o arriba esta el attributo
        if self._add_attribute_look_up(attribute=attribute):
            # si esta le respondemos que no necesita nada.
            return None
        # si no hay nadie que lo cubra miramos para abajo a quien perjudicamos
        products = self._add_attribute_look_down(attribute=attribute)
        products_in_risk = []
        for p in products:
            if not p.is_attribute_in(attribute=attribute):
                products_in_risk.append(p)
        return products_in_risk

    #retorna variantes impactadas pendientes de implementacion
    # helper para "add_dinamic_attribute"
    def _add_attribute_variant_impact_check(self,attribute:Attribute,product_variant_implementations):
        #[{"product_id": id, "variants": [{"variant_id": id, "value": value}]}]
        impact = self._add_attribute_product_check_family_impact(attribute=attribute)
        # algun ancestro ya lo cubre, nada que hacer
        if impact is None:
            return None

        # no hay productos perjudicados, agregamos libre
        if not impact:
            if attribute.key not in self._attribute_keys:
                self.attributes.append(attribute)
                self._attribute_keys.add(attribute.key)
            return {}

        #si hay impacto
        # construimos set de product_ids en riesgo y de los que llegan, chequeando duplicados
        impact_product_ids = {p.id for p in impact}
        impl_product_ids = set()
        for entry in product_variant_implementations:
            pid = entry["product_id"]
            if pid in impl_product_ids:
                return impact  # product_id duplicado
            impl_product_ids.add(pid)

        # deben cubrir exactamente los mismos productos
        if impact_product_ids != impl_product_ids:
            return impact

        impact_map = {p.id: p for p in impact}
        pending = []  # (variant, AttributeImplementation) a aplicar si todo matchea

        for entry in product_variant_implementations:
            product = impact_map[entry["product_id"]]
            product_variant_ids = {v.id for v in product.variants}
            variants_map = {v.id: v for v in product.variants}

            # chequeamos duplicados de variant_id y construimos set de los que llegan
            entry_variant_ids = set()
            for v_entry in entry["variants"]:
                vid = v_entry["variant_id"]
                if vid in entry_variant_ids:
                    return impact  # variant_id duplicado
                entry_variant_ids.add(vid)

            # deben cubrir exactamente las variantes del producto
            if product_variant_ids != entry_variant_ids:
                return impact

            # chequeamos valores y acumulamos cambios pendientes
            for v_entry in entry["variants"]:
                try:
                    if not attribute.check_value(v_entry["value"]):
                        return impact
                except ValueError:
                    return impact
                impl = AttributeImplementation(attribute=attribute, value=v_entry["value"])
                pending.append((variants_map[v_entry["variant_id"]], impl))

        return pending

    # pide variantes
    def add_dinamic_attribute(self,
        attribute:Attribute,
        product_variant_implementations):

        if attribute.is_static:
            raise ValueError("El attributo que se quiere incertar es estatico")

        pending = self._add_attribute_variant_impact_check(attribute=attribute, product_variant_implementations=product_variant_implementations)

        # ancestro cubre o sin impacto (atributo ya agregado dentro de add_impact_check)
        if pending is None or isinstance(pending, dict):
            return {}

        # validacion fallo: pending es la lista de productos en riesgo
        if pending and isinstance(pending[0], Product):
            return pending

        # todo matcheó, aplicamos
        for variant, impl in pending:
            variant.attribute_implementations.append(impl)

        self.attributes.append(attribute)
        self._attribute_keys.add(attribute.key)
        return {}

    # helper para "add_static_attribute"
    def _add_static_impact_check(self, attribute:Attribute, implementations):
        #[{"product_id": id, "value": value}]
        impact = self._add_attribute_product_check_family_impact(attribute=attribute)

        if impact is None:
            return None

        if not impact:
            if attribute.key not in self._attribute_keys:
                self.attributes.append(attribute)
                self._attribute_keys.add(attribute.key)
            return {}

        # verificamos cobertura exacta de productos, sin duplicados
        impact_product_ids = {p.id for p in impact}
        impl_product_ids = set()
        for entry in implementations:
            pid = entry["product_id"]
            if pid in impl_product_ids:
                return impact  # product_id duplicado
            impl_product_ids.add(pid)

        if impact_product_ids != impl_product_ids:
            return impact

        impact_map = {p.id: p for p in impact}
        pending = []  # (product, AttributeImplementation)

        for entry in implementations:
            product = impact_map[entry["product_id"]]
            try:
                if not attribute.check_value(entry["value"]):
                    return impact
            except ValueError:
                return impact
            impl = AttributeImplementation(attribute=attribute, value=entry["value"])
            pending.append((product, impl))

        return pending
    
    # pide productos
    def add_static_attribute(self, attribute:Attribute, implementations):
        #[{"product_id": id, "value": value}]
        if not attribute.is_static:
            raise ValueError("El atributo que se quiere insertar no es estatico")

        pending = self._add_static_impact_check(attribute=attribute, implementations=implementations)

        if pending is None or isinstance(pending, dict):
            return {}

        if pending and isinstance(pending[0], Product):
            return pending

        for product, impl in pending:
            product.attributes_implementations.append(impl)
            product._impl_keys.add(impl.attribute.key)

        self.attributes.append(attribute)
        self._attribute_keys.add(attribute.key)
        return {}

    # retorna true si un ancestro lo tiene.
    @staticmethod
    def _del_attribute_look_up(category:Category,attribute:Attribute):
        if attribute.key in category._attribute_keys:
            return True
        if category.father_categorie is None:
            return False
        return Category._del_attribute_look_up(category=category.father_categorie,attribute=attribute)

    #retorna productos perjudicados
    @staticmethod
    def _del_attribute_look_down(category:Category,attribute:Attribute):
        products = []
        # verifica si el que esta lo tiene retorna [] si lo tiene
        if attribute.key in category._attribute_keys:
            return []
        # verifica que si tene hijos categorias y entra en un for sumador recursivo
        if len(category.subcategories) > 0:
            for c in category.subcategories:
                products.extend(Category._del_attribute_look_down(c,attribute=attribute))        
            return products
        # verifica si tiene productos y un for sumador uno a uno de los que lo tengan
        if len(category.products)>0:
            for p in category.products:
                if attribute.key not in p._attribute_keys: # producto que no tiene el attrto
                    products.append(p)
            return products
        return []

    # retorna todos los productos perjudicados
    def del_attribute_check_family_impact(self,attribute:Attribute):
        # tiene que verificar que no perjudique productos, es decir, ancestros tienen que tener ese atributo, o todos los herederos tenerlo propiamente. productos retorna perjudicados si los hay.
        products = []
        #si algun ancestro lo tiene
        if self.father_categorie and Category._del_attribute_look_up(category=self.father_categorie,attribute=attribute):
            return products
        # verifica si tiene productos y un for sumador uno a uno de los que lo tengan
        if len(self.products)>0:
            for p in self.products:
                if attribute.key not in p._attribute_keys:
                    products.append(p)
            return products
        # si tiene hijo categoria
        for c in self.subcategories:
            products.extend(Category._del_attribute_look_down(c,attribute=attribute))
        return products
    
    #delete_all significa que elimina todos las implementaciones de ese attributo en los afectados.
    #si esta en 0 no hace nada
    #si esta en 1 elimina implementaciones
    #si esta en 2 injecta ese attributo en los productos afectados
    def del_attribute(self, attribute:Attribute,delete_opt:int=0):
        # 1. calcular productos impactados
        products: List[Product] = self.del_attribute_check_family_impact(attribute=attribute).copy()

        # 2. sin impacto, eliminamos directo
        if not products:
            self._attribute_keys.discard(attribute.key)
            self.attributes = [a for a in self.attributes if a.key != attribute.key]
            return []

        # 3. delete_opt=0: solo avisa, no modifica nada
        if delete_opt == 0:
            return products

        # 4. delete_opt=1: elimina implementaciones segun tipo de atributo
        if delete_opt == 1:
            for p in products:
                if attribute.is_static:
                    p.attributes_implementations = [i for i in p.attributes_implementations if i.attribute.key != attribute.key]
                    p._impl_keys.discard(attribute.key)
                else:
                    for variant in p.variants:
                        variant.attribute_implementations = [i for i in variant.attribute_implementations if i.attribute.key != attribute.key]
            self._attribute_keys.discard(attribute.key)
            self.attributes = [a for a in self.attributes if a.key != attribute.key]
            return []

        # 5. delete_opt=2: inyecta la definicion del atributo en los productos, mantiene implementaciones
        if delete_opt == 2:
            for p in products:
                p.attributes.append(attribute)
                p._attribute_keys.add(attribute.key)
            self._attribute_keys.discard(attribute.key)
            self.attributes = [a for a in self.attributes if a.key != attribute.key]
            return []

    # handler para change_categorie_father
    @staticmethod
    def change_lookup_for_attributes(init_categorie: "Category") -> set:
        # buscamos desde el que estamos todas las categorias para arriba y devolvemos set asi no hay replica
        attributes = set(init_categorie.attributes)
        if init_categorie.father_categorie:
            attributes |= Category.change_lookup_for_attributes(init_categorie.father_categorie)
        return attributes

    # vamos a cambiar de en vez de add_categorie, a change categorie father
    # resuelve menjor y cumple lo mismo
    # refactorizar en varios metodos distintos.
    def change_categorie_father(self, father_categorie: Category, implementations, del_option: int = 0):
        # del_option controla que hacer con los atributos que el padre anterior aportaba y el nuevo no:
        # 0 = si hay impacto, retorna el mapa de huerfanos sin modificar nada
        # 1 = inyecta los atributos huerfanos en self para que los descendientes los sigan heredando
        # 2 = elimina las implementaciones de los atributos huerfanos en los productos afectados

        # 1. validar que no se forme un ciclo
        cursor = father_categorie
        while cursor is not None:
            if cursor is self:
                raise ValueError("No se puede asignar un descendiente como padre: se formaría un ciclo.")
            cursor = cursor.father_categorie

        # 2. no puede tener productos si quiere tener categorias
        if len(father_categorie.products) > 0:
            raise ValueError("No puede tener productos si quiere poner categorias")

        # 3. atributos del nuevo padre hacia arriba sin replica
        father_attributes = Category.change_lookup_for_attributes(father_categorie)
        father_attr_keys = {a.key for a in father_attributes}

        # 4. atributos del padre anterior que dejan de estar cubiertos (huerfanos)
        old_orphan_attrs = []
        if self.father_categorie:
            old_attrs = Category.change_lookup_for_attributes(self.father_categorie)
            old_orphan_attrs = [
                a for a in old_attrs
                if a.key not in father_attr_keys and a.key not in self._attribute_keys
            ]

        # 5. calcular impacto de atributos huerfanos
        # {attr: [products]} — productos que tienen implementacion del attr y la perderan
        orphan_impact = {}
        for attr in old_orphan_attrs:
            affected = [p for p in self._add_attribute_look_down(attr) if attr.key in p._impl_keys]
            if affected:
                orphan_impact[attr] = affected

        # 6. si del_option=0 y hay impacto de huerfanos, retornar sin modificar nada
        if del_option == 0 and orphan_impact:
            return orphan_impact

        # 7. impacto de atributos nuevos en descendientes, separado por tipo
        # static_impact_map:  {attr: [product, ...]}
        # dynamic_impact_map: {attr: [(product, [{"variant_id": id, "value": None}, ...]), ...]}
        static_impact_map = {}
        dynamic_impact_map = {}
        for attr in father_attributes:
            impacted = [p for p in self._add_attribute_look_down(attribute=attr) if not p.is_attribute_in(attr)]
            if not impacted:
                continue
            if attr.is_static:
                static_impact_map[attr] = impacted
            else:
                dynamic_impact_map[attr] = [
                    (product, [{"variant_id": v.id, "value": None} for v in product.variants])
                    for product in impacted
                ]

        # 8. validar implementations para atributos nuevos segun tipo
        # estaticos:  {attr_key: [(product_id, value), ...]}
        # dinamicos:  {attr_key: [(product_id, [{"variant_id": id, "value": value}, ...]), ...]}
        impact_map = {**static_impact_map, **dynamic_impact_map}  # union para retornar en caso de error
        if static_impact_map or dynamic_impact_map:
            for attr, products in static_impact_map.items():
                impl_entries = implementations.get(attr.key)
                if not impl_entries:
                    return impact_map  # falta el atributo entero
                impl_product_map = {pid: value for pid, value in impl_entries}
                for product in products:
                    value = impl_product_map.get(product.id)
                    if value is None:
                        return impact_map  # falta el producto
                    try:
                        if not attr.check_value(value):
                            return impact_map
                    except ValueError:
                        return impact_map

            for attr, product_entries in dynamic_impact_map.items():
                impl_entries = implementations.get(attr.key)
                if not impl_entries:
                    return impact_map  # falta el atributo entero
                impl_product_map = {pid: variants for pid, variants in impl_entries}
                for product, variant_slots in product_entries:
                    impl_variants = impl_product_map.get(product.id)
                    if impl_variants is None:
                        return impact_map  # falta el producto
                    impl_variant_map = {v["variant_id"]: v["value"] for v in impl_variants}
                    for slot in variant_slots:
                        value = impl_variant_map.get(slot["variant_id"])
                        if value is None:
                            return impact_map  # falta la variante
                        try:
                            if not attr.check_value(value):
                                return impact_map
                        except ValueError:
                            return impact_map

        # 9. todo validado — aplicamos implementaciones de atributos nuevos segun tipo
        if static_impact_map or dynamic_impact_map:
            for attr, products in static_impact_map.items():
                impl_entries = implementations.get(attr.key)
                impl_product_map = {pid: value for pid, value in impl_entries}
                for product in products:
                    impl = AttributeImplementation(attribute=attr, value=impl_product_map[product.id])
                    product.attributes_implementations.append(impl)
                    product._impl_keys.add(attr.key)

            pending = []
            for attr, product_entries in dynamic_impact_map.items():
                impl_entries = implementations.get(attr.key)
                impl_product_map = {pid: variants for pid, variants in impl_entries}
                for product, variant_slots in product_entries:
                    impl_variants = impl_product_map[product.id]
                    impl_variant_map = {v["variant_id"]: v["value"] for v in impl_variants}
                    variants_map = {v.id: v for v in product.variants}
                    for slot in variant_slots:
                        variant = variants_map[slot["variant_id"]]
                        impl = AttributeImplementation(attribute=attr, value=impl_variant_map[slot["variant_id"]])
                        pending.append((variant, impl))
            for variant, impl in pending:
                variant.attribute_implementations.append(impl)

        # 10. desvincular del padre anterior
        if self.father_categorie:
            self.father_categorie.subcategories = [
                c for c in self.father_categorie.subcategories if c is not self
            ]

        # 11. manejar atributos huerfanos segun del_option
        if del_option == 1:
            # inyecta los huerfanos en self para que los descendientes los sigan heredando
            for attr in old_orphan_attrs:
                if attr.key not in self._attribute_keys:
                    self.attributes.append(attr)
                    self._attribute_keys.add(attr.key)
        elif del_option == 2:
            # elimina las implementaciones huerfanas de los productos afectados
            for attr, products in orphan_impact.items():
                for product in products:
                    if attr.is_static:
                        product.attributes_implementations = [
                            i for i in product.attributes_implementations if i.attribute.key != attr.key
                        ]
                        product._impl_keys.discard(attr.key)
                    else:
                        for variant in product.variants:
                            variant.attribute_implementations = [
                                i for i in variant.attribute_implementations if i.attribute.key != attr.key
                            ]

        # 12. vincular al nuevo padre
        self.father_categorie = father_categorie
        father_categorie.subcategories.append(self)
        return {}

    # lo hizo claude a tener cuidado
    def del_categorie(self, categorie:Category, del_option:int):
        # tiene que verificar que no perjudique productos, es decir, ancestros tienen que tener ese atributo, o todos los herederos tenerlo propiamente. retorna perjudicados si los hay, sino efectua.

        # verificar si tengo esa categoria.
        # recolectar mis attributos y de mis ancestros.
        # recolectar todos los de la categoria y hacer la diferencia de attributos.
        # los que queden tienen impacto de eliminacion para esa categoria.
        # hay tres opciones, integrarle los attrb sobrantes a los productos 0, eliminarl las integraciones 1, no hacer nada 2.

        # 1. verificar que categorie es hija directa de self
        if categorie not in self.subcategories:
            return False

        # 2. atributos sobrantes: los que aporta categorie y self (ni sus ancestros) no cubren
        parent_attr_keys = self.get_attribute_keys()
        leftover_attrs = [a for a in categorie.attributes if a.key not in parent_attr_keys]

        # 3. si no hay sobrantes, eliminamos directo sin impacto
        if not leftover_attrs:
            self.subcategories = [c for c in self.subcategories if c is not categorie]
            categorie.father_categorie = None
            return []

        # 4. calcular productos impactados por atributo
        # no podemos pasar categorie directamente a _del_attribute_look_down porque
        # categorie tiene el attr y retornaria [] — salteamos ese check mirando directo
        impact_map = {}
        for attr in leftover_attrs:
            impacted = [p for p in categorie.products if attr.key not in p._attribute_keys and attr.key in p._impl_keys]
            for c in categorie.subcategories:
                impacted.extend(Category._del_attribute_look_down(c, attr))
            impact_map[attr] = impacted
        all_impacted = {p.code: p for products in impact_map.values() for p in products}

        # 5. si hay sobrantes pero ningun producto los usa, eliminamos directo
        if not all_impacted:
            self.subcategories = [c for c in self.subcategories if c is not categorie]
            categorie.father_categorie = None
            return []

        # 6. del_option=2: solo retorna productos impactados sin modificar nada
        if del_option == 2:
            return list(all_impacted.values())

        # 7. del_option=1: elimina implementaciones huerfanas segun tipo de atributo
        if del_option == 1:
            for attr, products in impact_map.items():
                for p in products:
                    if attr.is_static:
                        p.attributes_implementations = [i for i in p.attributes_implementations if i.attribute.key != attr.key]
                        p._impl_keys.discard(attr.key)
                    else:
                        for variant in p.variants:
                            variant.attribute_implementations = [i for i in variant.attribute_implementations if i.attribute.key != attr.key]

        # 8. del_option=0: inyecta la definicion del atributo en los productos, mantiene implementaciones
        if del_option == 0:
            for attr, products in impact_map.items():
                for p in products:
                    if attr.key not in p._attribute_keys:
                        p.attributes.append(attr)
                        p._attribute_keys.add(attr.key)

        # 9. eliminar la categoria y desconectar
        self.subcategories = [c for c in self.subcategories if c is not categorie]
        categorie.father_categorie = None
        return []

    def create_product(self, product:Product):
        # el producto vive en la categoria
        pass
    # elimina prod si existe, no de categorias, de todo, se elimina.
    def del_product(self, product:Product): 
        if product.code not in self._product_codes:
            return False
        self.products = [p for p in self.products if p.code != product.code]
        self._product_codes.discard(product.code)
        return True
    # agrega prod si existe
    def add_product(self, product:Product):
        if len(self.subcategories) > 0:
            raise ValueError("No puede tener categorias si quiere agregar productos")
        if product.code in self._product_codes:
            return False
        self.products.append(product)
        self._product_codes.add(product.code)
        return True

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "attributes": [
                attr.to_json() if hasattr(attr, "to_json") else attr
                for attr in self.attributes
            ],
            "subcategories": [
                sub.to_json() for sub in self.subcategories
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        attributes = [
            Attribute.from_json(attr) if isinstance(attr, dict) else attr
            for attr in data.get("attributes", [])
        ]

        category = cls(
            name=data.get("name"),
            id=data.get("id"),
            attributes=attributes
        )

        for sub_data in data.get("subcategories", []):
            sub = cls.from_json(sub_data) if isinstance(sub_data, dict) else sub_data
            sub.father_categorie = category
            category.subcategories.append(sub)

        return category

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
    attributes: List[Attribute] = None, 
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
        self.attributes_implementations = attributes_implementations or [] # implementaciones de atributos estaticos
        self._impl_keys = {i.attribute.key for i in self.attributes_implementations}
        self.attributes = attributes or [] # lista de objetos Attribute
        self._attribute_keys = {a.key for a in self.attributes}
        self.variants = variants or [] # lista de objetos Variant
    #tiene este attributo ?
    def is_attribute_in(self, attribute: Attribute):
        return attribute.key in self._attribute_keys
    #devuelve los atributos del producto
    def get_attributes(self):
        attributes = self.attributes.copy()
        attributes += self.category.get_attributes()
        return attributes

    def get_attribute_keys(self) -> set: # keys propios + todos los de la categoria recursivamente
        return self._attribute_keys | self.category.get_attribute_keys()

    # agrega attributo de variante
    def add_dinamic_attribute(self,
        attribute:Attribute,
        variant_options:list = None,
        ):
        # variant_options[{ "variant_id": "value" },...] struct que llega.
        #debe verificar que no este, y ademas pedir data de variantes para aplicar los cambios.
        # pedimos atributos purgados
        needed_attributes = self.get_needed_atributes_implementations()
        needed_keys = {a.key for a in needed_attributes}
        if attribute.key in needed_keys:
            self.attributes.append(attribute)
            self._attribute_keys.add(attribute.key)
            return True
        # si no esta debemos checkear que datos necesito y efectuar si es valido
        #hago un set con las id de las variantes y con los id pasado en variant options
        #agregando los id en variant variant_options_id verifico que no haya id duplicados, si los hay retorno false
        # ids de las variantes que tiene el producto
        variant_options_id = set()
        variants_id = {v.id for v in self.variants}
        # ids que llegan en variant_options, chequeando duplicados
        for opt in variant_options:
            vid = opt["variant_id"]
            if vid in variant_options_id:
                return False  # id duplicado en los datos que llegan
            variant_options_id.add(vid)
        # verificar que sean exactamente los mismos
        if variants_id != variant_options_id:
            return False

        # verificamos valores y tipado
        try:
            for vo in variant_options:
                attribute.check_value(vo["value"])
        except ValueError as error:
            print(error)
            return False

        # estan bien entonces les agrego las attribute implementation
        variants_map = {v.id: v for v in self.variants}
        for opt in variant_options:
            variant = variants_map[opt["variant_id"]]
            impl = AttributeImplementation(attribute=attribute, value=opt["value"])
            variant.attribute_implementations.append(impl)

        self.attributes.append(attribute)
        self._attribute_keys.add(attribute.key)
        return True
    #agrega attributo de producto
    def add_static_attribute(self,
        attribute:Attribute,
        implementation:AttributeImplementation
        ):
        # verifica que el value sea correcto.
        if not attribute.check_value(implementation.value):
            raise ValueError(f"El valor '{implementation.value}' no es válido para el atributo '{attribute.name}'.")
        # verifica que exista la subscripcion.
        needed_keys = {a.key for a in self.get_needed_atributes_implementations(is_static=True)}
        if attribute.key in needed_keys:
            #verifica que la implementacion no sea repetida, redundante pero por las dudas
            if implementation.attribute.key in self._impl_keys:
                raise ValueError("La implementacion ya esta hecha")

            # agrega la implementacion
            self.attributes_implementations.append(implementation)
            self._impl_keys.add(implementation.attribute.key)
            return True

        return False
    #elimina un attributo de un producto
    def del_attribute(self, attribute:Attribute, delete_opt:int=0):
        # delete_opt : 0=avisa impacto, 1=elimina de una sin importar impacto y borra implementaciones
        if attribute.key not in self._attribute_keys:
            return False

        # si la categoria (o algun ancestro) ya cubre el atributo, no hay impacto
        if attribute.key in self.category.get_attribute_keys():
            self.attributes = [a for a in self.attributes if a.key != attribute.key]
            self._attribute_keys.discard(attribute.key)
            return []

        # buscamos implementaciones huerfanas segun tipo
        if attribute.is_static:
            impacted = [i for i in self.attributes_implementations if i.attribute.key == attribute.key]
        else:
            impacted = [v for v in self.variants if any(i.attribute.key == attribute.key for i in v.attribute_implementations)]

        if not impacted:
            self.attributes = [a for a in self.attributes if a.key != attribute.key]
            self._attribute_keys.discard(attribute.key)
            return []

        if delete_opt == 0:
            return impacted

        # delete_opt == 1: borra implementaciones y el atributo
        if attribute.is_static:
            self.attributes_implementations = [i for i in self.attributes_implementations if i.attribute.key != attribute.key]
            self._impl_keys.discard(attribute.key)
        else:
            for v in self.variants:
                v.attribute_implementations = [i for i in v.attribute_implementations if i.attribute.key != attribute.key]
        self.attributes = [a for a in self.attributes if a.key != attribute.key]
        self._attribute_keys.discard(attribute.key)
        return []

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "brand": self.brand,
            "category": self.category.to_json() if self.category else None,
            "attributes_implementations": [
                ai.to_json() if hasattr(ai, "to_json") else ai
                for ai in self.attributes_implementations
            ],
            "attributes": [
                attr.to_json() if hasattr(attr, "to_json") else attr
                for attr in self.attributes
            ],
            "variants": [
                v.to_json() if hasattr(v, "to_json") else v
                for v in self.variants
            ]
        }

    @classmethod
    def from_json(cls, data: dict):
        category_data = data.get("category")
        category = (
            Category.from_json(category_data)
            if isinstance(category_data, dict)
            else category_data
        )

        attributes_implementations = [
            AttributeImplementation.from_json(ai) if isinstance(ai, dict) else ai
            for ai in data.get("attributes_implementations", [])
        ]

        attributes = [
            Attribute.from_json(attr) if isinstance(attr, dict) else attr
            for attr in data.get("attributes", [])
        ]

        variants = [
            Variant.from_json(v) if isinstance(v, dict) else v
            for v in data.get("variants", [])
        ]

        return cls(
            code=data.get("code"),
            title=data.get("title"),
            price=data.get("price"),
            description=data.get("description"),
            brand=data.get("brand"),
            id=data.get("id"),
            category=category,
            attributes_implementations=attributes_implementations,
            attributes=attributes,
            variants=variants
        )
    #agrega variante
    def _add_variant(self, variant:Variant):
        self.variants.append(variant)

    def del_variant(self, variant_id:int):
        original_len = len(self.variants)
        self.variants = [v for v in self.variants if v.id != variant_id]
        return len(self.variants) < original_len
    #agrega implementaciones de producto
    def add_product_implementation(self, attribute_implementation:AttributeImplementation):
        if not attribute_implementation.attribute.is_static:
            raise ValueError("Estas intentando meter un atributo dinamico como implementacion estatica")

        # chequeamos tipo de dato y que esta en attributs del producto o categoria
        try: 
            self._check_implementation(attr_impl=attribute_implementation)
        except ValueError as error:
            print(error)    
            return False

        # verificar si el atributo ya esta implementado en el producto
        if attribute_implementation.attribute.key in self._impl_keys:
            raise ValueError(f"El atributo '{attribute_implementation.attribute.name}' ya está implementado para este producto")

        self.attributes_implementations.append(attribute_implementation)
        self._impl_keys.add(attribute_implementation.attribute.key)
    #verifica type y subscripcion del attributo
    def _check_implementation(self, attr_impl:AttributeImplementation): #mixed
        # verificar que el valor sea valido segun el tipo de dato
        if not attr_impl.attribute.check_value(attr_impl.value):
            raise ValueError(f"El valor '{attr_impl.value}' no es válido para el atributo '{attr_impl.attribute.name}'.")
        # verificar que el atributo este definido en el producto o en la categoria
        needed_keys = {a.key for a in self.get_needed_atributes_implementations(is_static=True)}
        if attr_impl.attribute.key not in needed_keys:
            raise ValueError(f"La implimentacion es de un attributo que no se encuentra subscripto.")
        return True
        
    # da los atributos necesario que requeriria una variante o producto depende del parametro
    def get_needed_atributes_implementations(self, is_static:bool=False) -> set:
        all_attributes = self.get_attributes()
        result = set()
        for attr in all_attributes:
            if attr.is_static == is_static:
                result.add(attr)
        return result
    # crea la variante a travez de una lista de implementaciones que machean con las necesarias
    def create_variant_by_implementations(self, implementations:list[AttributeImplementation]):
        needed_attributes = self.get_needed_atributes_implementations()

        # construimos el set de atributos de las implementaciones recibidas, detectando duplicados
        impl_attributes = set()
        for impl in implementations:
            if impl.attribute in impl_attributes:
                print(f"Error: atributo '{impl.attribute.name}' duplicado en las implementaciones.")
                return None
            impl_attributes.add(impl.attribute)

        # los sets tienen que ser identicos
        if impl_attributes != needed_attributes:
            print("Error: las implementaciones no coinciden con los atributos requeridos.")
            return None

        # ya sabemos que las implementaciones para los atributos son los que tiene que poner, ahora mandamos a chequear los types para los values.
        for i in implementations:
            try:
                i.attribute.check_value(i.value)
            except ValueError as error:
                print(f"Error en tipo: {error}")
                return None
        # una vez chequeado verificamos que no haya otra implementacion igual
            
        # por ultimo agregamos la variante
        varian = Variant(attribute_implementations=implementations)
        self._add_variant(variant=varian)

    # helpers para category add and del attributes
    def get_add_attribute_impact(self, attribute: Attribute) -> dict | None:
        # si ya lo tiene, no impacta
        if self.is_attribute_in(attribute):
            return None
        # si no lo tiene, devuelve sus variant ids listos para appendear
        return { self.id: [v.id for v in self.variants] }
