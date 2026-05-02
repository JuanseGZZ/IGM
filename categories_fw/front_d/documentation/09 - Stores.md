# Stores

Carpeta: `stores/`

Dos módulos que encapsulan todo acceso a `localStorage`. Ningún otro archivo toca `localStorage` directamente.

---

## `attrStore.js`

Almacén global de atributos. Los atributos son objetos planos compartidos entre todas las categorías del árbol.

### Estructura de un atributo

```js
{
  id:          number,   // autoincremental
  key:         string,   // identificador único (ej: "color")
  name:        string,   // nombre visible (ej: "Color")
  data_type:   string,   // "text" | "number" | "boolean" | "enum"
  is_static:   boolean,  // true → aplica a Producto, false → aplica a Categoría/Variante
  enum_values: string[], // opciones cuando data_type === "enum"
}
```

### API

```js
attrStore.load()
// Lee localStorage("igm-attrs") y populea this.attrs y this.lastId.
// Llamar una vez al iniciar (events.js).

attrStore.add({ key, name, data_type, is_static, enum_values })
// Crea un atributo con id autoincremental, lo empuja a this.attrs y persiste.
// Retorna el objeto creado.

attrStore.remove(id)
// Elimina el atributo por id. Retorna true si existía, false si no.

attrStore.attrs   // array en memoria (no modificar directamente)
attrStore.lastId  // contador interno
```

### Persistencia

```
localStorage("igm-attrs") → JSON.stringify({ lastId, attrs: [...] })
```

---

## `catalogStore.js`

Almacén del árbol de catálogo. Delega la serialización al `Handler`.

### API

```js
catalogStore.save(handler)
// Serializa el árbol completo con handler.toJson() y lo escribe en localStorage.

catalogStore.load(handler)
// Lee localStorage("igm-catalog") y llama handler.fromJson(raw).
// Retorna true si había datos guardados, false si no.
// En caso de error de parseo, imprime warning y retorna false.
```

### Persistencia

```
localStorage("igm-catalog") → handler.toJson()  (JSON con lastId + árbol completo)
```

### Cuándo se llama `save`

- En cada `handler.render()` (el render está wrapeado en `events.js`)
- En el evento `igm-collapse` (colapsar/expandir una carta no dispara un render completo)

```js
// events.js — wrap del render
handler.render = (opts) => {
  _render(opts);
  catalogStore.save(handler);
};

// events.js — colapso sin re-render
board.addEventListener("igm-collapse", () => catalogStore.save(handler));
```
