# Lista de tiendas · dshb.shops.html

> **Para IAs:** Documenta `dshb.shops.html`, la pantalla de workspace del usuario donde se listan todas sus tiendas. Contiene un strip de KPIs, las tiendas con dropdown de acciones y una card para agregar tienda nueva. La lógica JS en esta página es solo para abrir/cerrar los dropdowns. Si buscás el dashboard de una tienda individual, ver `page-dashboard.md`.

---

## Índice

1. [Rol de la página](#rol-de-la-página)
2. [Nav](#nav)
3. [Page head](#page-head)
4. [Summary strip](#summary-strip)
5. [Lista de tiendas (.shop)](#lista-de-tiendas-shop)
6. [Dropdown de acciones (.menu)](#dropdown-de-acciones-menu)
7. [Card Agregar tienda (.add-shop)](#card-agregar-tienda-add-shop)
8. [JS inline](#js-inline)
9. [Estilos inline page-specific](#estilos-inline-page-specific)

---

## Rol de la página

Workspace del usuario. Carga `auth.js` (guard). Muestra todas las tiendas del usuario como cards/filas con acciones, y el estado de su plan.

---

## Nav

Nav estándar con links: Inicio / **Mis tiendas** (activo) / Pagos / Cuenta.

---

## Page head

`.page-head` → flex `space-between`, con título display "Mis tiendas" y CTA `btn-primary` → `subcription.html` (nueva tienda).

---

## Summary strip

`.sum-strip` → grid 3 columnas, background `--line` (las celdas son `--card` creando efecto de rejilla).

| Celda | Valor |
|---|---|
| Tiendas activas | 2 / 5 incluidas |
| Pedidos · mes | 147 (+12% vs mes anterior, color accent) |
| Revenue · mes | $ 1.245.300 |

---

## Lista de tiendas (.shop)

Cada tienda es un `.shop` con grid `72px / 1fr / auto / auto`:

| Columna | Contenido |
|---|---|
| `.shop-logo` | Avatar 72px con letra de la tienda |
| `.shop-info` | Nombre + meta (tag de plan, shop_id, productos, estado) |
| `.num` | Pedidos/mes (oculto en mobile) |
| `.menu-wrap` | Dropdown de acciones |

**Logos:**
- `.shop-logo.a` → gradiente oscuro (`#1a1816 → #3a352e`), letra "U"
- `.shop-logo.b` → gradiente accent verde, letra "M"
- `.shop-logo.c` → gradiente coral

**Tiendas de ejemplo:**

| Tienda | Plan | ID | Productos | Estado |
|---|---|---|---|---|
| Urban Sneakers | Standard (tag-accent) | shop_001 | 87 | ● activa (accent) |
| Minimal Home Store | Free (tag-outline) | shop_002 | 6 | ○ borrador (mute) |

---

## Dropdown de acciones (.menu)

`.menu-wrap` → posición relativa. `.menu-btn` → botón 38px con ícono `⋮`. `.menu` → absolute, visible con `.open`.

Items del menú:

| Ítem | Destino | Clase |
|---|---|---|
| Gestionar | `dshb.manage.html?shop_id=X` | `.mi` |
| Suscripción | `subcription.html` | `.mi` |
| Renombrar | `#` (placeholder) | `.mi` |
| (separador) | — | `.sep` |
| Eliminar | `#` (placeholder) | `.mi.danger` |

`.mi.danger:hover` → bg `--danger-soft`.

---

## Card Agregar tienda (.add-shop)

`<a class="add-shop" href="subcription.html">` → estilo dashed border, flex centrado con `.plus` (cuadrado 36px, bg `--ink`, ícono ＋).

Hover: borde `--ink`, color `--ink`, bg `rgba(20,18,14,.025)` (overrideado en dark mode a `rgba(232,227,216,.03) !important`).

**Dark mode:** `.plus` flipea a crema/oscuro (ink bg → crema). Contrasta sobre el fondo oscuro.

---

## JS inline

```js
// Abre/cierra dropdowns — uno a la vez
document.querySelectorAll(".menu-btn").forEach(btn => {
  btn.addEventListener("click", e => {
    e.stopPropagation(); // no propaga al document
    const id = btn.dataset.menu; // "m1" o "m2"
    // cierra todos excepto el clickeado
    document.querySelectorAll(".menu").forEach(m => { if (m.id !== id) m.classList.remove("open"); });
    document.getElementById(id).classList.toggle("open");
  });
});

// Cierra todos al hacer click en cualquier parte del doc
document.addEventListener("click", () => {
  document.querySelectorAll(".menu").forEach(m => m.classList.remove("open"));
});
```

---

## Estilos inline page-specific

Todos usan variables CSS. Se adaptan automáticamente al dark mode.

- `.page-head` → layout del encabezado
- `.shop` → grid y hover de cada tienda
- `.shop-logo` + variantes `.a`, `.b`, `.c` → avatares con gradientes
- `.shop-info .nm`, `.meta`, `.sep` → tipografía de la tienda
- `.shop .num` → columna de pedidos
- `.menu-wrap`, `.menu-btn`, `.menu`, `.mi` → dropdown completo
- `.add-shop`, `.plus` → card de nueva tienda
- `.shops-list` → flex column con gap 12px
- `.sum-strip`, `.sum-cell` → strip de KPIs
