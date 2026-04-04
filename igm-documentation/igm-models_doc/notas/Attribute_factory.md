# Attribute_factory

> **Factory con caché** para instancias de `Attribute`. Garantiza que no se creen dos atributos con el mismo `key` — siempre devuelve la misma instancia.

## Por qué existe

En el modelo, un mismo atributo (por ejemplo `"color"`) puede estar referenciado en múltiples categorías y productos. La factory evita duplicación de objetos y asegura identidad referencial.

## Propiedades de clase

| Propiedad | Tipo | Descripción |
|---|---|---|
| `_instances` | dict | Mapa `key → Attribute` de instancias en memoria |

## Métodos

### `get(key, name, data_type, id, is_static) → Attribute` *(classmethod)*
Devuelve la instancia existente si el `key` ya fue registrado, o crea una nueva.
- **No actualiza** los datos si el `key` ya existe. El primer llamado define la instancia.

### `clear()` *(classmethod)*
Limpia todo el caché. Útil para tests o reinicio de estado.

## Notas de uso

```python
# Siempre usar la factory para obtener atributos
color = Attribute_factory.get(key="color", name="Color", data_type="enum")
# Mismo objeto, no importa cuántas veces se llame
color2 = Attribute_factory.get(key="color", name="Color", data_type="enum")
assert color is color2  # True
```
