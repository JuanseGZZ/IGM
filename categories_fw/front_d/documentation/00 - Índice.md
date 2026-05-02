# front_d — Documentación

Visor visual del catálogo de categorías/productos/variantes, implementado como SPA vanilla JS con layout organigrama.

---

## Archivos del proyecto

```
front_d/
├── index.html          ← HTML, estructura base
├── styles.css          ← todos los estilos (dark mode nativo)
├── models.js           ← modelos de dominio
├── charts.js           ← nodo visual Chart + constantes de tipo/color
├── btandvoid.js        ← marcadores de celda (Void, WireTop)
├── organigram.js       ← algoritmo de layout top-down + render al DOM
├── Handler.js          ← CRUD del árbol, serialización JSON
├── ui.js               ← creación del modal, helper showMenu
└── events.js           ← entry point: eventos, layout actors, drag&drop, zoom
```

---

## Documentos

| # | Documento | Qué cubre |
|---|---|---|
| 01 | [Arquitectura General](01%20-%20Arquitectura%20General.md) | Flujo de vida de un render, separación de capas |
| 02 | [Modelos de Dominio](02%20-%20Modelos%20de%20Dominio.md) | `models.js`: Category, Product, Variant, Attribute, AttributeSet |
| 03 | [Charts](03%20-%20Charts.md) | Clase `Chart`, tipos, colores, flags de dibujo |
| 04 | [Organigrama](04%20-%20Organigrama.md) | Algoritmo layout + render DOM, conectores, WireTop |
| 05 | [Handler](05%20-%20Handler.md) | CRUD del árbol, move, serialización |
| 06 | [Sistema de Eventos](06%20-%20Sistema%20de%20Eventos.md) | Layout actors, modales, drag & drop, zoom, pan |
| 07 | [UI y Estilos](07%20-%20UI%20y%20Estilos.md) | Modal, showMenu, variables CSS, dark mode |
