# Documentación — app.py

La app es un **tester visual** del modelo. Su único propósito es hacer visible el comportamiento de `models.py` mientras se itera sobre las reglas de negocio. No es producción.

**Principio**: la app no tiene lógica de negocio propia. Llama métodos del modelo, muestra lo que devuelven, y aplica solo lo que el modelo indicó.

---

## Rol de cada parte

### Canvas (pestaña "Árbol")

Visualiza el árbol completo: Catálogo → Categorías → Subcategorías → Productos → Variantes.

- **Colores**: azul = categoría, verde = producto, violeta = variante
- **Doble clic** sobre un nodo → abre modal de edición
- **Arrastrar** un nodo sobre otro → intenta reparentarlo

### Pestaña "Atributos"

CRUD de atributos globales. Crear, editar, eliminar atributos y sus valores enum.

---

## Flujo de drag & drop (reparentar)

### Categoría → Categoría

1. Llama `src.impact_on_change_father(tgt)` → obtiene `(impact_out, impact_in)`
2. Muestra modal con exactamente lo que devolvió el modelo
3. Si confirma:
   - Aplica `impact_out`: quita AttributeImplementations de productos afectados
   - Aplica `impact_in`: agrega AttributeImplementations vacías a productos afectados
   - `src.father_categorie.subcategories.remove(src)` ← **GAP del modelo** (no hay remove_subcategory)
   - `tgt.add_subcategory(src)` ← modelo

### Producto → Categoría

1. Llama `src.impact_on_change_category(tgt)` → obtiene `(to_add, to_remove)`
2. Muestra modal con lo que devolvió el modelo
3. Si confirma:
   - Aplica el delta en `src.attributes_implementations`
   - `src.category.products.remove(src)` ← **GAP del modelo** (no hay remove_product)
   - `tgt.add_product(src)` ← modelo
   - `src.category = tgt` ← **GAP del modelo** (add_product no lo hace)

---

## Flujo de edición de categoría (doble clic)

Al guardar cambios en los atributos de una categoría:

1. Calcula `added = new_attrs - old_attrs` y `removed = old_attrs - new_attrs`
2. Para cada attr agregado: llama `cat.impact_on_add_attribute(attr)` ← modelo
3. Para cada attr removido: llama `cat.impact_on_remove_attribute(attr)` ← modelo
4. Si hay impacto: muestra modal
5. Si confirma: aplica impactos + muta `cat.attributes` ← **GAP del modelo** (no hay setter)

---

## Modal de impacto

Siempre muestra, incluso cuando el resultado es vacío ("sin impacto"). Esto es intencional para poder verificar qué está devolviendo el modelo en cada operación.

Muestra dos secciones:
- **SE AGREGAN**: qué atributos se incorporan a qué productos
- **SE QUITAN**: qué atributos se sacan de qué productos

---

## Gaps del modelo que la app cubre con mutación directa

| Operación | Código | Motivo |
|---|---|---|
| Quitar subcategoría de su padre | `parent.subcategories.remove(cat)` | No existe `remove_subcategory` |
| Quitar producto de su categoría | `cat.products.remove(product)` | No existe `remove_product` |
| Actualizar referencia de categoría en producto | `product.category = new_cat` | `add_product` no lo hace |
| Asignar atributos a categoría | `cat.attributes = [...]` | No existe setter |

---

## Lo que la app NO hace

- No valida variantes al mover un producto (el modelo detecta el delta en E6 pero no valida las variantes existentes)
- No aplica impactos dinámicos a variantes (los aplica a `product.attributes_implementations`, que es para estáticos)
- No persiste estado (todo en memoria, se pierde al cerrar)

---

## Datos de prueba (build_demo)

Al iniciar, carga este árbol:

```
Catálogo
├── Ropa  [attrs: Color (enum, dinámico), Talle (enum, dinámico)]
│   ├── Remeras  [attrs: Material (text, estático)]
│   │   ├── REM001 "Remera Básica"  [impl: Material="Algodón"]
│   │   │   ├── Var1: Color=Rojo, Talle=M, Material=Algodón
│   │   │   └── Var2: Color=Azul, Talle=L, Material=Algodón
│   │   └── REM002 "Polo Premium"
│   │       └── Var3: Color=Verde, Talle=S, Material=Piqué
│   └── Pantalones  [sin attrs propios]
└── Calzado  [sin attrs propios]
```

Atributos globales: Color, Talle, Material, Peso (g)
