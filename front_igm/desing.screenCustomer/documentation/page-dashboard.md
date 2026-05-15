# Dashboard de tienda · dshb.manage.html

> **Para IAs:** Documenta `dshb.manage.html`, la pantalla más compleja del proyecto. Es el panel de control de una tienda individual con 4 tabs: Productos, Pedidos, Estadísticas y Campañas. Tiene un topbar oscuro propio (`.dash-top`) distinto al nav estándar. Los formularios y botones están deshabilitados (prototipo sin backend). Si buscás la lógica de tabs, acordeones o la tarjeta de rendimiento (card.ink), están documentados aquí.

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Topbar oscuro (.dash-top)](#topbar-oscuro-dash-top)
3. [Page head y tabs (.dtabs)](#page-head-y-tabs-dtabs)
4. [Tab Productos](#tab-productos)
5. [Tab Pedidos](#tab-pedidos)
6. [Tab Estadísticas](#tab-estadísticas)
7. [Tab Campañas](#tab-campañas)
8. [Footer](#footer)
9. [JS inline](#js-inline)
10. [Estilos inline page-specific](#estilos-inline-page-specific)
11. [Dark mode — consideraciones especiales](#dark-mode--consideraciones-especiales)

---

## Rol de la página

Dashboard operativo de una tienda. Recibe `?shop_id=X` como query param para identificar la tienda. Carga `auth.js` (guard).

---

## Topbar oscuro (.dash-top)

Diferente al nav estándar. Siempre oscuro (bg `var(--ink)` → forzado a `#0C0A08` en dark mode con `!important`).

```html
<header class="dash-top nav">
  <div class="dash-wrap nav-inner">
    <div class="crumb">...</div>
    <div class="head-tools">...</div>
  </div>
</header>
```

**Breadcrumb (`.crumb`):**
- Link "Mis tiendas" → `dshb.shops.html`
- Separador `/`
- `.shop` con `.dot-mark` (22px gradiente accent) + nombre "Urban Sneakers"

**`.id-pill`** (oculto en mobile): muestra `shop_id` leído desde query params.

**Botón ← Tiendas**: `btn-outline btn-sm` con `style="background:transparent; color:var(--paper); border-color:rgba(241,238,230,.22)"`. El `color:var(--paper)` flipea a oscuro en dark mode — overrideado via `.dash-top .btn { color: var(--ink) !important }`.

---

## Page head y tabs (.dtabs)

`.dash-page-head` → flex space-between con título "Panel de Urban Sneakers" + tags + botón Refrescar.

`.dtabs` → 4 tabs: Productos / Pedidos / Estadísticas / Campañas. JS cambia el `.pane.active`.

---

## Tab Productos

Layout `.split-5-7` (form izquierda, lista derecha).

**Formulario (card.pad-lg):**
- ID, Título, Precio + Stock (`.frow`), Descripción (textarea), Foto (`.photo-up`)
- Botones "Guardar" y "Limpiar" — `disabled`

**`.photo-up`**: label custom para file input. Flex con icono SVG upload, texto y `<input type="file" display:none>`.

**Lista de productos:**
- Buscador con icono SVG absoluto dentro de `.search`
- Tabla `.tbl` con columnas: Producto / ID / Stock / Precio / Acciones
- Cada fila tiene `.prod-row` (imagen `.ph` + nombre/descripción) y `.btn-group` (Editar + Borrar, `disabled`)
- 3 productos de ejemplo: Coca Cola P001, Hamburguesa P002, Papas fritas P003

**`.btn-group`**: grupo de botones donde el primero tiene border-radius izquierdo y el último derecho.

---

## Tab Pedidos

Layout `.split-5-7` (filtros izquierda, lista derecha).

**Filtros (card.pad-lg):**
- Select de estado (Todos/Pendiente/Pagado/Cancelado/Expirado)
- Input email del cliente
- Rango de fechas (date inputs)
- Botones Aplicar + Limpiar — `disabled`

**Lista de pedidos (.acc-item):**
3 órdenes en acordeón expandible:

| Pedido | Estado | Total |
|---|---|---|
| #1001 | Pendiente (tag-gold) | $8.200 |
| #1002 | Pagado (tag-success) | $3.700 |
| #1003 | Enviado (tag-blue) | $23.000 |

Cada `.acc-item.open` muestra tabla interna con productos del pedido y botones de acción (`disabled`).

---

## Tab Estadísticas

**KPI strip** (grid-4):
- Revenue total: $1.245.300 (trend up +12%)
- Pedidos: 342 (ticket prom $3.640)
- Conversión: 3,8% (up +0,4pp)
- Unidades vendidas: 890 (down −3%)

**`.stat-grid`** (2fr / 1fr):

**Gráfico de ventas** (card.pad-lg):
- 12 `.bar-col` con altura % como inline style (datos mock)
- Label de mes via `data-mo` attribute + `::after` CSS
- Nota: "se reemplazará por Chart.js cuando llegue el backend"

**Breakdown (card.pad-lg):**
- "Pedidos por estado" con 4 filas de `.donut-list` + `.bar` de progreso
- Pagados 62% (green), Pendientes 24% (gold), Cancelados 10% (coral), Expirados 4% (muted)

**Segundo `.stat-grid`** (2fr / 1fr):

**Top productos** (tabla): Hamburguesa 34%, Coca Cola 9%, Papas fritas 7%.

**Clientes** (card): barras Nuevos 41% / Recurrentes 59% + top 3 clientes por revenue.

---

## Tab Campañas

Layout `.split-5-7` (formulario izquierda, lista derecha).

**Formulario nueva campaña** (card.pad-lg):
- ID + Estado (`.frow`)
- Nombre de la campaña
- Tipo de descuento + porcentaje (`.frow`)
- Código (texto mono)
- Rango de fechas (`.frow`)
- Max usos + Target (`.frow`)
- Botones Crear + Limpiar — `disabled`

**Simulador de impacto** (card soft, borde dashed, bg `--paper-2`):
- Select de producto
- Fila de dos cards: "Precio original" ($4.500) y "Con descuento" ($3.825 en bg `--accent-soft`)
- Nota de ahorro

**Lista de campañas activas** (tabla):
| Código | Nombre | Estado | Período | Revenue |
|---|---|---|---|---|
| VERANO2026 | Promo Verano | Activa | 01 Ene → 31 Ene | $234.500 |
| BIENVENIDO | Welcome 20 | Activa | always-on | $89.200 |
| NAVIDAD25 | Navidad 2025 | Expirada | 01 Dic → 31 Dic | $567.800 |

**Card de rendimiento** (`.card.ink` / performance card):
- bg `var(--ink)` inline → `#222018` en dark mode via `!important`
- Grid 4 col: Ingresos $234.500 / Pedidos 847 / Ticket $2.769 / Tasa 68%
- Labels con `style="color: rgba(241,238,230,.5)"` → visibles sobre fondo oscuro
- HR con `rgba(241,238,230,.12)` → divisor sutil
- Texto final con `rgba(241,238,230,.7)` y link accent

---

## Footer

Usa `.dash-wrap` (no `.wrap-sm`). Links: Tiendas / Cuenta / Inicio.

---

## JS inline

```js
// Shop ID desde query params
const shopId = new URLSearchParams(location.search).get("shop_id") || "shop_001";
document.getElementById("shopIdLabel").textContent = shopId;

// Tabs
document.querySelectorAll(".dtab").forEach(t => {
  t.addEventListener("click", () => {
    // remueve active de todos, pone en clickeado
    // usa t.dataset.pane para encontrar el .pane correspondiente
  });
});

// Acordeón de pedidos
document.querySelectorAll("[data-acc] .acc-head").forEach(head => {
  head.addEventListener("click", () => {
    head.parentElement.classList.toggle("open");
  });
});
```

---

## Estilos inline page-specific

- `.dash-top`, `.crumb`, `.id-pill` → topbar oscuro y breadcrumb
- `.dash-page-head` → encabezado de página
- `.dash-wrap` → wrapper de 1180px
- `.frow` → grid 2 cols para pares de inputs
- `.photo-up`, `.photo-up .icon` → uploader de foto
- `.prod-row` → fila de producto con thumbnail
- `.stat-grid` → grid 2fr/1fr
- `.donut-list`, `.it` → lista de breakdown
- `.ord-meta`, `.mail` → meta info de órdenes
- `.btn-group` → grupo de botones conectados
- `.head-tools` → herramientas del topbar

---

## Dark mode — consideraciones especiales

Esta página tiene los casos más complejos del dark mode:

1. **`.dash-top`**: override explícito a `#0C0A08` con `!important`. Los textos del breadcrumb (`rgba(241,238,230,...)`) siguen siendo correctos porque el fondo sigue oscuro.

2. **`.card.ink` (performance card)**: override a `#222018` con `!important`. Bloquea el inline `style="background:var(--ink)"`. Los labels con `rgba(241,238,230,.5)` quedan visibles (texto claro sobre fondo oscuro).

3. **Botón ← Tiendas**: `style="color:var(--paper)"` flipearía a oscuro invisible. Override: `.dash-top .btn { color: var(--ink) !important }`.
