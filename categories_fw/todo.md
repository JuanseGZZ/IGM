# TODO — categories_fw

Estado al 2026-04-26.

---

## Leyenda
- `[x]` hecho
- `[-]` parcialmente hecho
- `[ ]` pendiente

---

## 1. Modelo base (`app/models.py`)

### Clases

- `[x]` **Attribute** — key, name, data_type, is_static, enum_values, check_value, to_json, from_json, __eq__, __hash__
- `[x]` **Attribute_factory** — singleton por key
- `[x]` **AttributeImplementation** — attribute + value, to_json, from_json
- `[-]` **Category** — ver detalle abajo
- `[-]` **Product** — ver detalle abajo
- `[-]` **Variant** — ver detalle abajo

### Category

- `[x]` `__init__` con id, name, attributes, subcategories, father_categorie, products
- `[x]` `compute_impact(attrs)` — punto de entrada publico, retorna `list[(set[Attr], list[Product])]`
- `[x]` `_descend_impact(attrs)` — recursion privada, filtra por rama
- `[x]` `get_ancestor_attrs()` — sube por father_categorie acumulando todos los atributos de los ancestros
- `[x]` `get_effective_inherited_attrs()` — attrs de ancestros que self no pisa (usado por eventos de padre)
- `[x]` validacion: una categoria no puede tener productos Y subcategorias al mismo tiempo (`_check_exclusive_children` + `add_product` / `add_subcategory`)
- `[x]` validacion: no puede haber ciclos en el arbol de categorias (`_check_no_cycle`)

### Product

- `[x]` `__init__` con code, title, price, description, brand, category, attributes_implementations, variants
- `[ ]` `get_required_static_attrs()` — todos los atributos is_static=True heredados de la cadena de categorias
- `[ ]` `get_required_dynamic_attrs()` — todos los atributos is_static=False heredados de la cadena de categorias
- `[ ]` `get_missing_static_impls()` — estaticos requeridos que no estan implementados todavia
- `[ ]` `get_extra_static_impls()` — implementaciones que ya no corresponden (herencia cambio)

### Variant

- `[x]` `__init__` con attribute_implementations, to_json, from_json
- `[ ]` validacion de unicidad — no pueden existir dos variantes con la misma combinacion de valores dentro del mismo producto
- `[ ]` `get_missing_dynamic_impls(product)` — dinamicos requeridos que la variante no tiene implementados

---

## 2. Eventos de negocio

Todos los eventos devuelven el impacto para que la capa de arriba decida que hacer (agregar/eliminar implementaciones). El modelo no muta estado por su cuenta.

### Eventos de Categoria

- `[x]` **E1 — categoria agrega un padre** (`impact_on_add_father`)
  - Calcula `(new_father.get_ancestor_attrs() | new_father.attributes) - self.attributes`
  - Llama `compute_impact` con eso — cada rama filtra lo que ya absorbe
  - Retorna: `list[(set[Attr], list[Product])]`

- `[x]` **E2 — categoria cambia de padre** (`impact_on_change_father`)
  - Llama E3 + E1 en secuencia
  - Retorna: `(impacto_salida, impacto_entrada)`

- `[x]` **E3 — categoria elimina el padre** (`impact_on_remove_father`)
  - Llama `compute_impact(self.get_effective_inherited_attrs())`
  - Debe llamarse ANTES de mutar `father_categorie`
  - Retorna: `list[(set[Attr], list[Product])]`

- `[x]` **E4 — categoria agrega un atributo** (`impact_on_add_attribute`)
  - `compute_impact({nuevo_attr})` — cada rama absorbe si ya lo tiene
  - Retorna: `list[(set[Attr], list[Product])]`

- `[x]` **E5 — categoria elimina un atributo** (`impact_on_remove_attribute`)
  - `compute_impact({attr})` — mismo mecanismo, distinto significado para el llamador
  - Subcategorias que ya definen el attr lo absorben → sus productos no pierden nada
  - Retorna: `list[(set[Attr], list[Product])]`

### Eventos de Producto

- `[x]` **E6 — producto cambia de categoria** (`Product.impact_on_change_category`)
  - `new_required = new_category.get_full_attr_set()` filtrado a `is_static=True`
  - `to_add    = new_required - current_static_impls`
  - `to_remove = current_static_impls - new_required`
  - Retorna: `(to_add, to_remove)`
  - Nota: el delta de variantes (attrs dinamicos) queda en E7

- `[x]` **E7a — producto agrega una variante** (`Product.add_variant`)
  - `get_required_dynamic_attrs()` = attrs `is_static=False` del `get_full_attr_set()` de la categoria
  - `_check_variant_completeness`: la variante debe implementar exactamente esos attrs (ni de mas ni de menos)
  - `_check_variant_uniqueness`: firma = `frozenset((attr.key, value))`, no puede repetirse
  - Retorna: ok o lanza ValueError con detalle

- `[x]` **E7b — producto quita una variante** (`Product.remove_variant`)
  - Verifica que la variante pertenezca al producto antes de eliminar

---

## 2b. Capa de servicio y API (`app/`)

- `[x]` **`schemas.py`** — contratos de request/response para todos los eventos
- `[x]` **`store.py`** — repositorio en memoria (placeholder para DB real)
- `[x]` **`services.py`** — logica de dos fases: calcula impacto, valida resolucion, ejecuta
- `[x]` **`router.py`** — 6 endpoints FastAPI con contrato de dos fases documentado

### Contrato de dos fases (aplica a E1-E6)
- **Fase 1** (sin `resolution`): calcula impacto y lo devuelve `{ status: "impact_pending", impact: [...] }`
- **Fase 2** (con `resolution`): valida que cubre todo el impacto y ejecuta. Si no cubre, vuelve a devolver el impacto pendiente.
- `action: "eliminar"` → quita las implementaciones de esos attrs en esos productos
- `action: "heredar"` → mantiene las implementaciones como estan (no hace nada)

### Pendiente en esta capa
- `[ ]` Conectar `store.py` con DB real (reemplazar dicts por queries)
- `[ ]` Endpoints CRUD base: crear/leer/listar categorias, productos, atributos
- `[ ]` Autenticacion / permisos

---

## 3. Capa de gestor / admin (`gestor/`)

- `[ ]` Vista del arbol de categorias con atributos visibles por nodo
- `[ ]` Formulario agregar/editar/eliminar categoria
- `[ ]` Formulario agregar/editar/eliminar atributo en categoria
- `[ ]` Formulario agregar/editar/eliminar producto
- `[ ]` Panel de impacto: cuando se hace un evento, mostrar que productos se ven afectados antes de confirmar
- `[ ]` Formulario agregar/editar/eliminar variante de producto con validacion de unicidad

---

## 4. Capa de usuario (`frontend/`)

- `[ ]` Pantalla de producto — muestra atributos estaticos implementados + variantes disponibles
- `[ ]` Pantalla de busqueda por categoria
- `[ ]` Filtros automaticos por categoria
  - El usuario elige una categoria y aparecen los filtros basados en sus atributos heredados
  - Version global: desde cualquier punto del arbol, recolectar todos los atributos posibles hasta las hojas y mostrarlos como filtros

---

## 5. Persistencia (`db_handler/`)

- `[x]` `schema.sql` — SQLite corregido (eliminados products_atributes y variant.code, tipos correctos)
- `[x]` `db.py` — conexion SQLite, `init_db()` para crear tablas
- `[x]` `repositories.py` — AttributeRepo, CategoryRepo, ProductRepo, VariantRepo
  - CategoryRepo.load_tree() arma el arbol completo en Python desde filas planas
  - product_implementation y variant_implementation son 1-1 (sin sharing de atr_implementation)
- `[x]` `app/store.py` — actualizado para usar repositorios en lugar de dicts en memoria

### Pendiente en persistencia
- `[ ]` `CategoryRepo.get()` resuelve el arbol completo en cada llamada — agregar cache si escala
- `[ ]` `ProductRepo._load_product()` devuelve Category stub (solo id) — enlazar con CategoryRepo para devolver el objeto completo
- `[ ]` Endpoints CRUD base en el router (crear/listar/eliminar entidades)
- `[ ]` `init_db()` llamado al arrancar la app (en main.py)

---

## Proximo paso sugerido

**E3/E1/E2** (eventos de padre en Category) — requieren primero implementar `get_ancestor_attrs()` y `get_effective_inherited_attrs()` en Category, que son los helpers que alimentan a `compute_impact`.
