# Resultados de pago · dshb.payment.success.html / dshb.payment.failure.html

> **Para IAs:** Documenta las dos pantallas de resultado de pago. Comparten la misma estructura "ticket perforado" pero difieren en color, animación e iconografía. Ambas tienen un redirect automático con countdown. La pantalla de failure tiene además un bloque de motivo de rechazo y un botón de retry. No cargan `auth.js`. Si solo necesitás saber qué hace el countdown, ir a [Countdown y redirect](#countdown-y-redirect).

---

## Índice

1. [Estructura compartida](#estructura-compartida)
2. [Pantalla de éxito (success)](#pantalla-de-éxito-success)
3. [Pantalla de fallo (failure)](#pantalla-de-fallo-failure)
4. [Countdown y redirect](#countdown-y-redirect)
5. [Dark mode — consideraciones](#dark-mode--consideraciones)
6. [Estilos inline page-specific](#estilos-inline-page-specific)

---

## Estructura compartida

Ambas páginas comparten:

```
<header class="nav">         ← nav reducido (solo brand + tag de estado)
<div class="canvas">         ← full-height, centrado
  <div class="ticket">       ← card tipo ticket perforado
    <div class="ticket-top"> ← header del ticket (ícono + título + subtítulo)
    <div class="perf">       ← perforación decorativa
    <div class="ticket-body">← detalles de la transacción
    <div class="ticket-foot">← botones de acción + countdown
    <div class="br">         ← footer del ticket (ayuda / email)
```

**`.canvas::before`**: gradiente radial de fondo usando la variable soft del color correspondiente (accent-soft en success, coral-soft en failure). En dark mode estas variables son muy oscuras (`#0D2018` y `#20100E`), creando un sutil halo de color sin deslumbrar.

**`.perf`**: div con pseudo-elementos `::before` y `::after` que simulan semicírculos de perforación del ticket. `background: var(--ink)` para el fondo del perf y `var(--paper)` para los semicírculos.

---

## Pantalla de éxito (success)

**`dshb.payment.success.html`**

**Nav tag**: `tag-success` con "Transacción aprobada" (o similar).

**Ícono** (`.check`):
- Círculo 72px, bg `var(--accent)` verde
- Box-shadow: `0 0 0 8px rgba(14,94,63,.18)` → halo verde
- **Animación** `pop`: scale .4 → 1 con cubic-bezier elástico (.2,.9,.3,1.4) en 0.6s

**Ticket-top**: bg `var(--ink)` (crema en dark mode), text `var(--paper)` (oscuro en dark mode).
- h1 serif italic: "¡Pago *aprobado.*"
- subtítulo con detalles del plan comprado

**Ticket-body**: resumen de la transacción:
- Nro de pedido (ej. VTM-A1029)
- Fecha (JS: `new Date().toLocaleDateString("es-AR", ...)`)
- Plan contratado
- Monto

**Ticket-foot**:
- `btn-accent btn-block btn-lg` → `account.html`
- `btn-outline btn-block` → `index.html`
- Countdown row

**Redirect**: va a `account.html` cuando el contador llega a 0.

---

## Pantalla de fallo (failure)

**`dshb.payment.failure.html`**

**Nav tag**: `tag-danger` "Transacción rechazada".

**Ícono** (`.xmark`):
- Círculo 72px, bg `var(--coral)` rojo-naranja
- Box-shadow: `0 0 0 8px rgba(199,85,58,.18)` → halo coral
- **Animación** `shake`: scale .4 → 1.05 + rotate -3deg → 1 + rotate 3deg → 1 en 0.6s

**Ticket-top**: igual al success (bg `var(--ink)`, text `var(--paper)`).
- h1: "No se pudo procesar el pago."
- subtítulo: "no se realizó ningún cargo"

**Bloque de motivo** (`.reason`):
- bg `var(--coral-soft)`, borde `#ecc4b6` (hardcodeado en light)
- Ícono `!` serif italic en círculo coral
- `.reason .t`: título del motivo (color `#6a1d10`)
- `.reason .d`: descripción (color `#7a3322`)
- **Nota dark mode**: estos colores hardcodeados de texto son oscuros. Sobre el `--coral-soft` que en dark mode = `#20100E` (muy oscuro), quedarían invisibles. Sin embargo, el `borde: 1px solid #ecc4b6` es claro sobre oscuro, y los colores de texto actuales son oscuros sobre oscuro — esto es una deuda de dark mode pendiente para esta página.

**Ticket-body** (`.row-sum`):
| Campo | Valor |
|---|---|
| Intento | VTM-ERR-7B22 |
| Fecha | JS: fecha actual |
| Método | Mercado Pago · ●●●● 24 |
| Monto | $14.900 |

**Ticket-foot**:
- `btn-primary btn-block btn-lg` → `subcription.html` (Reintentar)
- `btn-outline btn-block` → `index.html`
- Countdown row

**Redirect**: va a `index.html` cuando el contador llega a 0.

---

## Countdown y redirect

```js
const d = new Date();
document.getElementById("todayDate").textContent =
  d.toLocaleDateString("es-AR", { day: "2-digit", month: "long", year: "numeric" });

let seconds = 10;
const counter = document.getElementById("counter");
const t = setInterval(() => {
  seconds--;
  counter.textContent = seconds;
  if (seconds <= 0) {
    clearInterval(t);
    window.location.href = "destino.html";
  }
}, 1000);
```

- Inicia en 10 segundos
- El `.countdown` (span mono con bg `--paper-2`) muestra el número restante
- Al llegar a 0 hace el redirect

---

## Dark mode — consideraciones

**Lo que funciona bien:**
- `.canvas::before` usa `var(--coral-soft)` / `var(--accent-soft)` → en dark mode son tonos muy oscuros, creando halos sutiles correctos
- `.ticket` usa `var(--card)` → se oscurece correctamente
- `.row-sum .v` usa `var(--ink)` → texto claro en dark mode
- `.countdown` usa `var(--paper-2)` → superficie oscura correcta

**`.ticket-top`** usa `bg: var(--ink)` → en dark mode flipea a crema `#E8E3D8`. Los textos dentro con `color: var(--paper)` = oscuro sobre crema = legible. Esta inversión es aceptable aquí (es un header de ticket, no un panel de dashboard).

**`.reason` block** (solo en failure): colores hardcodeados oscuros (`#6a1d10`, `#7a3322`) sobre `--coral-soft` en dark mode = oscuro sobre oscuro. **Deuda de dark mode**: estos colores deberían overridearse en una futura iteración.

---

## Estilos inline page-specific

Todos excepto `.reason` colors usan variables CSS.

- `body { min-height: 100vh; display: flex; flex-direction: column }` → para que canvas ocupe todo el alto
- `.canvas`, `.canvas::before` → centrado full-height con gradiente radial
- `.ticket` → card tipo ticket
- `.ticket-top` → header del ticket con bg `var(--ink)`
- `.check` / `.xmark` → ícono animado + box-shadow halo
- `@keyframes pop` / `@keyframes shake` → animaciones de entrada
- `.perf`, `.perf-line` → decoración de perforación
- `.ticket-body`, `.ticket-foot` → cuerpo y pie del ticket
- `.row-sum` → fila de detalle
- `.countdown-row`, `.countdown` → fila del contador
- `.br` → footer del ticket
- **Solo failure:** `.reason`, `.reason .ic`, `.t`, `.d` → bloque de motivo de rechazo
