# Attribute

> Representa la **definición** de un atributo (no su valor). Es el esquema que describe qué tipo de dato puede tener una propiedad de producto o variante.

## Propiedades

| Propiedad | Tipo | Descripción |
|---|---|---|
| `id` | int | Identificador en base de datos |
| `key` | str | Clave única del atributo (usada como identificador interno) |
| `name` | str | Nombre legible del atributo |
| `data_type` | str | Tipo de dato: `text`, `number`, `boolean`, `enum` |
| `is_static` | bool | Si es `True`, es atributo de **producto** (info estática). Si es `False`, es de **variante** (opción elegible) |
| `enum_values` | list | Lista de valores primitivos posibles cuando `data_type == "enum"` |

## Convenciones de uso

- **`text` y `number`**: siempre son atributos de **producto** (estáticos)
- **`boolean`**: siempre es atributo de **variante** (dinámico)
- **`enum`**: puede ser de producto o variante
  - Si es de producto → se muestra como información
  - Si es de variante → se muestra como opción a elegir

## Métodos

### `add_enum_value(value)`
Agrega un valor posible a la lista de enums.
- Lanza `ValueError` si `data_type != "enum"` o si el valor ya existe.

### `check_value(value) → bool`
Valida que un valor sea del tipo correcto según `data_type`.
- Para `enum`: verifica que el valor esté en `enum_values`.
- Lanza `ValueError` si el tipo de dato no es reconocido.

### `to_json() → dict`
Serializa el atributo completo a un diccionario JSON.
- Los `enum_values` son primitivos; se serializan directamente.

### `from_json(data: dict) → Attribute` *(classmethod)*
Reconstruye un `Attribute` desde un diccionario.
- Los `enum_values` se cargan directamente en la lista (sin pasar por `add_enum_value` para evitar el chequeo de duplicados al reconstruir).
