# Design System · styles.css

> **Para IAs:** Este archivo documenta todo el sistema de diseño de Ventium definido en `styles.css`. Contiene las variables CSS (paleta, tipografía, radii, sombras), todos los componentes reutilizables (nav, botones, cards, tags, inputs, tablas, KPIs, etc.) y el sistema de dark mode completo con la explicación de qué flipea y qué no. Si buscás el comportamiento de un componente específico, buscá su sección. Si buscás cómo funciona el dark mode, ir directamente a [Dark Mode](#dark-mode).

---

## Índice

1. [Variables CSS — Paleta](#variables-css--paleta)
2. [Variables CSS — Tipografía, Radii y Sombras](#variables-css--tipografía-radii-y-sombras)
3. [Reset y Base](#reset-y-base)
4. [Layout y Grid](#layout-y-grid)
5. [Tipografía](#tipografía)
6. [Brand mark](#brand-mark)
7. [Nav](#nav)
8. [Botones](#botones)
9. [Cards](#cards)
10. [Tags / Pills](#tags--pills)
11. [Inputs](#inputs)
12. [Tablas](#tablas)
13. [KPIs](#kpis)
14. [Barras de progreso](#barras-de-progreso)
15. [Acordeón](#acordeón)
16. [Tabs](#tabs)
17. [Dashboard Tabs (dtabs)](#dashboard-tabs-dtabs)
18. [Modal](#modal)
19. [Chart placeholder](#chart-placeholder)
20. [Componentes menores](#componentes-menores)
21. [Dark Mode](#dark-mode)

---

## Variables CSS — Paleta

Definidas en `:root`. La paleta "paper" usa tonos cálidos crema/beige para el modo claro.

```css
/* superficies (light mode) */
--paper:        #F1EEE6   /* body background — base */
--paper-2:      #E8E4D9   /* secciones alternas, table headers */
--card:         #FFFFFF   /* superficie de card */
--ink:          #15130F   /* texto primario + fondo de elementos destacados */
--ink-2:        #3A352E   /* texto secundario */
--mute:         #7B7669   /* texto apagado */
--mute-2:       #A39E92   /* muy apagado */
--line:         #DDD7C9   /* bordes */
--line-2:       #ECE7DC   /* divisores suaves (dentro de cards) */
```

```css
/* acentos */
--accent:       #0E5E3F   /* verde bosque — acento principal */
--accent-2:     #1A8557   /* verde ligeramente más claro */
--accent-soft:  #D9E8DD   /* fondo suave accent */
--accent-ink:   #082B1D   /* texto sobre fondo accent-soft */

--coral:        #C7553A   /* rojo-naranja */
--coral-soft:   #F3DDD3

--gold:         #A87826   /* dorado */
--gold-soft:    #F1E4C8

--blue:         #2E5B8E
--blue-soft:    #DCE6F0

--danger:       #B83A2C
--danger-soft:  #F3D9D3
--success:      #1A7E4F
--success-soft: #D6E9DC
--warning:      #A87826
```

**Regla de profundidad en light mode:** `--paper` (body) → `--paper-2` (sección alt) → `--card` (blanco, el nivel más alto). A más profundidad de layer, más claro.

---

## Variables CSS — Tipografía, Radii y Sombras

```css
/* fuentes */
--serif:  'Instrument Serif'    /* display / italic / decorativo */
--sans:   'Geist'               /* todo el texto funcional */
--mono:   'Geist Mono'          /* labels, código, datos numéricos */

/* radios de borde */
--r-sm:  6px
--r:     10px   /* default */
--r-lg:  14px
--r-xl:  20px
--r-2xl: 28px

/* sombras (apiladas) */
--sh-1:  sutil (1px offset)
--sh-2:  media (18px blur)
--sh-3:  fuerte (40px blur, para modales y overlays)
```

---

## Reset y Base

- `box-sizing: border-box` global
- `body`: fuente `--sans`, 15.5px, `color: var(--ink)`, `background: var(--paper)`
- `-webkit-font-smoothing: antialiased` + `text-rendering: optimizeLegibility`
- `font-feature-settings: 'ss01','ss02','cv11'` (features de Geist)

---

## Layout y Grid

**Wrappers:**
- `.wrap` → max 1180px, padding 0 24px
- `.wrap-sm` → max 880px
- `.wrap-xs` → max 560px

**Flex:**
- `.row` / `.col` → flex row / column
- `.gap-2` a `.gap-8` → gap 8px a 32px
- `.between`, `.center` → justify/align
- `.wrap-flex` → flex-wrap

**Grid:**
- `.grid-2` / `.grid-3` / `.grid-4` → grids con columnas iguales
- `.split` → 1.05fr / 0.95fr
- `.split-7-5` / `.split-5-7` → asimétricos
- Responsive: a 960px `.grid-3` y `.grid-4` pasan a 2 cols; a 600px todo pasa a 1 col

---

## Tipografía

| Clase | Descripción |
|---|---|
| `.display` | Serif italic, clamp(48px–92px), line-height .98 |
| `.display .roman` | Versión no italic del display |
| `h1` / `.h1` | Sans 600, 34px |
| `h2` / `.h2` | Sans 600, 24px |
| `h3` / `.h3` | Sans 600, 18px |
| `h4` / `.h4` | Sans 600, 15px |
| `.lead` | 17px, `--ink-2`, line-height 1.55 |
| `.muted` | `color: var(--mute)` |
| `.eyebrow` | Mono, 11px, uppercase, 0.14em tracking, inline-flex con dot |
| `.mono` | font-family mono |
| `.serif-em` | Serif italic sin peso |
| `.text-small` | 13.5px |
| `.text-xs` | 12px |

---

## Brand mark

`.brand` → inline-flex con `.brand-mark` (cuadrado 26px, border-radius 8px, bg `--ink`, texto `--paper`, serif italic "v") + texto "Ventium" + `.dot-tag` (punto accent verde).

Variante `.brand-mark.lg` → 36px.

**En dark mode:** `.brand-mark` toma `bg: var(--ink)` = crema `#E8E3D8` con texto `var(--paper)` = oscuro. Logo invertido (intencionalmente contrastante).

---

## Nav

`.nav` → sticky, z-index 50, vidrio esmerilado `backdrop-filter: blur(12px)`.

- `.nav-inner` → flex, altura 64px
- `.nav-links` → lista horizontal de links, pill hover sobre `rgba(20,18,14,.06)`, activo con `bg: var(--ink)`
- `.nav-burger` → visible solo mobile (<860px), abre dropdown `.nav.open .nav-links`

**Dark mode:** fondo `rgba(16,15,12,.93)`, hover `rgba(232,227,216,.06)`.

---

## Botones

Base `.btn` → inline-flex, gap 8px, padding 10x16, transition suave, `:active` baja 1px.

| Clase | Estilo |
|---|---|
| `.btn-primary` | bg `--ink`, text `--paper` |
| `.btn-accent` | bg `--accent` verde, text blanco |
| `.btn-outline` | bg `--card`, borde `--line`, hover borde `--ink` |
| `.btn-ghost` | transparente, hover `rgba(20,18,14,.06)` |
| `.btn-danger-soft` | bg `--danger-soft`, text `--danger` |

Tamaños: `.btn-lg` (14px 22px / 15px), `.btn-sm` (7px 12px / 13px), `.btn-block` (width 100%).

`.btn .arrow` → anima `translateX(3px)` en hover.

**Dark mode:** `.btn-primary` flipea a crema (CTAs "claros" en página oscura). `.btn-ghost:hover` usa `rgba(232,227,216,.07)`.

---

## Cards

`.card` → bg `--card`, borde `--line`, border-radius `--r-lg`, sombra `--sh-1`.

Variantes:
- `.card.soft` → bg `--paper-2`, sin borde ni sombra
- `.card.ghost` → transparente, sin sombra
- `.card.ink` → bg `--ink`, text `--paper` (elemento de alto contraste)

Padding helpers: `.pad` (20px), `.pad-lg` (28px), `.pad-xl` (36px).

`.card-line` → divisor horizontal `--line-2`.

**Dark mode:** `.card.ink` overrideado a `#222018` con borde `#363028` y `!important` (porque el HTML puede tener inline `style="background:var(--ink)"` que de otro modo flipearía a crema).

---

## Tags / Pills

`.tag` → inline-flex, mono 11px uppercase, bg `--paper-2`, borde `--line`. Contiene opcionalmente `.dot` (6px círculo).

Variantes de color:

| Clase | BG variable | Color texto |
|---|---|---|
| `.tag-accent` | `--accent-soft` | `--accent-ink` |
| `.tag-coral` | `--coral-soft` | `#7a2a17` |
| `.tag-gold` | `--gold-soft` | `#5e4514` |
| `.tag-blue` | `--blue-soft` | `#1f3f64` |
| `.tag-danger` | `--danger-soft` | `#6a1d14` |
| `.tag-success` | `--success-soft` | `#0e4a2d` |
| `.tag-ink` | `--ink` | `--paper` |
| `.tag-outline` | transparent | `--ink-2` |

**Dark mode:** Las variables de soft backgrounds flipean a tonos muy oscuros (ej. `--coral-soft: #20100E`). Los colores de texto hardcodeados se overridean en la media query: `.tag-coral { color: #D09888 }`, etc.

---

## Inputs

`.field` → columna con gap 6px (label + input + help).

`.label` → mono 12px uppercase, `--ink-2`.

`.input` / `.select` / `.textarea` → padding 11x14, borde `--line`, bg `--card`, focus: borde `--ink` + ring `rgba(20,18,14,.06)`.

`.select` → flecha SVG custom hardcodeada como data URI. **Dark mode:** la flecha usa stroke `#E8E3D8` para ser visible.

`.checkbox` → custom con `:checked` bg `--ink`, checkmark SVG blanco.

`.range` → slider custom, thumb 22px circular con borde `--paper`.

**Dark mode:** `.input:focus` ring usa `rgba(232,227,216,.07)`. Thumb borde usa `var(--paper)` = oscuro.

---

## Tablas

`.tbl` → border-collapse separate. `thead th` → mono 11px uppercase, bg `--paper-2`, borde inferior `--line`. `tbody tr:hover` → `rgba(20,18,14,.025)`. `tbl code` → inline code con bg `--paper-2`.

`.tbl-wrap` → overflow-x auto para scroll en mobile.

**Dark mode:** hover `rgba(232,227,216,.03)`.

---

## KPIs

`.kpi` → card con label (mono 11px), `.k-value` (sans 600 28px), `.k-trend` (12.5px muted con clases `.up` = accent y `.down` = danger).

---

## Barras de progreso

`.bar` → contenedor 6px height con `> span` para el fill.

Colores: `.bar` (default, ink) / `.bar.green` (accent) / `.bar.coral` / `.bar.gold` / `.bar.blue`.

---

## Acordeón

`.acc-item` → card con `.acc-head` (button full-width) y `.acc-body` (oculto por defecto).

`.acc-item.open .acc-body { display: block }`.

`.acc-chev` → rota 180° cuando `open`.

**Dark mode:** `.acc-head:hover` usa `rgba(232,227,216,.03)`.

---

## Tabs

`.tabs` → pill container con bg `--paper-2`. `.tab` → botón sin borde; `.tab.active` → bg `--card`, sombra `--sh-1`.

---

## Dashboard Tabs (dtabs)

`.dtabs` → flex horizontal con borde inferior `--line`. `.dtab` → sin borde lateral, borde inferior activo `2px var(--ink)`.

`.pane` → `display: none`. `.pane.active` → `display: block` con animación `fade` (opacity + translateY 4px).

---

## Modal

`.modal-backdrop` → fixed inset, bg `rgba(20,18,14,.45)`, blur 4px. `.modal-backdrop.open` → flex.

`.modal` → bg `--card`, border-radius `--r-xl`, max-width 440px, sombra `--sh-3`.

`.modal-head` + `.modal-body` → estructura interna. `.modal-close` → botón cuadrado 32px.

**Dark mode:** backdrop `rgba(0,0,0,.68)`.

---

## Chart placeholder

`.chart` → grid 12 columnas, height 220px, bg `--paper-2`, borde dashed `--line`.

`.bar-col` → gradient vertical accent → accent-2. `::after` → label de mes debajo.

---

## Componentes menores

- `.divider` → hr 1px `--line`. `.divider.dashed` → borde dashed.
- `.section-head` → contenedor de título de sección con `.title` (36px) y `.sub` (16px muted).
- `.footer` → borde superior, padding 36px/48px, texto `--mute`.
- `.thumb` → imagen 44px cuadrada con borde y bg `--paper-2`.
- `.ph` → placeholder de imagen con patrón diagonal de líneas `rgba(20,18,14,.04)`.
- `.eyebrow .dot` → punto 6px con bg `--accent`.

---

## Dark Mode

Implementado como bloque `@media (prefers-color-scheme: dark)` al final de `styles.css`. No requiere clase en el HTML; se activa por preferencia del sistema.

### Filosofía de diseño dark mode

- **Warm-neutral**: base oscura con tinte cálido mínimo — no frío, no marrón
- **Elevación visible**: 3 capas (`--paper` → `--paper-2` → `--card`) claramente distintas
- **Jerarquía de texto**: opacidades al 88/63/38/22% (estándar Material Design)
- **Rim lights**: `--sh-3` lleva `0 0 0 1px rgba(255,255,255,.06)` → superficies elevadas brillan
- **Glows en accent**: botones y plan featured tienen aura verde suave
- **Inputs sunken**: usan `--paper-2` (más oscuro que `--card`) → sensación de profundidad
- **Backdrop blur**: modal usa `backdrop-filter: blur(8px)` para look premium

### Regla de profundidad

| Variable | Light | Dark | Rol |
|---|---|---|---|
| `--paper` | `#F1EEE6` | `#0F0E0D` | Body — el piso |
| `--paper-2` | `#E8E4D9` | `#161412` | Secciones / inputs (sunken) |
| `--card` | `#FFFFFF` | `#1D1A17` | Surface de card |
| `--ink` | `#15130F` | `#EDE8DF` | Texto primario (~88%) |
| `--ink-2` | `#3A352E` | `#AAA49A` | Texto secundario (~63%) |
| `--mute` | `#7B7669` | `#6E6860` | Texto apagado (~38%) |
| `--mute-2` | `#A39E92` | `#3D3830` | Muy apagado (~22%) |
| `--line` | `#DDD7C9` | `#2C2824` | Bordes |
| `--line-2` | `#ECE7DC` | `#1E1B18` | Divisores suaves |

### Acentos en dark mode

Más saturados/brillantes que en light. El verde `#38B578` supera la ratio WCAG AA (4.5:1) sobre `--card`.

| Variable | Light | Dark |
|---|---|---|
| `--accent` | `#0E5E3F` | `#38B578` |
| `--accent-soft` | `#D9E8DD` | `#0A1D13` |
| `--accent-ink` | `#082B1D` | `#7DD4A8` |
| `--coral` | `#C7553A` | `#D96250` |
| `--coral-soft` | `#F3DDD3` | `#1E0D0A` |
| `--gold` | `#A87826` | `#C49440` |
| `--gold-soft` | `#F1E4C8` | `#1B1407` |
| `--blue` | `#2E5B8E` | `#5A96D4` |
| `--blue-soft` | `#DCE6F0` | `#0C1825` |

### Efectos especiales del dark mode

```css
/* Rim light en superficies muy elevadas */
--sh-3: 0 0 0 1px rgba(255,255,255,.06), 0 24px 48px -20px rgba(0,0,0,.88);

/* Glow en btn-accent (reposo → hover) */
box-shadow: 0 0 0 1px rgba(56,181,120,.18), 0 4px 16px -4px rgba(56,181,120,.3);
box-shadow: 0 0 0 1px rgba(56,181,120,.28), 0 6px 22px -4px rgba(56,181,120,.4);

/* Glow en .plan.featured */
box-shadow: 0 0 0 1px rgba(56,181,120,.28), 0 8px 32px -8px rgba(56,181,120,.2);

/* Focus ring accent verde */
.input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(56,181,120,.15); }

/* Nav premium glass */
.nav { background: rgba(15,14,13,.9); border-bottom: 1px solid rgba(255,255,255,.07); }

/* Modal backdrop premium */
.modal-backdrop { background: rgba(0,0,0,.72); backdrop-filter: blur(8px); }
```

### Qué flipea naturalmente (no necesita override)

Cualquier elemento con `var(--ink)` como fondo se invierte a crema `#EDE8DF`. Es intencional:

- `.btn-primary` → CTA crema que destaca sobre página oscura
- `.nav-links a.active` → pill crema (sección activa visible)
- `.brand-mark` → logo invertido crema/oscuro
- `.seg button.active` → filtro activo en payments
- `.stepper .s.active` → paso activo en subscription
- `.add-shop .plus` → ícono + visible
- `.ticket-top` → header crema del ticket (contraste intencional)
- `.contact-card` → card crema en sección de contacto

### Overrides explícitos (NO deben invertirse)

| Selector | Override | Razón |
|---|---|---|
| `.plan.featured` | `bg: #0C1C14`, borde + glow accent | Featured oscuro con corona verde = premium |
| `.card.ink` | `bg: #16130F` con `!important` | El HTML tiene `style="background:var(--ink)"` inline |
| `.dash-top` | `bg: #080706` con `!important` | Topbar del dashboard debe ser muy oscuro siempre |
| `.plan.featured` hijos | `color: var(--ink) !important` | `style="color:var(--paper)"` flipearía a oscuro invisible |
| `.dash-top .btn` | `color: var(--ink) !important` | `style="color:var(--paper)"` flipearía a texto invisible |

### Overrides por rgba hardcodeados

| Elemento | Solución |
|---|---|
| Select SVG arrow | Reemplazada: stroke `#EDE8DF` |
| `.nav` bg | `rgba(15,14,13,.9)` + borde `rgba(255,255,255,.07)` |
| `.marquee` bg | `rgba(21,19,16,.88)` |
| Hover states | `rgba(237,232,223,.03/.04)` |
| `.contact-card .contact-row` | Selector 0,2,0 más específico → sin `!important` |
| Tags colored | Texto overrideado a versiones claras (ej. coral → `#E89E8A`) |

### color-scheme

```css
:root { color-scheme: dark; }
```
Activa scrollbars, inputs de fecha y controles nativos del browser en modo oscuro.
