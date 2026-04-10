# frontFW — Documentación del Framework Frontend

Framework JS modular (ES Modules) para interactuar con la API del catálogo IGM.
Maneja DTOs, llamadas HTTP, y formularios dinámicos de dos llamadas de forma transparente.

---

## Estructura de carpetas

```
TestingConcepts/
├── package.json                      ← "type": "module" (requerido para ES Modules en Node)
└── frontFW/
    ├── index.js                      ← barrel export único del framework
    ├── config/
    │   └── config.js                 ← URL base y headers globales
    ├── interfaceModels/
    │   ├── AttributeDTO.js
    │   ├── AttributeImplementationDTO.js
    │   ├── VariantDTO.js
    │   ├── CategoryDTO.js
    │   ├── ProductDTO.js
    │   └── index.js
    ├── api/
    │   ├── _request.js               ← fetch wrapper compartido
    │   ├── attributeApi.js
    │   ├── categoryApi.js
    │   ├── productApi.js
    │   └── index.js
    └── service/
        ├── formBuilder.js            ← DOM form builder
        ├── attributeService.js
        ├── categoryService.js
        ├── productService.js
        └── index.js
```

### package.json requerido

Para que Node.js trate los archivos `.js` del framework como ES Modules:

```json
// TestingConcepts/package.json
{ "type": "module" }
```

Sin este archivo, `import` falla en Node con `SyntaxError: Cannot use import statement in a module`.

---

## Importación

```js
// Todo desde un único punto
import {
  Config,
  ProductService, CategoryService, AttributeService,
  ProductDTO, CategoryDTO, AttributeDTO,
  buildGenericForm,
} from "./frontFW/index.js";
```

O por capa:

```js
import { AttributeService } from "./frontFW/service/index.js";
import { ProductApi }       from "./frontFW/api/index.js";
import { ProductDTO }       from "./frontFW/interfaceModels/index.js";
```

---

## config/config.js

```js
Config.BASE_URL        // "http://localhost:8001"  (modificable)
Config.defaultHeaders  // { "Content-Type": "application/json" }
Config.timeout         // 0 (sin timeout activo por ahora)
```

Cambiar URL:
```js
Config.BASE_URL = "http://mi-servidor:8001";
```

---

## interfaceModels — DTOs

### AttributeDTO

| Campo         | Tipo       | Descripción                                  |
|---------------|------------|----------------------------------------------|
| `id`          | number     | ID del atributo                              |
| `key`         | string     | Identificador único (`"color"`, `"talle"`)   |
| `name`        | string     | Nombre legible (`"Color"`)                   |
| `data_type`   | string     | `"text"` \| `"number"` \| `"boolean"` \| `"enum"` |
| `is_static`   | boolean    | `true`=aplica al producto, `false`=a variante |
| `enum_values` | string[]   | Valores posibles (solo si `data_type="enum"`) |

Métodos:
```js
attr.isEnum()     // → boolean
attr.isStatic()   // → boolean
attr.isDynamic()  // → boolean
attr.toJSON()     // → plain object para la API
```

---

### AttributeImplementationDTO

Valor concreto de un atributo sobre un producto o variante.

| Campo       | Tipo          | Descripción                       |
|-------------|---------------|-----------------------------------|
| `id`        | number        | ID de la implementación           |
| `attribute` | AttributeDTO  | Atributo al que pertenece         |
| `value`     | string        | Valor siempre llega como string   |

Métodos:
```js
impl.castValue()
// Retorna el valor convertido al tipo real:
// number  → parseFloat(value)
// boolean → value === "true"
// resto   → string
```

---

### VariantDTO

Combinación concreta de atributos dinámicos de un producto.

| Campo                       | Tipo                          | Descripción                    |
|-----------------------------|-------------------------------|--------------------------------|
| `id`                        | number                        | **No estable** entre escrituras|
| `attribute_implementations` | AttributeImplementationDTO[]  | Valores por atributo dinámico  |

> **IMPORTANTE:** Los IDs de variante no son estables entre operaciones de escritura (el producto se re-persiste con nuevos IDs). Siempre hacer `getById` antes de usar `variant.id`.

Métodos:
```js
variant.getValue("color")  // → valor casteado al tipo real, o null
```

---

### CategoryDTO

| Campo        | Tipo            | Descripción                              |
|--------------|-----------------|------------------------------------------|
| `id`         | number          |                                          |
| `name`       | string          |                                          |
| `attributes` | AttributeDTO[]  | Atributos asignados a la categoría       |
| `products`   | object[]        | Productos raw (evita import circular con ProductDTO) |

---

### ProductDTO

| Campo                        | Tipo                          | Descripción                              |
|------------------------------|-------------------------------|------------------------------------------|
| `id`                         | number                        |                                          |
| `code`                       | string                        | Código único (`"REMERA-001"`)            |
| `title`                      | string                        |                                          |
| `price`                      | number                        |                                          |
| `description`                | string                        |                                          |
| `brand`                      | string                        |                                          |
| `category`                   | CategoryDTO                   | Objeto completo — **NO** `category_id`   |
| `attributes`                 | AttributeDTO[]                | Atributos propios del producto           |
| `attributes_implementations` | AttributeImplementationDTO[]  | Implementaciones estáticas               |
| `variants`                   | VariantDTO[]                  |                                          |

> La API retorna `category` como objeto completo. Para leer el id: `product.category.id`

Métodos:
```js
product.getAllDynamicAttributes()   // → AttributeDTO[] (categoría + propios, sin duplicados)
product.getAllStaticAttributes()    // → AttributeDTO[] (categoría + propios, sin duplicados)
product.getImplementation("color") // → AttributeImplementationDTO | null
```

---

## api — Capa HTTP

### _request.js — fetch wrapper

```js
import { request, ApiError } from "./frontFW/api/_request.js";

const { status, data } = await request("GET", "/products/1");
```

**Convenciones:**
- Retorna `{ status, data }` siempre — incluyendo 400 y 404.
- Lanza `ApiError` solo en error de red (status=0) o status >= 500.
- Los errores de negocio (400, 404) se manejan en la capa de servicio.

```js
class ApiError extends Error {
  status  // HTTP status (0 = red)
  detail  // mensaje del servidor
}
```

---

### AttributeApi

```js
AttributeApi.getAll()                      // GET  /attributes
AttributeApi.getById(id)                   // GET  /attributes/{id}
AttributeApi.create({ key, name, data_type, is_static, enum_values })
                                           // POST /attributes
AttributeApi.update(id, { name, enum_values })
                                           // PATCH /attributes/{id}
AttributeApi.addEnumValue(id, value)       // POST /attributes/{id}/enum-values
AttributeApi.delete(id)                    // DELETE /attributes/{id}
```

---

### CategoryApi

```js
CategoryApi.getAll()                        // GET  /categories
CategoryApi.getById(id)                     // GET  /categories/{id}
CategoryApi.create(name)                    // POST /categories
CategoryApi.updateName(id, name)            // PATCH /categories/{id}
CategoryApi.delete(id)                      // DELETE /categories/{id}
CategoryApi.addDynamicAttribute(id, body)   // POST /categories/{id}/dynamic-attributes
CategoryApi.addStaticAttribute(id, body)    // POST /categories/{id}/static-attributes
CategoryApi.removeAttribute(id, attrId, del_opt)
                                            // DELETE /categories/{id}/attributes/{attrId}?del_opt=N
CategoryApi.addProduct(id, productId)       // POST /categories/{id}/products
```

---

### ProductApi

```js
ProductApi.getAll()                         // GET  /products
ProductApi.getById(id)                      // GET  /products/{id}
ProductApi.getByCode(code)                  // GET  /products/by-code/{code}
ProductApi.create({ code, title, price, description, brand, category_id })
                                            // POST /products
ProductApi.update(id, fields)               // PATCH /products/{id}
ProductApi.delete(id)                       // DELETE /products/{id}
ProductApi.addDynamicAttribute(id, body)    // POST /products/{id}/dynamic-attributes
ProductApi.addImplementation(id, attrId, value)
                                            // POST /products/{id}/implementations
ProductApi.removeOwnAttribute(id, attrKey, del_opt)
                                            // DELETE /products/{id}/own-attributes/{attrKey}?del_opt=N
ProductApi.createVariant(id, implementations)
                                            // POST /products/{id}/variants
ProductApi.deleteVariant(id, variantId)     // DELETE /products/{id}/variants/{variantId}
```

---

## service — Lógica de negocio

Los servicios reciben parámetros tipados, manejan los errores de la API y retornan DTOs ya mapeados.

Las operaciones con impacto (que pueden requerir datos del usuario) aceptan un `container` HTMLElement. El servicio renderiza el formulario necesario en ese div y devuelve una Promise que resuelve cuando el usuario confirma.

---

### AttributeService

No toca el DOM — nunca recibe container.

```js
// Retorna AttributeDTO[]
await AttributeService.getAll()

// Retorna AttributeDTO | null
await AttributeService.getById(id)

// Retorna AttributeDTO
await AttributeService.create({ key, name, data_type, is_static, enum_values })

// Retorna AttributeDTO | null
await AttributeService.update(id, { name, enum_values })

// Retorna AttributeDTO | null  — lanza si no es enum o valor duplicado
await AttributeService.addEnumValue(id, value)

// Retorna boolean (false si no existía) — lanza si hay impls referenciando
await AttributeService.delete(id)
```

---

### CategoryService

```js
// Retorna CategoryDTO[]
await CategoryService.getAll()

// Retorna CategoryDTO | null
await CategoryService.getById(id)

// Retorna CategoryDTO
await CategoryService.create(name)

// Retorna CategoryDTO | null
await CategoryService.updateName(id, name)

// Retorna boolean — lanza si tiene productos asociados
await CategoryService.delete(id)

// Retorna object (ProductDTO raw)
await CategoryService.addProduct(catId, productId)
```

**Operaciones con impacto:**

```js
// Agrega atributo dinámico. Si hay variantes afectadas → renderiza form en container.
await CategoryService.addDynamicAttribute(catId, attrId, container)
// → CategoryDTO

// Agrega atributo estático. Si hay productos afectados → renderiza form en container.
await CategoryService.addStaticAttribute(catId, attrId, container)
// → CategoryDTO

// Elimina atributo. Si hay impls huérfanas → renderiza decisión en container.
// del_opt=1: eliminar impls | del_opt=2: migrar atributo al producto
await CategoryService.removeAttribute(catId, attrId, container)
// → CategoryDTO
```

---

### ProductService

```js
// Retorna ProductDTO[]
await ProductService.getAll()

// Retorna ProductDTO | null
await ProductService.getById(id)

// Retorna ProductDTO | null
await ProductService.getByCode(code)

// Retorna ProductDTO
await ProductService.create({ code, title, price, description, brand, category_id })

// Retorna ProductDTO | null  — solo pasa los campos que quieras modificar
await ProductService.update(id, { title, price, description, brand, category_id })

// Retorna boolean (false si no existía)
await ProductService.delete(id)

// Retorna ProductDTO — lanza si atributo no suscripto o impl duplicada
await ProductService.addImplementation(prodId, attrId, value)

// Retorna ProductDTO
await ProductService.deleteVariant(prodId, variantId)
```

**Operaciones con impacto:**

```js
// Agrega atributo dinámico. Si tiene variantes → renderiza form en container.
await ProductService.addDynamicAttribute(prodId, attrId, container)
// → ProductDTO

// Elimina atributo propio. Si hay impls → renderiza decisión (solo del_opt=1).
await ProductService.removeOwnAttribute(prodId, attrKey, container)
// → ProductDTO

// Crea variante. Si falta cubrir atributos → renderiza form en container.
// Puede llamarse con [] en la primera vez para disparar el form directamente.
await ProductService.createVariant(prodId, implementations, container)
// → ProductDTO
```

---

## service/formBuilder.js — Formularios dinámicos

Genera formularios en un `container` div. Todos reciben un callback `onSubmit`/`onDecision` que se invoca con los datos procesados.

Los servicios ya usan este módulo internamente en las operaciones de impacto, pero está disponible para usarse directamente.

### Clases CSS asignadas

Todos los elementos tienen prefijo `igm-` para evitar colisiones:

| Elemento              | Clase CSS                                      |
|-----------------------|------------------------------------------------|
| Formulario dinámico   | `igm-form igm-form--dynamic`                   |
| Formulario estático   | `igm-form igm-form--static`                    |
| Formulario variante   | `igm-form igm-form--variant`                   |
| Formulario genérico   | `igm-form igm-form--generic`                   |
| Formulario decisión   | `igm-decision`                                 |
| Sección de producto   | `igm-section igm-product-section`              |
| Fila de variante      | `igm-section igm-variant-row`                  |
| Fila de atributo      | `igm-section igm-attr-row`                     |
| Fila de campo genérico| `igm-section igm-field-row`                    |
| Label                 | `igm-label`                                    |
| Título                | `igm-title`                                    |
| Hint / descripción    | `igm-hint`                                     |
| Input texto/número    | `igm-input`                                    |
| Select                | `igm-select`                                   |
| Textarea              | `igm-textarea`                                 |
| Botón primario        | `igm-btn igm-btn--primary`                     |
| Botón danger          | `igm-btn igm-btn--danger`                      |
| Botón warning         | `igm-btn igm-btn--warning`                     |
| Lista de impacto      | `igm-impact-list`                              |
| Item de lista         | `igm-impact-item`                              |

---

### buildDynamicImplForm

```js
buildDynamicImplForm(container, { attribute, impact }, onSubmit)
```

Para cuando el servidor responde `needs_implementations: true` al agregar un atributo **dinámico**.
Pide el valor del atributo para cada variante afectada.

- `attribute`: `AttributeDTO`
- `impact`: `[{ product_id, product_code, variants: [{ variant_id }] }]`
- `onSubmit`: `(implementations: [{ product_id, variants: [{ variant_id, value }] }]) => void`

---

### buildStaticImplForm

```js
buildStaticImplForm(container, { attribute, impact }, onSubmit)
```

Para cuando el servidor responde `needs_implementations: true` al agregar un atributo **estático**.
Pide el valor del atributo para cada producto afectado.

- `attribute`: `AttributeDTO`
- `impact`: `[{ product_id, product_code }]`
- `onSubmit`: `(implementations: [{ product_id, value }]) => void`

---

### buildDecisionForm

```js
buildDecisionForm(container, { impact, hasOptTwo }, onDecision)
```

Para cuando el servidor responde `needs_decision: true` al eliminar un atributo.
Muestra la lista de productos afectados y botones de acción.

- `impact`: `[{ product_id, product_code }]`
- `hasOptTwo`: `boolean` — si `true`, muestra también "Migrar al producto" (del_opt=2)
- `onDecision`: `(del_opt: 1 | 2) => void`

> En productos `hasOptTwo=false` (solo del_opt=1). En categorías `hasOptTwo=true`.

---

### buildVariantForm

```js
buildVariantForm(container, neededAttributes, onSubmit)
```

Para cuando `createVariant` recibe `implementations_invalid`.
Pide el valor de cada atributo necesario para crear la variante.

- `neededAttributes`: `AttributeDTO[]`
- `onSubmit`: `(implementations: [{ attribute_id, value }]) => void`

---

### buildGenericForm

```js
buildGenericForm(container, schema, defaults, onSubmit)
```

Formulario genérico configurable vía schema. Útil para crear/editar cualquier entidad.

- `schema`: mapa de campos:
  ```js
  {
    fieldKey: {
      label:       string,
      type:        "text" | "number" | "textarea" | "select" | "boolean",
      required:    boolean,          // agrega " *" al label
      placeholder: string,
      options:     [{ value, label }],  // solo para type="select"
    }
  }
  ```
- `defaults`: `{ fieldKey: value }` — valores iniciales para edición
- `onSubmit`: `(data: { fieldKey: typedValue }) => void` — valores ya casteados al tipo real

---

## Flujos de dos llamadas (Two-Call Pattern)

Varias operaciones del catálogo requieren primero consultar el impacto y luego confirmar con datos adicionales.

Los servicios manejan esto automáticamente. Desde afuera solo se hace una llamada y se espera la Promise:

```
Primera llamada → server detecta impacto
   ↓
Service renderiza form en container
   ↓
Usuario completa y confirma
   ↓
Segunda llamada automática con los datos
   ↓
Promise resuelve con el DTO final
```

### Ejemplo — Agregar atributo estático a categoría

```js
const container = document.getElementById("form-area");

try {
  const category = await CategoryService.addStaticAttribute(catId, attrId, container);
  // Si no hay impacto: resuelve inmediato
  // Si hay productos afectados: renderiza form, espera al usuario, llama al server, resuelve
  console.log("Categoría actualizada:", category.name);
} catch (err) {
  console.error(err.message);
}
```

### Ejemplo — Crear variante

```js
// Primera llamada con [] para que el server diga qué atributos hacen falta
const product = await ProductService.createVariant(prodId, [], container);
// El form aparece en container, el usuario lo llena,
// y la promise resuelve con el ProductDTO actualizado.
```

---

## Ejemplo completo de uso en HTML

```html
<!DOCTYPE html>
<html>
<body>
  <div id="form-area"></div>
  <script type="module">
    import {
      Config,
      CategoryService,
      ProductService,
      AttributeService,
      buildGenericForm,
    } from "./frontFW/index.js";

    // Opcional: cambiar URL
    Config.BASE_URL = "http://localhost:8001";

    const container = document.getElementById("form-area");

    // 1. Crear un producto con formulario genérico
    const cats = await CategoryService.getAll();
    buildGenericForm(
      container,
      {
        code:        { label: "Código",      type: "text",   required: true },
        title:       { label: "Título",      type: "text",   required: true },
        price:       { label: "Precio",      type: "number", required: true },
        description: { label: "Descripción", type: "textarea" },
        brand:       { label: "Marca",       type: "text" },
        category_id: {
          label: "Categoría", type: "select",
          options: cats.map(c => ({ value: c.id, label: c.name })),
        },
      },
      {},
      async (data) => {
        const product = await ProductService.create(data);
        console.log("Producto creado:", product.id, product.code);
      }
    );

    // 2. Agregar atributo dinámico con form automático si hay variantes afectadas
    const attrId = 3;
    const prodId = 1;
    const updated = await ProductService.addDynamicAttribute(prodId, attrId, container);
    console.log("Producto con atributo:", updated.getAllDynamicAttributes().map(a => a.name));

    // 3. Leer el id de categoría (viene como objeto, no category_id)
    const prod = await ProductService.getById(prodId);
    console.log("Categoría id:", prod.category.id);

    // 4. Acceder al valor de una variante
    const variant = prod.variants[0];
    console.log("Color:", variant.getValue("color"));
  </script>
</body>
</html>
```

---

## Notas importantes

| Tema | Nota |
|------|------|
| `category` vs `category_id` | La API retorna `category` como objeto completo. Usar `product.category.id` |
| IDs de variante | No son estables entre writes. Siempre refrescar con `getById` antes de usar `variant.id` |
| Error de red vs error de negocio | `ApiError` se lanza solo en error de red o 5xx. Los 400/404 retornan `{ status, data }` |
| Módulos ES | Todos los archivos usan `import/export`. El HTML debe usar `<script type="module">` |
| `implementations_invalid` | El server lo retorna como HTTP 200 con `{ error, needed_attributes }`, no como 400 |
| `del_opt` en productos | Solo existe del_opt=1 (eliminar impls). del_opt=2 (migrar) solo existe en categorías |
| `container = null` | Se puede pasar `null` como container cuando se sabe que no habrá impacto (ej: categoría sin productos). Si el server responde con impacto y el container es null, el service lanza un error |

---

## Correcciones aplicadas al servidor (server_apis.py)

Durante el testing del framework se detectó un bug en la capa del servidor que afecta a todos los clientes (incluyendo el framework):

### Bug: InFailedSqlTransaction — transacción queda abierta en error DB

**Síntoma:** si cualquier operación falla con un error de DB (ej: FK violation al borrar un atributo que tiene implementaciones), todas las requests HTTP siguientes devuelven 500 con el mensaje `current transaction is aborted, commands ignored until end of transaction block`.

**Causa:** `crud_base.py` usa una única conexión psycopg compartida (`conn`). Cuando una query falla, PostgreSQL deja la transacción abierta en estado de error. psycopg requiere `conn.rollback()` explícito antes de poder ejecutar nuevas queries. El `_run` helper original no hacía este rollback.

**Fix en `server_apis.py`:**

```python
# Agregar import al inicio:
from config import conn

# Reemplazar _run:
def _run(fn):
    """Ejecuta fn(), convierte ValueError → 400. Rollback en cualquier error."""
    try:
        return fn()
    except ValueError as e:
        conn.rollback()   # reset de transacción también en errores de negocio
        _400(str(e))
    except Exception:
        conn.rollback()   # reset en cualquier error de DB (FK, unique, etc.)
        raise
```

**Impacto:** sin este fix, un único error de DB (como intentar borrar un atributo con FK references) rompe todas las requests subsiguientes hasta reiniciar el servidor.
