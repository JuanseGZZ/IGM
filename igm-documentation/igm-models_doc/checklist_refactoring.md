# Checklist de Refactoring — models.py

> Cada ítem es independiente y puede hacerse en sesiones separadas.
> Para cada uno: leer el contexto indicado, hacer el cambio, correr los tests.
> Detalle completo de cada refactor en `refactoring.md`.

---

## Cómo usar este checklist

- Los ítems están ordenados de menor a mayor impacto/riesgo.
- Empezar siempre por leer las líneas indicadas antes de tocar código.
- Antes de cada cambio: los tests existentes deben pasar en verde.
- Después de cada cambio: los tests deben seguir en verde.

---

## Ítems

### [ ] 1. Guard en `Product.add_dinamic_attribute`
**Archivo:** `TestingConcepts/app/models.py`
**Línea:** 784

**Qué hacer:**
Agregar al inicio del método, antes de cualquier otra lógica:
```python
if attribute.is_static:
    raise ValueError("El attributo que se quiere incertar es estatico")
```
Esto espeja exactamente lo que ya hace `Category.add_dinamic_attribute` en la línea 254.

**Por qué:** si alguien pasa un atributo estático al método dinámico del producto, hoy no hay ningún error; el atributo se agrega igual y las variantes quedan con datos inválidos.

---

### [ ] 2. Rename de nombres con typos
**Archivo:** `TestingConcepts/app/models.py`
**Impacto:** toda la clase `Category`, `Product`, y cualquier test o repositorio que llame estos métodos.

**Qué renombrar:**

| Actual | Nuevo | Tipo |
|---|---|---|
| `add_dinamic_attribute` | `add_dynamic_attribute` | método (Category y Product) |
| `del_categorie` | `del_category` | método (Category) |
| `change_categorie_father` | `change_father_category` | método (Category) |
| `father_categorie` | `parent_category` | campo en `__init__` de Category |

**Cómo:** usar rename global (no reemplazar a mano). Asegurarse de actualizar también los tests y el repositorio.

---

### [ ] 3. Extraer helpers de `Category.del_attribute`
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 389–423

**Qué hacer:**
Leer el método completo. Extraer dos helpers privados que hoy están como bloques inline:

**`_del_attribute_remove_implementations(self, attribute, products)`**
Contiene la lógica del `delete_opt=1` (líneas 404–413):
```
para cada producto en products:
    si is_static → limpia attributes_implementations y _impl_keys
    si no → limpia variant.attribute_implementations en todas las variantes
```

**`_del_attribute_inject_to_products(self, attribute, products)`**
Contiene la lógica del `delete_opt=2` (líneas 417–420):
```
para cada producto en products:
    agrega attribute a product.attributes y _attribute_keys
```

El método `del_attribute` queda como coordinador que llama a estos dos según `delete_opt`.

---

### [ ] 4. Extraer helpers de `Category.del_categorie`
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 595–661

**Qué hacer:**
Leer el método completo. Extraer dos helpers privados:

**`_compute_categorie_impact_map(self, categorie, leftover_attrs) → tuple[dict, dict]`**
Construye y retorna `(impact_map, all_impacted)`.
Corresponde a las líneas 621–627 actuales:
```
para cada attr en leftover_attrs:
    busca productos que tienen impl del attr pero no lo tienen como propio
    suma los de subcategorias via _del_attribute_look_down
construye all_impacted como dict code → product
```

**`_apply_del_categorie_option(self, del_option, impact_map)`**
Aplica el `del_option` sobre los productos. Corresponde a los bloques de las líneas 636–657:
```
del_option=2 → retorna lista de impactados
del_option=1 → limpia implementaciones según tipo de attr
del_option=0 → inyecta definición de attr en los productos
```

---

### [ ] 5. Unificar look-up/look-down a `@staticmethod`
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 142–168 (instance methods) y 339–365 (staticmethods)

**Qué hacer:**
Convertir `_add_attribute_look_up` y `_add_attribute_look_down` de instance methods a `@staticmethod`, agregando `category` como primer argumento (igual que los `_del_*`).

Antes:
```python
def _add_attribute_look_up(self, attribute):
    if attribute.key in self._attribute_keys:
        ...
    return self.father_categorie._add_attribute_look_up(attribute=attribute)
```

Después:
```python
@staticmethod
def _add_attribute_look_up(category, attribute):
    if attribute.key in category._attribute_keys:
        ...
    return Category._add_attribute_look_up(category=category.father_categorie, attribute=attribute)
```

Actualizar todas las llamadas internas que hoy dicen `self._add_attribute_look_up(...)` para que pasen `self` como primer argumento.

---

### [ ] 6. Extraer validadores de `Category._add_attribute_variant_impact_check` y `_add_static_impact_check`
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 188–247 y 276–314

**Qué hacer:**
Ambos métodos tienen la misma estructura:
1. Llaman a `_add_attribute_product_check_family_impact`
2. Si no hay impacto → agregan el atributo directamente y retornan `{}`
3. Si hay impacto → validan coverage exacta + tipos → acumulan `pending` list → retornan pending o lista de riesgo

**Paso A — extraer bloque inicial compartido:**
`_apply_no_impact_add(self, attribute)` — el bloque "si el key no está, lo agrego" que se repite igual en los dos métodos.

**Paso B — extraer validadores separados:**

`_validate_variant_impl_coverage(self, impact, attribute, product_variant_implementations) → list`
Contiene solo la lógica de validación y construcción del `pending` de variantes (líneas 204–246). No toca estado. Retorna `pending` si todo OK, o `impact` si algo falla.

`_validate_static_impl_coverage(self, impact, attribute, implementations) → list`
Igual pero para estáticos (líneas 290–313).

Los métodos `_add_attribute_variant_impact_check` y `_add_static_impact_check` quedan como coordinadores delgados.

---

### [ ] 7. Extraer validador y chequeo de duplicados en `Product.create_variant_by_implementations`
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 993–1020

**Qué hacer:**
El método hoy mezcla validación y creación. Tiene un TODO en la línea 1016 que nunca se implementó.

**`_validate_variant_implementations(self, needed_attributes, implementations) → bool`**
Extrae las validaciones de duplicados, exact match de atributos, y chequeo de tipos (líneas 996–1015). Retorna `True` si todo OK, `False` si no (con print de error, igual que hoy).

**`_is_duplicate_variant(self, implementations) → bool`**
Implementa el TODO pendiente: compara la combinación de valores de las `implementations` contra las variantes ya existentes en `self.variants`. Si ya existe una variante con exactamente la misma combinación de valores, retorna `True`.

`create_variant_by_implementations` queda así:
```python
def create_variant_by_implementations(self, implementations):
    needed_attributes = self.get_needed_atributes_implementations()
    if not self._validate_variant_implementations(needed_attributes, implementations):
        return None
    if self._is_duplicate_variant(implementations):
        print("Error: ya existe una variante con esa combinación de valores.")
        return None
    varian = Variant(attribute_implementations=implementations)
    self._add_variant(variant=varian)
```

---

### [ ] 8. Partir `Category.change_categorie_father` en métodos
**Archivo:** `TestingConcepts/app/models.py`
**Líneas:** 437–592

**Este es el más grande. Leer el método entero antes de empezar.**
También leer en `acciones_reglas_negocio.md` la sección "5. Categoría — cambiar categoría padre" para entender bien los escenarios.

**Extraer en orden:**

**`_validate_new_father(self, father_categorie)`** — líneas 443–452
Valida anti-ciclo y que el nuevo padre no tenga productos. Lanza `ValueError` si alguno falla. Sin retorno.

**`_compute_orphan_attrs(self, father_attr_keys) → list`** — líneas 459–465
Retorna la lista de atributos del padre viejo que el nuevo padre no cubre y que `self` no tiene propios. Si `self` no tiene padre viejo, retorna `[]`.

**`_compute_new_attrs_impact(self, father_attributes) → tuple[dict, dict]`** — líneas 483–494
Retorna `(static_impact_map, dynamic_impact_map)`. Para cada atributo del nuevo padre que los descendientes no tienen, clasifica por tipo.

**`_validate_new_attr_implementations(self, static_map, dynamic_map, implementations) → dict | None`** — líneas 500–534
Valida que `implementations` cubra exactamente todos los productos y variantes afectados con valores válidos. Retorna `None` si todo OK, o `impact_map` si algo falla (sin modificar estado).

**`_apply_new_attr_implementations(self, static_map, dynamic_map, implementations)`** — líneas 537–559
Aplica las implementations validadas: estáticas en `product.attributes_implementations`, dinámicas en `variant.attribute_implementations`.

**`_resolve_orphans(self, del_option, orphan_attrs, orphan_impact)`** — líneas 568–587
Maneja los atributos huérfanos según `del_option`: 1 los inyecta en `self`, 2 elimina sus implementaciones de los productos afectados.

`change_categorie_father` queda como coordinador que llama a estos seis en orden y maneja los retornos anticipados.
