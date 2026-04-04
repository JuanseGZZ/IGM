# AttributeImplementation

> Representa la **asignación de un valor concreto** a un `Attribute`. Une la definición del atributo con su valor real en un producto o variante.

## Analogía

Si `Attribute` es la columna de una tabla (ej: "Color"), `AttributeImplementation` es la celda concreta (ej: "Color = Rojo").

## Propiedades

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador en base de datos |
| `attribute` | Attribute | Referencia al objeto `Attribute` que se está implementando |
| `value` | str \| int \| float \| bool | Valor concreto asignado (el tipo depende del `data_type` del atributo) |

## Dónde vive

- En **`Product.attributes_implementations`**: implementaciones de atributos **estáticos** (`is_static=True`), información fija del producto.
- En **`Variant.attribute_implementations`**: implementaciones de atributos **dinámicos** (`is_static=False`), opciones elegibles de la variante.

## Métodos

### `to_json() → dict`
Serializa la implementación, incluyendo el atributo completo anidado.

### `from_json(data: dict) → AttributeImplementation` *(classmethod)*
Deserializa desde un diccionario. Si `attribute` es un dict, intenta reconstruirlo con `Attribute.from_json()`.
