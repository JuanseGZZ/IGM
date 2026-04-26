# Arquitectura del sistema

## Capas

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Bootstrap 5 + Vanilla JS)                │
│  api.js → service.js → render.js / events.js        │
└────────────────────┬────────────────────────────────┘
                     │ HTTP (fetch)
┌────────────────────▼────────────────────────────────┐
│  FastAPI — router.py                                │
│  16 endpoints REST                                  │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  Capa de servicios — services.py                    │
│  CategoryService / ProductService                   │
│  Patrón dos fases (impacto → resolución)            │
└────────────┬───────────────────────┬────────────────┘
             │                       │
┌────────────▼────────┐  ┌───────────▼───────────────┐
│  Dominio — models.py │  │  store.py (fachada)       │
│  Category / Product  │  │  repositories.py          │
│  Variant / Attribute │  │  SQLite (db_handler/)     │
└─────────────────────┘  └───────────────────────────┘
```

## Flujo de una operación con impacto (ejemplo: E4 — agregar atributo)

```
1. Cliente → POST /categories/3/attributes/7   (body: {})
2. Router   → cat_svc.add_attribute(cat, attr, resolution=None, ...)
3. Service  → cat.impact_on_add_attribute(attr)   # computa pares (attrs, productos)
4. pairs != [] → retorna ImpactResponse { status: "impact_pending", impact: [...] }

5. Cliente muestra modal, usuario elige "eliminar" o "heredar" por grupo
6. Cliente → POST /categories/3/attributes/7   (body: { resolution: [...] })
7. Service  → _resolution_covers(resolution, pairs)   # valida cobertura completa
8. OK       → _apply_resolution(...)   # muta implementaciones en productos
9. cat.attributes.append(attr)
10. Retorna SuccessResponse { status: "ok" }
```

## Principios de diseño

- **Sin ORM**: todo acceso a SQLite usa `sqlite3` de la stdlib.
- **Dominio puro**: `models.py` no depende de ninguna capa de infraestructura.
- **Dos fases**: el router nunca muta nada si hay impacto sin resolver; siempre devuelve `impact_pending` primero.
- **Árbol en memoria**: `CategoryRepo.load_tree()` carga todo el árbol en tres queries y lo ensambla en Python. El árbol se re-carga en cada request (sin caché aún).
- **Hijos exclusivos**: una categoría puede tener subcategorías **o** productos, nunca ambos.
- **Sin ciclos**: al cambiar el padre se valida que el nuevo padre no sea descendiente de la categoría.

## Decisiones técnicas

| Decisión | Motivo |
|---|---|
| SQLite embebido | Sin dependencias externas, setup cero |
| Árbol en memoria | Simplifica la lógica de negocio; el modelo opera sobre objetos Python |
| Pydantic v2 | Validación de requests automática en FastAPI |
| Bootstrap 5 CDN | Sin build step en el frontend |
| Modales con Promises | Permite `await modal` dentro de un flujo async lineal |
