# Suscripción y checkout · subcription.html

> **Para IAs:** Documenta `subcription.html`, la pantalla de selección de plan y proceso de checkout. Contiene un stepper visual, un selector de planes y un formulario de pago. El flujo desemboca en `dshb.payment.success.html` o `dshb.payment.failure.html`. Los botones de submit están como CTAs a esas páginas (sin lógica de pago real). No carga `auth.js` (no hay guard en esta pantalla).

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Nav](#nav)
3. [Page head y stepper](#page-head-y-stepper)
4. [Layout del checkout](#layout-del-checkout)
5. [Selector de planes (.plan-pick)](#selector-de-planes-plan-pick)
6. [Formulario de checkout](#formulario-de-checkout)
7. [Order summary (resumen lateral)](#order-summary-resumen-lateral)
8. [Estilos inline page-specific](#estilos-inline-page-specific)

---

## Rol de la página

Pantalla de conversión para:
- Usuarios nuevos que vienen del form de la landing (sección "Make")
- Usuarios existentes que quieren agregar/cambiar plan desde "Mis tiendas"

No tiene guard de auth (es accesible sin sesión para nuevos usuarios).

---

## Nav

Nav estándar sin links activos marcados. No hay botones de auth aquí.

---

## Page head y stepper

`.page-head` → padding 40px 0 8px.

**Stepper** (`.stepper`): indicador visual de 3 pasos con líneas separadoras:

```
[1] Elegí un plan  ──  [2] Datos de pago  ──  [3] Confirmación
```

`.stepper .s` → pill con número y texto. `.stepper .s.active` → bg `var(--ink)`, color `var(--paper)` (en dark mode flipea a crema = contraste correcto para paso activo). `.s .n` → círculo 18px con número; el activo usa bg `var(--accent)`.

---

## Layout del checkout

`.checkout-grid` → grid `1.15fr / 0.85fr` (formulario izquierda, resumen derecha).

Responsive: a 900px pasa a 1 columna (resumen debajo del formulario).

---

## Selector de planes (.plan-pick)

Grid 2x2 de `.pp` (plan picker):

| Plan | Precio |
|---|---|
| Free | $0 |
| Standard | $X |
| Shop | $Y |
| Enterprise | Custom |

Cada `.pp` es interactivo (cursor pointer). Visualmente similar a las `.plan` cards de la landing pero más compacto. El plan seleccionado muestra un estado diferente (borde accent / bg accent-soft).

---

## Formulario de checkout

Dentro de una card `.pad-lg`:

**Sección datos personales:**
- Nombre + Apellido (`.frow`)
- Email
- Teléfono

**Sección datos de pago:**
- Número de tarjeta
- Vencimiento + CVV (`.frow`)
- Titular

**Checkbox** de términos y condiciones.

**CTA**: `btn-primary btn-block btn-lg` → `dshb.payment.success.html` (prototipo, siempre va al success).

**Botón secundario**: `btn-outline btn-block` → `dshb.payment.failure.html` (para poder probar el flujo de error).

---

## Order summary (resumen lateral)

Card lateral que muestra:
- Plan seleccionado (tag-accent con nombre del plan)
- Período (mensual)
- Detalle de precio
- Total

Contenido estático (placeholder, no se actualiza al cambiar el plan selector).

---

## Estilos inline page-specific

Todos usan variables CSS → adaptan automáticamente al dark mode.

- `.page-head` → padding del encabezado
- `.checkout-grid` → layout del formulario + resumen
- `.stepper` → barra de pasos
- `.stepper .s`, `.s.active`, `.s .n` → estados de los pasos
- `.stepper .ln` → línea conectora entre pasos
- `.plan-pick`, `.pp` → grid de selección de plan
