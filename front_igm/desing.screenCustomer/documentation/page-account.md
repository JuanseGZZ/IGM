# Panel de cuenta · account.html

> **Para IAs:** Documenta `account.html`, la pantalla de perfil del usuario. Es la primera página privada que ve el usuario tras el login. Contiene el perfil, método de pago, estadísticas rápidas y accesos al resto del dashboard. Página sencilla — si buscás lógica compleja, está en `dshb.manage.html`. El logout de esta página es un botón ghost inline, no el de `auth.js`.

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Nav](#nav)
3. [Sección hero de cuenta](#sección-hero-de-cuenta)
4. [Profile card (.acc-card)](#profile-card-acc-card)
5. [Quick stats](#quick-stats)
6. [Nav cards (accesos rápidos)](#nav-cards-accesos-rápidos)
7. [Logout](#logout)
8. [Estilos inline page-specific](#estilos-inline-page-specific)

---

## Rol de la página

Primera pantalla del área privada. Agrega:
- Identidad del usuario (avatar, nombre, email)
- Método de pago conectado (Mercado Pago placeholder)
- Resumen numérico (tiendas, compras, gasto total)
- Accesos directos a Mis tiendas y Mis pagos

Carga `auth.js` → si no hay sesión, redirige a `index.html`.

---

## Nav

Nav estándar de Ventium (`.nav`) con links: Inicio / Mis tiendas / Pagos / **Cuenta** (activo).

No tiene el modal de auth (eso vive solo en `index.html`). No hay `#logoutItem` en el nav de esta página; el logout está en la parte inferior del contenido.

---

## Sección hero de cuenta

```html
<section class="acc-hero">
  <span class="eyebrow">Mi cuenta</span>
  <h1 class="display">Hola, Juan.</h1>
  <p class="lead">...</p>
</section>
```

El nombre "Juan" es placeholder estático (prototipo).

---

## Profile card (.acc-card)

Contenedor `.acc-card` con filas `.row-info` (grid `200px / 1fr`):

| Fila | Contenido |
|---|---|
| Perfil | Avatar `.avatar` (gradiente accent, letra JP, serif italic 32px) + nombre + email + antigüedad |
| Nombre | "Juan" + label "editable" |
| Apellido | "Pérez" + label "editable" |
| Email | `juan.perez@...` |
| Cuenta asociada | `.mp-row` con icono "MP", nombre "Mercado Pago", ID `shop_123456`, tag `tag-success` "Conectado" |

**`.avatar`**: div 64px con `border-radius: 18px`, gradiente accent diagonal, texto serif italic crema.

**`.mp-row`**: row con `.ic` (icono cuadrado 40px bg `--card` con texto "MP" en color `--blue`) y `.tag-success`.

Todo es estático (prototipo). Los campos "editables" no tienen forma de editarse.

---

## Quick stats

Grid 3 columnas de `.qs` (bg `--paper-2`):

| Stat | Valor |
|---|---|
| Tiendas | 2 |
| Compras | 12 |
| Total gastado | $ 185.400 |

---

## Nav cards (accesos rápidos)

Grid `1fr / 1fr` de `.nav-card` con hover de `translateY(-2px)` + sombra + borde `--ink`.

| Card | Destino | Descripción |
|---|---|---|
| Mis tiendas | `dshb.shops.html` | Icono tienda SVG, "Gestioná tus tiendas, planes y catálogos" |
| Mis pagos | `payments.html` | Icono tarjeta SVG, "Historial completo de transacciones y facturas" |

Cada `.nav-card` tiene `.ic-lg` (44px, bg `--paper-2`) y `.arrow` (→ que se mueve en hover).

---

## Logout

Botón `.btn-ghost` con id `#logoutBtn` al final de la sección principal:

```js
#logoutBtn.click → localStorage.removeItem("logged") → redirect a index.html
```

Diferente al `#logoutLink` de `index.html` que no hacía redirect.

---

## Estilos inline page-specific

Todos usan variables CSS, no hay rgba hardcodeados. Se adaptan automáticamente al dark mode.

- `.acc-hero` → padding 48px 0 16px
- `.acc-card`, `.row-info` → layout del profile card
- `.avatar` → gradiente accent, tamaño, tipografía
- `.mp-row`, `.ic` → fila de cuenta de pago
- `.nav-grid`, `.nav-card` → grid y estilo de tarjetas de acceso
- `.ic-lg` → contenedor de ícono grande
- `.quick-stats`, `.qs` → grid y celdas de stats
