# Historial de pagos · payments.html

> **Para IAs:** Documenta `payments.html`, la pantalla de historial de pagos del usuario (como cliente de Ventium, no como vendedor). Es una página relativamente simple: KPIs + filtro por estado + buscador + lista de transacciones. Toda la data es estática (prototipo). La lógica JS es solo para el filtro y el buscador.

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Nav](#nav)
3. [Page head](#page-head)
4. [KPI strip](#kpi-strip)
5. [Filtros — Segment y Search](#filtros--segment-y-search)
6. [Lista de transacciones (.stack)](#lista-de-transacciones-stack)
7. [JS inline — filtro y búsqueda](#js-inline--filtro-y-búsqueda)
8. [Estilos inline page-specific](#estilos-inline-page-specific)

---

## Rol de la página

Historial de pagos del usuario como **suscriptor de Ventium** (lo que pagó a Ventium por sus planes, no las ventas de sus tiendas). Carga `auth.js` (guard).

---

## Nav

Nav estándar con links: Inicio / Mis tiendas / **Pagos** (activo) / Cuenta.

---

## Page head

`.page-head` → flex `space-between`:
- Título display "Tus *pagos.*" (serif italic en "pagos")
- CTA `btn-outline` → `account.html` (← Cuenta)
- Lead: "Cada cargo, cada reembolso. Ordenado por fecha y filtrable por estado."

---

## KPI strip

Grid 3 de `.kpi` del design system:

| KPI | Valor | Trend |
|---|---|---|
| Compras totales | 12 | "5 este año" |
| Total gastado | $185.400 | ▲ +18% vs 2025 (up) |
| Última compra | 1 Mar (serif italic) | "hace 73 días" |

---

## Filtros — Segment y Search

**`.seg`** (segmented control): 4 botones con `data-f`:
- `all` → Todos (activo por defecto)
- `paid` → Pagados
- `pending` → Pendientes
- `rejected` → Rechazados

`.seg button.active { background: var(--ink); color: var(--paper) }` → en dark mode flipea a crema/oscuro (contraste claro sobre página oscura).

**`.search`**: input con ícono SVG absoluto. Busca en el `textContent` de cada `.stack-row`.

---

## Lista de transacciones (.stack)

`.stack` → card contenedor con `border-radius: --r-xl`.

Cada `.stack-row` es un grid `110px / 1fr / auto / auto`:

| Columna | Contenido |
|---|---|
| `.date` | Año + fecha (ej. 2026 / 1 Mar en strong) |
| `.pay-info` | Nombre del pago + `.meta` (tag de estado + ítems + método) |
| `.total` | Monto en ARS (sans 600, 20px) |
| Link | `btn-outline btn-sm` "Detalle" → `#` (placeholder) |

`.stack-row:hover { background: rgba(20,18,14,.025) }` → overrideado en dark mode a `rgba(232,227,216,.03) !important`.

**Transacciones de ejemplo:**

| ID | Fecha | Estado | Total |
|---|---|---|---|
| #A1029 Mi Tienda | 1 Mar 2026 | Pagado (tag-success) | $24.800 |
| #A1012 Urban Shop | 18 Feb 2026 | Pendiente (tag-gold) | $9.999 |
| #A0993 Mi Tienda | 2 Feb 2026 | Pagado (tag-success) | $56.200 |
| #A0977 Deco House | 20 Ene 2026 | Rechazado (tag-danger) | $18.500 |
| #A0951 Mi Tienda | 5 Ene 2026 | Pagado (tag-success) | $11.900 |

**`.table-foot`**: pie del stack con "Mostrando 5 de 12 pagos" y link "Cargar más →" (placeholder).

Cada `.stack-row` tiene `data-status` (`paid` / `pending` / `rejected`) para el filtro por segmento.

---

## JS inline — filtro y búsqueda

```js
// Filtro por segmento
seg.addEventListener("click", e => {
  if (e.target.tagName !== "BUTTON") return;
  // actualiza botón activo
  const f = e.target.dataset.f;  // "all", "paid", "pending", "rejected"
  rows.forEach(r => {
    r.style.display = (f === "all" || r.dataset.status === f) ? "" : "none";
  });
});

// Búsqueda por texto
document.getElementById("search").addEventListener("input", e => {
  const q = e.target.value.toLowerCase().trim();
  rows.forEach(r => {
    r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none";
  });
});
```

---

## Estilos inline page-specific

Todos usan variables CSS → adaptan automáticamente al dark mode.

- `.page-head` → layout del encabezado (40px 0 24px)
- `.filters` → flex wrap con gap 8px
- `.seg` → segmented control con bg `--paper-2`
- `.search` → wrapper con icono SVG absoluto
- `.stack` → card contenedor
- `.stack-row` → grid de transacción con hover y responsive
- `.date` → tipografía de fecha (mono + strong)
- `.pay-info .nm`, `.meta` → nombre y metadatos
- `.total`, `.total .cur` → monto y moneda
- `.table-foot` → pie del stack con bg `--paper-2`
