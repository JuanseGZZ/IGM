# M2 · Estructura final refactorizada

Suposiciones usadas para este canvas:

- Se aplicaron los renombres sugeridos:
  - `add_dinamic_attribute` -> `add_dynamic_attribute`
  - `del_attribute` -> `remove_attribute`
  - `del_categorie` -> `remove_subcategory`
  - `change_categorie_father` -> `change_parent_category`
  - `del_product` -> `remove_product`
  - `del_variant` -> `remove_variant`
  - `create_variant_by_implementations` -> `create_variant`
  - `add_product_implementation` + `add_static_attribute` -> `add_static_implementation`

- `Category.create_product` se considera eliminado en la version final porque habia quedado como API muerta.
- El canvas muestra estructura objetivo de diseño, no el codigo actual exacto.
- La relacion es:
  - clase
  - metodo publico
  - helpers privados que usa
