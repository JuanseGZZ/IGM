# Autenticación · auth.js

> **Para IAs:** Este archivo documenta `auth.js`, el módulo de autenticación del prototipo. Cubre cómo funciona la sesión (localStorage), la guardia de rutas privadas y la lógica de logout. **Importante:** hay una limitación conocida donde `auth.js` no puede manipular el navbar actual porque usa un selector Bootstrap que no existe en la UI. Leé la sección de limitaciones si trabajás con el navbar.

---

## Índice

1. [Rol del archivo](#rol-del-archivo)
2. [Modelo de sesión](#modelo-de-sesión)
3. [Funciones](#funciones)
4. [Flujo de ejecución](#flujo-de-ejecución)
5. [Limitación conocida: selector de navbar](#limitación-conocida-selector-de-navbar)
6. [Qué páginas lo incluyen](#qué-páginas-lo-incluyen)
7. [Relación con la lógica de auth de index.html](#relación-con-la-lógica-de-auth-de-indexhtml)

---

## Rol del archivo

`auth.js` es un IIFE (Immediately Invoked Function Expression) que se ejecuta en las páginas privadas. Su responsabilidad es:

1. **Guardar** la sesión del usuario (vía `localStorage`)
2. **Redirigir** a `index.html` si la página actual requiere sesión y el usuario no está logueado
3. **Mostrar/ocultar** el botón de logout en el navbar

---

## Modelo de sesión

El estado de auth vive 100% en `localStorage` del browser.

| Key | Tipo | Contenido |
|---|---|---|
| `"user"` | JSON string | `{ name: string, email: string, password: string }` |
| `"logged"` | string | `"true"` cuando hay sesión activa |

- `"user"` se escribe al registrarse (en `index.html`) y persiste entre sesiones
- `"logged"` se escribe al hacer login y se borra al hacer logout
- No hay expiración de sesión ni tokens

---

## Funciones

### `isLogged()`
```js
function isLogged() {
  return localStorage.getItem("logged") === "true";
}
```
Chequea si hay sesión activa. Retorna `boolean`.

### `redirectToIndex()`
```js
function redirectToIndex() {
  window.location.href = "index.html";
}
```
Redirige al index. Ruta hardcodeada (ajustar si el index está en otra ruta).

### `guardPrivatePages()`
Determina si la página actual es pública (index.html o raíz `/`). Si no es pública y el usuario no está logueado, ejecuta `redirectToIndex()`.

Páginas consideradas públicas:
- paths que terminan en `/index.html`
- paths que terminan en `/`
- path vacío o `"/"`

Todas las demás páginas son privadas y requieren sesión.

### `ensureLogoutInNav()`
Intenta insertar (o reutilizar) un `<li id="logoutItem">` con link de logout en el navbar. Muestra u oculta según `isLogged()`. Ver [Limitación conocida](#limitación-conocida-selector-de-navbar).

---

## Flujo de ejecución

```
DOMContentLoaded
  │
  ├── guardPrivatePages()
  │     ├── ¿es index/raíz? → no hace nada
  │     └── ¿no está logueado? → redirectToIndex()
  │
  └── ensureLogoutInNav()
        ├── busca .navbar .navbar-nav   ← no existe en la UI actual (ver limitación)
        ├── si existe: inserta/actualiza #logoutItem
        └── muestra/oculta según isLogged()
```

---

## Limitación conocida: selector de navbar

`ensureLogoutInNav()` busca:
```js
const navList = document.querySelector(".navbar .navbar-nav");
```

Este selector corresponde a Bootstrap. La UI de Ventium usa:
```html
<header class="nav">
  <ul class="nav-links">...</ul>
</header>
```

**Resultado:** `.navbar .navbar-nav` no encuentra nada → `ensureLogoutInNav()` retorna sin hacer nada → el botón de logout de `auth.js` nunca se inyecta.

**Solución actual:** cada página maneja su propio logout inline con un botón específico (ej. `#logoutBtn` en `account.html`). El guard de rutas (`guardPrivatePages`) sí funciona correctamente.

**Si se quiere que auth.js maneje el logout del nav**, cambiar el selector a:
```js
const navList = document.querySelector(".nav .nav-links");
```

---

## Qué páginas lo incluyen

```html
<script src="auth.js"></script>
```

Incluido en: `account.html`, `dshb.shops.html`, `dshb.manage.html`, `payments.html`.

**NO incluido en:** `index.html` (es la página pública), `subcription.html`, `dshb.payment.success.html`, `dshb.payment.failure.html`.

---

## Relación con la lógica de auth de index.html

`index.html` maneja su propio auth de forma completamente inline (sin usar `auth.js`):

- Modal de login/register con tabs
- Login: busca `"user"` en localStorage, compara email+password, setea `"logged": "true"`
- Register: guarda `"user"` con los datos del form, setea `"logged": "true"`
- Logout: remueve `"logged"` (sin redirect)
- `updateAuthUI()`: muestra/oculta `#logoutItem` según estado

**Hay dos sistemas paralelos** — el inline de `index.html` y `auth.js` — que no se duplican porque index.html es la única página pública y no carga `auth.js`.
