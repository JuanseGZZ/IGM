# Ventium — Documentación general · screenCustomer

> **Para IAs:** Este es el índice raíz. Contiene el inventario de todos los archivos del proyecto y de cada archivo de documentación. Si buscás un componente específico, un comportamiento de auth, o cómo funciona el dark mode, leé el resumen de cada sección antes de ir al archivo. Si lo que buscás no aparece en ningún resumen, no está documentado aquí.

---

## Índice de este archivo

1. [Descripción del proyecto](#descripción-del-proyecto)
2. [Stack y restricciones técnicas](#stack-y-restricciones-técnicas)
3. [Estado actual del prototipo](#estado-actual-del-prototipo)
4. [Mapa de archivos fuente](#mapa-de-archivos-fuente)
5. [Mapa de documentación](#mapa-de-documentación)
6. [Mapa de navegación entre páginas](#mapa-de-navegación-entre-páginas)
7. [Sistema de autenticación (resumen)](#sistema-de-autenticación-resumen)
8. [Dark mode (resumen)](#dark-mode-resumen)

---

## Descripción del proyecto

**Ventium** es una plataforma SaaS de ecommerce. La carpeta `desing.screenCustomer/` contiene el **prototipo de diseño de las pantallas del cliente** — es decir, las vistas que ve el usuario final que contrata el servicio (no las pantallas del comprador de la tienda).

El conjunto de pantallas cubre el flujo completo: landing → registro/login → gestión de cuenta → listado de tiendas → dashboard por tienda (productos, pedidos, estadísticas, campañas) → historial de pagos → suscripción → resultado de pago.

---

## Stack y restricciones técnicas

| Aspecto | Detalle |
|---|---|
| Tecnología | HTML5 + CSS custom (sin frameworks) + JS vanilla |
| CSS framework | Ninguno — design system propio (`styles.css`) |
| JS framework | Ninguno — DOM vanilla |
| Auth | `localStorage` (prototipo, sin backend) |
| Estado | No hay estado reactivo; cada página es estática con JS inline |
| Backend | No conectado. Datos son placeholders estáticos |
| Fuentes | Google Fonts: Geist, Geist Mono, Instrument Serif |
| Dark mode | `prefers-color-scheme: dark` nativo en `styles.css` |

---

## Estado actual del prototipo

- **Diseño**: completo y funcional visualmente
- **Auth**: funcional via `localStorage` (registro/login/logout/guard)
- **CRUD de productos**: formulario presente, botones `disabled` (sin backend)
- **Pedidos**: datos estáticos de ejemplo
- **Estadísticas**: datos mock, chart placeholder (se reemplazará por Chart.js)
- **Campañas**: formulario presente, sin persistencia
- **Pagos**: lista estática, sin integración real
- **Mercado Pago**: mencionado en UI pero sin integración

---

## Mapa de archivos fuente

| Archivo | Rol |
|---|---|
| `styles.css` | Design system completo (variables, componentes, dark mode) |
| `auth.js` | Guard de rutas privadas + UI de logout |
| `index.html` | Landing page pública (hero, planes, equipo, formulario de registro) |
| `account.html` | Panel de cuenta del usuario (perfil, stats, accesos rápidos) |
| `dshb.shops.html` | Lista de tiendas del usuario |
| `dshb.manage.html` | Dashboard de una tienda (productos / pedidos / estadísticas / campañas) |
| `payments.html` | Historial de pagos del usuario |
| `subcription.html` | Flujo de elección de plan y checkout |
| `dshb.payment.success.html` | Pantalla de pago exitoso (ticket animado + redirect) |
| `dshb.payment.failure.html` | Pantalla de pago rechazado (ticket + countdown + retry) |

---

## Mapa de documentación

Cada archivo de documentación describe uno o más archivos fuente. El resumen de cada entrada es suficiente para que una IA decida si necesita abrir ese archivo.

| Archivo doc | Cubre | Qué encontrás |
|---|---|---|
| [`design-system.md`](design-system.md) | `styles.css` | Variables CSS, paleta, tipografía, todos los componentes del sistema de diseño, reglas del dark mode, qué variables flipean y cuáles quedan fijas |
| [`page-home.md`](page-home.md) | `index.html` | Secciones de la landing (hero, pasos, beneficios, planes, equipo, formulario), modal de auth (login/register), lógica de auth inline |
| [`page-account.md`](page-account.md) | `account.html` | Estructura de la página de cuenta: perfil, método de pago, stats rápidas, tarjetas de acceso a tiendas y pagos, logout |
| [`page-shops.md`](page-shops.md) | `dshb.shops.html` | Lista de tiendas, strip de KPIs, dropdown de acciones por tienda, card "agregar tienda" |
| [`page-dashboard.md`](page-dashboard.md) | `dshb.manage.html` | Dashboard completo de una tienda: topbar oscuro, 4 tabs (productos/pedidos/estadísticas/campañas), tabla de productos, acordeón de pedidos, gráfico de ventas, simulador de descuentos, card de rendimiento de campaña |
| [`page-payments.md`](page-payments.md) | `payments.html` | Historial de pagos: KPIs, filtro por segmento, buscador, lista de transacciones |
| [`page-subscription.md`](page-subscription.md) | `subcription.html` | Flujo de suscripción: stepper visual, selector de plan, form de checkout |
| [`page-payment-results.md`](page-payment-results.md) | `dshb.payment.success.html` + `dshb.payment.failure.html` | Ambas pantallas de resultado de pago: diseño ticket perforado, animaciones, countdown de redirect |
| [`auth.md`](auth.md) | `auth.js` | Cómo funciona la guardia de rutas, el estado de sesión en localStorage, y la limitación conocida con el selector de navbar |

---

## Mapa de navegación entre páginas

```
index.html (pública)
  ├── modal auth → account.html   (si login exitoso)
  ├── → subcription.html          (CTAs de planes)
  └── → account.html              (link nav)

account.html
  ├── → dshb.shops.html
  ├── → payments.html
  └── logout → index.html

dshb.shops.html
  ├── → dshb.manage.html?shop_id=X  (gestionar tienda)
  └── → subcription.html             (nueva tienda / suscripción)

dshb.manage.html
  └── ← dshb.shops.html              (← Tiendas en topbar)

payments.html
  └── → account.html

subcription.html
  ├── → dshb.payment.success.html
  └── → dshb.payment.failure.html

dshb.payment.success.html  →  account.html  (redirect automático)
dshb.payment.failure.html  →  index.html    (countdown 10s) + → subcription.html (retry)
```

---

## Sistema de autenticación (resumen)

- Usuario guardado en `localStorage` como `{ name, email, password }` bajo la key `"user"`
- Sesión activa: `localStorage.getItem("logged") === "true"`
- `auth.js` corre en todas las páginas privadas y redirige a `index.html` si no hay sesión
- El modal de auth (login/register) vive en `index.html` y es el único punto de entrada
- **Limitación conocida**: `auth.js` busca `.navbar .navbar-nav` (selector Bootstrap) que no existe en la UI actual; la UI de logout se maneja inline en cada página

---

## Dark mode (resumen)

- Implementado como `@media (prefers-color-scheme: dark)` al final de `styles.css`
- **Regla de profundidad**: cuanto más cerca del body, más oscuro; cuanto más lejos (cards, elementos), más claro
- `--ink` flipea a crema clara `#E8E3D8` (texto primario en oscuro)
- `--paper` flipea a `#100F0C` (fondo del body)
- Elementos que usan `var(--ink)` como fondo (botones primarios, nav activo, brand-mark) se invierten naturalmente y crean contraste
- Excepciones con override explícito: `.dash-top` (topbar del dashboard, forzado oscuro), `.plan.featured` (superficie verde oscura con borde accent), `.card.ink` (mantiene oscuro con `!important`)
- Ver [`design-system.md`](design-system.md) para la lista completa de overrides
