# Refactoring — models.py

> Análisis de métodos a mejorar, dividir o corregir. Basado en las reglas de negocio de `acciones_reglas_negocio.md`.

---

## 1. `Category.change_categorie_father` — línea 437

**Problema:** 155 líneas, hace todo junto: validaciones, cálculo de huérfanos, cálculo de nuevos atributos, validación de implementations, aplicación de cambios, desconexión del padre viejo, reconexión al nuevo.

**Propuesta — partir en 6 métodos:**
- `_validate_new_father(father_categorie)` — anti-ciclo + que no tenga productos
- `_compute_orphan_attrs(father_attr_keys)` — attrs del padre viejo que quedan sin cobertura
- `_compute_new_attrs_impact(father_attributes)` — construye `static_impact_map` y `dynamic_impact_map`
- `_validate_new_attr_implementations(static_map, dynamic_map, implementations)` — valida cobertura exacta + valores (hoy son ~40 líneas sueltas dentro del método)
- `_apply_new_attr_implementations(static_map, dynamic_map, implementations)` — aplica las implementations (hoy duplica la misma lógica de iteración)
- `_resolve_orphans(del_option, orphan_attrs, orphan_impact)` — maneja del_option 1 y 2 para huérfanos

---

## 2. `Category._add_attribute_variant_impact_check` — línea 188

**Problema:** mezcla la validación de coverage (duplicados, valores, exactitud) con la acumulación del `pending` list, y además muta estado cuando no hay impacto.

**Propuesta — partir en 2:**
- `_validate_variant_impl_coverage(impact, attribute, product_variant_implementations)` — retorna `pending` list o la lista de productos en riesgo, sin tocar estado
- Mantener `_add_attribute_variant_impact_check` solo como coordinador que llama al check de familia y delega en el nuevo validador

---

## 3. `Category._add_static_impact_check` — línea 276

**Problema:** misma estructura que el punto 2, misma mezcla de concerns.

**Propuesta — partir en 2:**
- `_validate_static_impl_coverage(impact, attribute, implementations)` — mismo patrón que arriba pero para estáticos
- Mantener `_add_static_impact_check` como coordinador

> Además, los bloques iniciales de `_add_attribute_variant_impact_check` y `_add_static_impact_check` son idénticos (chequean `impact is None`, luego `not impact` + agregan attr). Ese bloque podría extraerse en `_apply_no_impact_add(attribute)` compartido.

---

## 4. `Category.del_attribute` — línea 389

**Problema:** los 3 modos de `delete_opt` están inline y cada uno mezcla lógica de tipo estático vs dinámico.

**Propuesta — partir en 2 helpers privados:**
- `_del_attribute_remove_implementations(attribute, products)` — lógica de `delete_opt=1`: limpia `attributes_implementations` o `variant.attribute_implementations` según tipo
- `_del_attribute_inject_to_products(attribute, products)` — lógica de `delete_opt=2`: inyecta el attr en los productos afectados

---

## 5. `Category.del_categorie` — línea 595

**Problema:** cálculo de impacto, arm de options, y desconexión todos inline.

**Propuesta — partir en 2:**
- `_compute_categorie_impact_map(categorie, leftover_attrs)` — construye el `impact_map` y `all_impacted` (hoy son las líneas 621–627)
- `_apply_del_categorie_option(del_option, impact_map)` — aplica la opción elegida sobre los productos

---

## 6. `Product.create_variant_by_implementations` — línea 993

**Problema:** hay un TODO comentado (línea 1016) que no está implementado (no chequea variantes duplicadas). Además mezcla validación con creación.

**Propuesta — partir en 2 + implementar el TODO:**
- `_validate_variant_implementations(needed_attributes, implementations)` — validaciones de duplicados, exact match, tipos; retorna `True/None`
- `_is_duplicate_variant(implementations)` — compara la combinación de valores contra variantes existentes
- `create_variant_by_implementations` queda limpio: llama los dos validadores y llama `_add_variant`

---

## 7. `Product.add_dinamic_attribute` — línea 784

**Problema:** la versión de `Category` guarda con `if attribute.is_static: raise ValueError`, pero la versión de `Product` no lo hace. Si alguien pasa un atributo estático no hay ningún guard.

**Propuesta:** agregar el guard al inicio, igual que `Category.add_dinamic_attribute`.

---

## 8. Naming — varios métodos y campos

**Problema:** typos consistentes a lo largo del archivo que dificultan la lectura.

| Actual | Propuesto |
|---|---|
| `add_dinamic_attribute` | `add_dynamic_attribute` |
| `del_categorie` | `del_category` |
| `change_categorie_father` | `change_father_category` |
| `father_categorie` (campo) | `parent_category` |

---

## 9. Inconsistencia instance vs static en look-up/look-down

**Problema:** `_add_attribute_look_up` y `_add_attribute_look_down` son instance methods, pero `_del_attribute_look_up` y `_del_attribute_look_down` son `@staticmethod`. No hay razón técnica para la diferencia.

**Propuesta:** unificar el patrón. Los `_del_*` ya son static por necesidad (se llaman desde el padre pasando la hija como argumento). Convertir los `_add_*` también a `@staticmethod` recibiendo `category` como primer argumento, para tener consistencia total.
