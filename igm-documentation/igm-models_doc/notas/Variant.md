# Variant

> Representa una **combinación específica de opciones** de un producto. Hereda toda la información del producto por asociación y agrega las implementaciones de atributos dinámicos que la diferencian.

## Ejemplo

Un producto "Remera" puede tener variantes:
- Variante 1: Color=Rojo, Talle=M
- Variante 2: Color=Azul, Talle=XL

Cada una es un objeto `Variant`.

## Propiedades

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador en base de datos |
| `attribute_implementations` | list[AttributeImplementation] | Implementaciones de atributos **dinámicos** (`is_static=False`) |

## Notas importantes

- Una variante **no tiene precio ni título propio** — los hereda del `Product` al que pertenece.
- Solo implementa atributos **no estáticos** (los elegibles por el usuario).
- Los atributos estáticos (información del producto) viven en `Product.attributes_implementations`.

## Métodos

### `to_json() → dict`
Serializa la variante con todas sus implementaciones de atributos.

### `from_json(data: dict) → Variant` *(classmethod)*
Reconstruye una variante desde un diccionario, deserializando cada `AttributeImplementation`.
