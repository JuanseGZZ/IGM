# Lista de refactoreo

## Metodos a refactorizar

1. `Attribute.check_value`
- Separarlo en `is_valid_value(value)` y `validate_value(value)`.
- Hacer que los metodos que escriben estado usen `validate_value`.

2. `Category.change_categorie_father`
- Dividirlo en:
  - `_validate_new_parent`
  - `_collect_inherited_attributes`
  - `_collect_orphan_attributes`
  - `_build_orphan_impact_map`
  - `_build_new_parent_impact_maps`
  - `_validate_reparent_implementations`
  - `_apply_reparent_implementations`
  - `_resolve_orphan_attributes_after_reparent`
  - `_relink_parent`

3. `Category.del_categorie`
- Dividirlo en:
  - `_validate_direct_subcategory`
  - `_collect_leftover_attributes_from_child`
  - `_build_subcategory_removal_impact_map`
  - `_resolve_subcategory_removal_impact`
  - `_detach_subcategory`

4. `Category.add_dinamic_attribute`
- Dividirlo en:
  - `_validate_dynamic_attribute_definition`
  - `_calculate_attribute_add_impact`
  - `_validate_dynamic_attribute_payload`
  - `_build_pending_dynamic_implementations`
  - `_apply_dynamic_attribute_addition`
- Hacer que `_add_attribute_variant_impact_check` no mute estado.

5. `Category.add_static_attribute`
- Dividirlo en:
  - `_validate_static_attribute_definition`
  - `_calculate_attribute_add_impact`
  - `_validate_static_attribute_payload`
  - `_build_pending_static_implementations`
  - `_apply_static_attribute_addition`
- Hacer que `_add_static_impact_check` no mute estado.

6. `Category.del_attribute`
- Dividirlo en:
  - `_collect_attribute_removal_impact`
  - `_remove_attribute_from_category`
  - `_remove_static_implementations_from_products`
  - `_remove_dynamic_implementations_from_products`
  - `_inject_attribute_into_products`
- Reemplazar `delete_opt` por un enum.

7. `Product.add_dinamic_attribute`
- Dividirlo en:
  - `_is_dynamic_attribute_already_covered`
  - `_validate_variant_options_coverage`
  - `_validate_variant_option_values`
  - `_build_dynamic_variant_implementations`
  - `_apply_dynamic_attribute_to_product`
  - `_attach_own_attribute`

8. `Product.add_static_attribute` y `Product.add_product_implementation`
- Unificarlos en una sola API.
- Dejar:
  - `add_static_implementation`
  - `_validate_static_implementation_allowed`
  - `_ensure_static_implementation_not_duplicate`
  - `_apply_static_implementation`

9. `Product.create_variant_by_implementations`
- Dividirlo en:
  - `_collect_required_variant_attributes`
  - `_validate_variant_implementation_set`
  - `_validate_variant_implementation_values`
  - `_find_duplicate_variant`
  - `_build_variant`
  - `_append_variant`

10. `Product.del_attribute`
- Dividirlo en:
  - `_validate_own_attribute_exists`
  - `_is_attribute_covered_by_category`
  - `_collect_orphan_product_implementations`
  - `_remove_product_attribute_definition`
  - `_remove_orphan_product_implementations`
- Reemplazar `delete_opt` por un enum.

11. `get_attributes`, `get_attribute_keys`, `change_lookup_for_attributes`
- Unificarlos en helpers comunes:
  - `iter_ancestor_categories()`
  - `collect_inherited_attributes()`
  - `collect_inherited_attribute_keys()`

12. `Category.create_product`
- Implementarlo o eliminarlo.
- Si se implementa:
  - `_validate_product_can_be_attached`
  - `_initialize_product_context`
  - `_attach_product_to_category`

## Cambios transversales

- Renombrar typos del dominio:
  - `dinamic` a `dynamic`
  - `categorie` a `category`
  - `atributes` a `attributes`

- Encapsular caches internos:
  - `_add_own_attribute`
  - `_remove_own_attribute`
  - `_add_static_impl`
  - `_remove_static_impl`
  - `_attach_product`
  - `_detach_product`

- Unificar contratos de retorno:
  - excepciones consistentes
  - o `OperationResult`

## Orden sugerido

1. `Attribute.check_value`
2. `Category.change_categorie_father`
3. `Category.del_categorie`
4. `Category.add_dinamic_attribute` y `Category.add_static_attribute`
5. `Product.add_static_attribute` y `Product.add_product_implementation`
6. `Product.create_variant_by_implementations`
