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
├── organigram.js       ← algoritmo de layout top-down (árbol → matriz 2D)
├── Handler.js          ← CRUD del árbol, serialización JSON
├── Gestor.js           ← árbol espejo de dominio, validaciones y análisis de impacto
├── ui.js               ← modal de edición, showMenu, showGestorDialog
├── events.js           ← entry point: eventos, layout actors, drag&drop, zoom
│
├── stores/
│   ├── attrStore.js    ← almacén global de atributos (localStorage "igm-attrs")
│   └── catalogStore.js ← persistencia del árbol de catálogo (localStorage "igm-catalog")
│
└── renders/
    ├── renderBoard.js      ← construcción DOM de cartas, conectores y botones
    ├── renderEditModal.js  ← renderAttrList + renderVariantImpls (modal de edición)
    ├── renderAttrsModal.js ← renderAttrRows + renderEnumValues (modal CRUD de atributos)
    └── renderAttrPicker.js ← renderPicker con 4 listas (modal selector de atributos)
```

> `attrStore.js` en la raíz es un re-export de `stores/attrStore.js` por compatibilidad.

---

## Documentos

| # | Documento | Qué cubre |
|---|---|---|
| 01 | [Arquitectura General](01%20-%20Arquitectura%20General.md) | Flujo de vida de un render, separación de capas |
| 02 | [Modelos de Dominio](02%20-%20Modelos%20de%20Dominio.md) | `models.js`: Category, Product, Variant, Attribute, AttributeSet |
| 03 | [Charts](03%20-%20Charts.md) | Clase `Chart`, tipos, colores, flags de dibujo |
| 04 | [Organigrama](04%20-%20Organigrama.md) | Algoritmo layout (árbol → matriz 2D), conectores, WireTop |
| 05 | [Handler](05%20-%20Handler.md) | CRUD del árbol, move, serialización |
| 06 | [Sistema de Eventos](06%20-%20Sistema%20de%20Eventos.md) | Layout actors, modales, drag & drop, zoom, pan |
| 07 | [UI y Estilos](07%20-%20UI%20y%20Estilos.md) | Modal, showMenu, showGestorDialog, variables CSS, dark mode |
| 08 | [Gestor](08%20-%20Gestor.md) | Árbol espejo, validaciones, análisis de impacto, flujos aditivo/destructivo/mixto |
| 09 | [Stores](09%20-%20Stores.md) | `attrStore` y `catalogStore`: qué persisten y cómo usarlos |
| 10 | [Renders](10%20-%20Renders.md) | `renders/`: contratos de cada función de render, separación DOM/lógica |
