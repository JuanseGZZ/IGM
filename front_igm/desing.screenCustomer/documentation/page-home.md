# Landing page · index.html

> **Para IAs:** Documenta `index.html`, la única página pública del proyecto. Contiene la landing de Ventium con la propuesta de valor, planes y formulario de contacto. También aloja el modal de auth (login/register) y toda la lógica de sesión para la página pública (sin usar `auth.js`). Si buscás cómo funciona el login o registro, ir a [Auth inline](#auth-inline). Si buscás la estructura de planes, ir a [Sección Planes](#sección-planes).

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Estructura de secciones](#estructura-de-secciones)
3. [Sección Hero](#sección-hero)
4. [Sección Marquee](#sección-marquee)
5. [Sección How (Cómo funciona)](#sección-how-cómo-funciona)
6. [Sección Benefits (Beneficios)](#sección-benefits-beneficios)
7. [Sección Planes](#sección-planes)
8. [Sección Who (Equipo)](#sección-who-equipo)
9. [Sección Make (Formulario)](#sección-make-formulario)
10. [Footer](#footer)
11. [Modal de Auth](#modal-de-auth)
12. [Auth inline](#auth-inline)
13. [Estilos inline (page-specific)](#estilos-inline-page-specific)

---

## Rol de la página

Página pública (no requiere sesión). Es el punto de entrada de usuarios no registrados. Cumple tres roles:
1. **Marketing** → presenta la propuesta de valor y los planes
2. **Registro** → formulario de onboarding + modal de login/register
3. **Gateway** → intercepta clicks a "Cuenta" y muestra el modal si no hay sesión

---

## Estructura de secciones

```
<header class="nav">          ← sticky nav con modal trigger
<main>
  <section class="hero">      ← propuesta de valor + phone mockup
  <div class="marquee">       ← strip de features
  <section id="how">          ← 3 pasos (grid de steps)
  <section id="benefits">     ← cards de beneficios + tabla comparativa
  <section id="costs">        ← 4 planes de precios
  <section id="who">          ← equipo + contact card
  <section id="make">         ← formulario de onboarding
  <footer class="footer">
<div class="modal-backdrop">  ← modal auth (fuera de main)
```

---

## Sección Hero

- Layout: grid `1.15fr / 0.85fr` (texto + phone mockup)
- **Display heading**: serif italic "Tu tienda online, sin complicarte"
- Palabra "complicarte" tiene subrayado accent verde con `::after` skewed
- **CTAs**: `btn-primary` → #make, `btn-outline` → #how
- **Hero meta**: estrellas doradas (hardcodeado ★★★★★), texto social proof
- **Phone mockup**: div decorativo que simula un teléfono con productos y botón de compra. Sin funcionalidad.

---

## Sección Marquee

Strip horizontal con 6 features en texto:

> ★ Mobile-first · ✦ Pagos integrados · ✱ Campañas de mailing · ◆ Estadísticas con IA · ＋ Multi-tienda · ⟶ Setup en 4 min

---

## Sección How (Cómo funciona)

Grid de 3 `<div class="step">` con números en serif italic (01, 02, 03):
1. Creá tu cuenta
2. Cargá productos
3. Publicá y vendé

---

## Sección Benefits (Beneficios)

Dos partes:
- **3 cards** (catálogo, mailing, insights) con eyebrow y descripción de límites por plan
- **Tabla comparativa** `.compare` → columnas Free / Standard / Shop / Enterprise. Filas: productos, seguimiento, mailing, mails/sem, estadísticas, IA asistida

---

## Sección Planes

Grid de 4 `.plan` cards:

| Plan | BG | Precio | Destacado |
|---|---|---|---|
| Free | card normal | $0/mes | — |
| Standard | `.plan.featured` (ink bg) | $X/mes | ribbon "Recomendado" |
| Shop | card normal | $Y/mes | — |
| Enterprise | card normal | Custom | — |

Precios Standard y Shop son placeholders (X / Y) pendientes de definición.

Todos los CTAs van a `subcription.html`.

**Dark mode:** `.plan.featured` overrideado a verde oscuro `#14211A` con borde accent (no flipea a crema).

---

## Sección Who (Equipo)

Grid `1.2fr / 0.8fr`:
- **Izquierda**: quote en serif italic + 4 who-stats (2k+ tiendas, $14M procesados, 99.9% uptime, 4 min setup)
- **Derecha**: `.contact-card` (bg `--ink` → crema en dark mode) con links de contacto (email, Instagram, WhatsApp)

Los `.contact-row` dentro del contact-card tienen `rgba(241,238,230,...)` hardcodeado (asumen fondo oscuro). En dark mode se overridean via selector más específico en `styles.css`.

---

## Sección Make (Formulario)

Grid 50/50:
- **Izquierda**: texto + lista de beneficios
- **Derecha**: `.make-card` con form de:
  - Nombre de marca
  - Email
  - Plan (select: Free / Standard / Shop / Enterprise)
  - Checkbox de términos
  - CTA → `subcription.html`

El form no tiene `action` ni JS de submit — prototipo estático.

---

## Footer

Row con brand-mark + año (JS) y links: Equipo / Planes / Cuenta / Términos / Privacidad.

---

## Modal de Auth

`<div class="modal-backdrop" id="authModal">` — fuera del `<main>`, siempre presente en el DOM.

Estructura interna:
- `.modal-head` → eyebrow "Acceso" + h3 + botón cerrar (`data-close`)
- `.tabs` → "Ingresar" / "Crear cuenta" (cambia `.pane.active`)
- **Pane Login** (`#paneLogin`): email + password + `#loginBtn` + `#loginError`
- **Pane Register** (`#paneRegister`): nombre + email + password + `#registerBtn` + `#registerError`

Abre: click en `#accountLink` del nav si no está logueado.
Cierra: click en backdrop, click en `[data-close]`, o login/register exitoso.

---

## Auth inline

Todo el JS de auth en `index.html` está en un `<script>` al final del body. No usa `auth.js`.

```js
// Helpers
isLogged()         // localStorage.getItem("logged") === "true"
updateAuthUI()     // muestra/oculta #logoutItem según estado
openModal()        // modal.classList.add("open")
closeModal()       // modal.classList.remove("open")

// Login flow
#loginBtn.click → compara email+pass con localStorage["user"]
  → si match: setea logged=true, cierra modal, redirect a account.html
  → si no: muestra #loginError

// Register flow
#registerBtn.click → valida campos, guarda localStorage["user"], setea logged=true
  → redirect a account.html

// Logout
#logoutLink.click → remueve "logged", updateAuthUI() (no hace redirect)

// Intercept nav
#accountLink.click → si !isLogged(): e.preventDefault() + openModal()
```

---

## Estilos inline (page-specific)

`index.html` contiene un `<style>` block con estilos de:
- `.hero`, `.hero-grid`, `.hero h1.display .underline::after` (subrayado accent)
- `.hero-cta`, `.hero-meta`, `.hero-meta .stars`
- `.phone`, `.phone-screen`, `.phone-bar`, `.phone-card`, `.phone-cta`
- `.marquee`, `.marquee-inner`
- `.steps`, `.step`
- `.plans`, `.plan`, `.plan-name`, `.plan-price`, `.feat`, `.ribbon`
- `.compare` table
- `.who-grid`, `.who-quote`, `.who-stats`, `.contact-card`, `.contact-row`
- `.make-grid`, `.make-card`

**Importante para dark mode:** estos estilos pueden tener mayor especificidad que el bloque dark de `styles.css` cuando el selector es idéntico. Los overrides de `styles.css` que necesitan ganar usan selectores más específicos o `!important` donde el HTML tiene inline styles.
