# Category Manager

Sistema de gestión de categorías, productos y variantes con herencia de atributos y detección de impacto.

## Requisitos

- Python 3.11+
- `pip install fastapi uvicorn pydantic`
- No requiere base de datos externa (SQLite embebido)

## Estructura del proyecto

```
categories_fw/
├── main.py                  # Punto de entrada FastAPI
├── app/
│   ├── models.py            # Dominio: Category, Product, Variant, Attribute
│   ├── schemas.py           # Contratos Pydantic (request / response)
│   ├── services.py          # Lógica de negocio con patrón dos fases
│   ├── serializers.py       # Conversión modelo → schema de salida
│   ├── router.py            # 16 endpoints FastAPI
│   └── store.py             # Fachada sobre los repositorios
├── db_handler/
│   ├── schema.sql           # Esquema SQLite (8 tablas)
│   ├── db.py                # Conexión y arranque de la base
│   └── repositories.py      # AttributeRepo, CategoryRepo, ProductRepo, VariantRepo
├── front_new/               # Dashboard web
│   ├── index.html
│   ├── api.js
│   ├── service.js
│   ├── render.js
│   ├── events.js
│   └── animations.js
├── testing.py               # Tests visuales con matplotlib
└── DOCu/                    # Esta carpeta
```

## Cómo correr

```bash
cd categories_fw
uvicorn main:app --reload
```

## Puntos de acceso

| URL | Descripción |
|-----|-------------|
| `http://localhost:8000/front/index.html` | Dashboard web |
| `http://localhost:8000/docs` | Swagger UI (documentación interactiva) |
| `http://localhost:8000/redoc` | ReDoc |

## Correr los tests visuales

```bash
python3 testing.py
```

Abre una figura matplotlib con dos subplots mostrando el árbol antes/después de cada evento.

## Convenciones de atributos

| Tipo de dato | Uso recomendado |
|---|---|
| `text`, `number` | Siempre estáticos (info del producto) |
| `boolean` | Siempre dinámico (variante) |
| `enum` | Puede ser estático o dinámico según el caso |

- **Estático** (`is_static=True`): describe al producto (marca, color de referencia).
- **Dinámico** (`is_static=False`): es una dimensión de variante (talle, color elegible).
