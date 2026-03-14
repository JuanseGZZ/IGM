"""
models.py — Schema híbrido Opción C

Dos conceptos separados:
  - Opciones       → diferencian variantes (Color, Talla). Generan SKUs.
  - Atributos      → describen el producto (Material, Peso). No generan variantes.

Entidades:
  Catálogo:     Category, Product
  Opciones:     ProductOption, ProductOptionValue
  Variantes:    Variant, VariantOptionValue
  Atributos:    Attribute, AttributeEnumValue, CategoryAttribute, ProductAttributeValue
  Helper:       VariantGenerator
"""

from __future__ import annotations
from itertools import product as cartesian_product
from typing import Optional, Union
from dataclasses import dataclass


# ──────────────────────────────────────────────
# Tipos
# ──────────────────────────────────────────────

AttributeDataType = str  # "enum" | "number" | "boolean" | "text"
FilterType        = str  # "enum_multi" | "range" | "toggle" | "text"
UIControl         = str  # "chips" | "dropdown" | "checkbox" | "slider" | "toggle"
AttributeValue    = Union[str, float, int, bool]

VALID_DATA_TYPES   = {"enum", "number", "boolean", "text"}
VALID_FILTER_TYPES = {"enum_multi", "range", "toggle", "text", None}
VALID_UI_CONTROLS  = {"chips", "dropdown", "checkbox", "slider", "toggle", None}


# ──────────────────────────────────────────────
# Category
# ──────────────────────────────────────────────

@dataclass
class Category:
    """
    Categoría de productos.
    Define qué atributos descriptivos aplican a sus productos
    a través de CategoryAttribute.
    """
    id:   int
    name: str

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Category.name no puede estar vacío")

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name!r})"


# ──────────────────────────────────────────────
# Product
# ──────────────────────────────────────────────

@dataclass
class Product:
    """
    Producto base. Contiene la información común a todas sus variantes.

    Las diferencias entre variantes (Color, Talla) → ProductOption.
    Las características descriptivas (Material, Peso) → ProductAttributeValue.
    """
    id:          int
    category_id: int
    title:       str
    description: Optional[str] = None
    brand:       Optional[str] = None
    is_active:   bool = True

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Product.title no puede estar vacío")

    def __repr__(self) -> str:
        return f"Product(id={self.id}, title={self.title!r}, brand={self.brand!r})"


# ──────────────────────────────────────────────
# ProductOption
# ──────────────────────────────────────────────

@dataclass
class ProductOption:
    """
    Dimensión que diferencia variantes de un producto.

    Cada producto puede tener múltiples opciones.
    Ejemplos: "Color", "Talla", "Almacenamiento".

    position: orden de presentación en la UI (0-indexed).

    Relación:
        Product 1 ──< ProductOption 1 ──< ProductOptionValue
    """
    id:         int
    product_id: int
    name:       str
    position:   int = 0

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("ProductOption.name no puede estar vacío")
        if self.position < 0:
            raise ValueError("ProductOption.position debe ser >= 0")

    def __repr__(self) -> str:
        return f"ProductOption(id={self.id}, name={self.name!r}, position={self.position})"


# ──────────────────────────────────────────────
# ProductOptionValue
# ──────────────────────────────────────────────

@dataclass
class ProductOptionValue:
    """
    Valor concreto de una opción de producto.

    Ejemplo:
        ProductOption "Color" → ["Negro", "Blanco", "Rojo"]
        ProductOption "Talla" → ["41", "42", "43", "44"]

    sort_order: orden de presentación dentro de la opción.
    """
    id:         int
    option_id:  int
    value:      str
    sort_order: int = 0

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("ProductOptionValue.value no puede estar vacío")

    def __repr__(self) -> str:
        return f"ProductOptionValue(id={self.id}, value={self.value!r})"


# ──────────────────────────────────────────────
# Variant
# ──────────────────────────────────────────────

@dataclass
class Variant:
    """
    Combinación específica de opciones de un producto.
    Tiene su propio SKU, precio y stock.

    Las opciones que definen esta variante se vinculan a través de
    VariantOptionValue (tabla pivote).

    Ejemplo:
        Air Max 90 + Color:Negro + Talla:42 → Variant(sku="AM90-NEG-42", price_cents=15000)

    price_cents: precio en centavos para evitar aritmética de punto flotante.
    """
    id:          int
    product_id:  int
    sku:         str
    price_cents: int
    stock:       int  = 0
    is_active:   bool = True

    def __post_init__(self):
        if not self.sku.strip():
            raise ValueError("Variant.sku no puede estar vacío")
        if self.price_cents < 0:
            raise ValueError("Variant.price_cents debe ser >= 0")
        if self.stock < 0:
            raise ValueError("Variant.stock debe ser >= 0")

    @property
    def price(self) -> float:
        """Precio en unidades (no centavos). Solo lectura."""
        return self.price_cents / 100

    def __repr__(self) -> str:
        return f"Variant(id={self.id}, sku={self.sku!r}, price={self.price:.2f}, stock={self.stock})"


# ──────────────────────────────────────────────
# VariantOptionValue
# ──────────────────────────────────────────────

@dataclass
class VariantOptionValue:
    """
    Tabla pivote: vincula una Variant con los ProductOptionValues que la definen.

    Una variante tendrá exactamente un VariantOptionValue
    por cada ProductOption de su producto.

    Ejemplo para Air Max 90 Negro Talla 42:
        VariantOptionValue(variant_id=1, option_value_id=<id Negro>)
        VariantOptionValue(variant_id=1, option_value_id=<id 42>)
    """
    variant_id:      int
    option_value_id: int

    def __repr__(self) -> str:
        return (
            f"VariantOptionValue("
            f"variant_id={self.variant_id}, "
            f"option_value_id={self.option_value_id})"
        )


# ──────────────────────────────────────────────
# Attribute
# ──────────────────────────────────────────────

@dataclass
class Attribute:
    """
    Definición de un atributo descriptivo reutilizable entre categorías.

    Los atributos NO generan variantes. Describen características
    del producto compartidas por todas sus variantes.

    Ejemplos:
        Attribute(key="peso_g",      name="Peso (g)",    data_type="number")
        Attribute(key="material",    name="Material",    data_type="text")
        Attribute(key="waterproof",  name="Impermeable", data_type="boolean")
        Attribute(key="pais_origen", name="País",        data_type="enum")

    data_type determina qué tipo de valor acepta:
        "text"    → str
        "number"  → float / int
        "boolean" → bool
        "enum"    → uno de los AttributeEnumValues asociados
    """
    id:        int
    key:       str
    name:      str
    data_type: AttributeDataType

    def __post_init__(self):
        if not self.key.strip():
            raise ValueError("Attribute.key no puede estar vacío")
        if not self.name.strip():
            raise ValueError("Attribute.name no puede estar vacío")
        if self.data_type not in VALID_DATA_TYPES:
            raise ValueError(
                f"Attribute.data_type inválido: {self.data_type!r}. "
                f"Válidos: {VALID_DATA_TYPES}"
            )

    def __repr__(self) -> str:
        return f"Attribute(id={self.id}, key={self.key!r}, data_type={self.data_type!r})"


# ──────────────────────────────────────────────
# AttributeEnumValue
# ──────────────────────────────────────────────

@dataclass
class AttributeEnumValue:
    """
    Valor permitido para un Attribute de tipo "enum".

    Solo existe para atributos con data_type == "enum".
    Define el universo de valores válidos para ese atributo.

    Ejemplo:
        Attribute(key="pais_origen") →
            AttributeEnumValue(value="Argentina", sort_order=0)
            AttributeEnumValue(value="Brasil",    sort_order=1)
            AttributeEnumValue(value="China",     sort_order=2)
    """
    id:           int
    attribute_id: int
    value:        str
    sort_order:   int = 0

    def __post_init__(self):
        if not self.value.strip():
            raise ValueError("AttributeEnumValue.value no puede estar vacío")

    def __repr__(self) -> str:
        return f"AttributeEnumValue(id={self.id}, value={self.value!r}, sort_order={self.sort_order})"


# ──────────────────────────────────────────────
# CategoryAttribute
# ──────────────────────────────────────────────

@dataclass
class CategoryAttribute:
    """
    Configura qué atributos descriptivos aplican a una categoría
    y cómo se comportan en filtros y formularios.

    Tabla pivote con metadata entre Category y Attribute.

    Nota: is_option fue eliminado vs el modelo anterior.
    Si algo diferencia variantes → ProductOption.
    Si algo describe el producto → Attribute + CategoryAttribute.

    is_filterable: aparece como filtro en el listado de categoría
    is_required:   obligatorio al crear un producto en esta categoría
    filter_type:   cómo se presenta el filtro en la UI
    ui_control:    qué componente UI usar para ingresar/filtrar el valor
    """
    category_id:   int
    attribute_id:  int
    is_filterable: bool = False
    is_required:   bool = False
    filter_type:   Optional[FilterType] = None
    ui_control:    Optional[UIControl]  = None

    def __post_init__(self):
        if self.filter_type not in VALID_FILTER_TYPES:
            raise ValueError(f"CategoryAttribute.filter_type inválido: {self.filter_type!r}")
        if self.ui_control not in VALID_UI_CONTROLS:
            raise ValueError(f"CategoryAttribute.ui_control inválido: {self.ui_control!r}")
        if self.is_filterable and not self.filter_type:
            raise ValueError("Si is_filterable=True, filter_type es requerido")

    def __repr__(self) -> str:
        return (
            f"CategoryAttribute("
            f"category_id={self.category_id}, "
            f"attribute_id={self.attribute_id}, "
            f"filterable={self.is_filterable}, "
            f"required={self.is_required})"
        )


# ──────────────────────────────────────────────
# ProductAttributeValue
# ──────────────────────────────────────────────

@dataclass
class ProductAttributeValue:
    """
    Valor de un atributo descriptivo para un producto específico.

    Va al PRODUCTO (no a la variante) porque describe características
    compartidas por todas las variantes del producto.

    value: valor Python tipado. En Postgres se guarda como JSONB:
        text:    {"text": "Cuero sintético"}
        number:  {"number": 310.5}
        boolean: {"bool": false}
        enum:    {"enum_id": 3, "enum_value": "Argentina"}

    enum_value_id: FK lógica a AttributeEnumValue.
                   Requerida cuando el atributo es de tipo "enum".
                   Garantiza integridad referencial para valores enum.
    """
    product_id:    int
    attribute_id:  int
    value:         AttributeValue
    enum_value_id: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.value, (str, float, int, bool)):
            raise TypeError(
                f"ProductAttributeValue.value debe ser str, float, int o bool. "
                f"Recibido: {type(self.value).__name__}"
            )

    def to_jsonb(self) -> dict:
        """
        Convierte el valor a la estructura jsonb para Postgres.

        Llamado internamente por el CRUD al persistir.
        El tipo bool debe ir antes de int porque bool es subclase de int en Python.
        """
        if self.enum_value_id is not None:
            return {"enum_id": self.enum_value_id, "enum_value": str(self.value)}
        if isinstance(self.value, bool):
            return {"bool": self.value}
        if isinstance(self.value, (int, float)):
            return {"number": float(self.value)}
        return {"text": self.value}

    @classmethod
    def from_jsonb(
        cls,
        product_id: int,
        attribute_id: int,
        jsonb: dict,
    ) -> "ProductAttributeValue":
        """
        Reconstruye un ProductAttributeValue desde el jsonb almacenado en Postgres.
        Llamado internamente por el CRUD al leer.
        """
        if "enum_id" in jsonb:
            return cls(product_id, attribute_id, jsonb["enum_value"], jsonb["enum_id"])
        if "bool"    in jsonb:
            return cls(product_id, attribute_id, jsonb["bool"])
        if "number"  in jsonb:
            return cls(product_id, attribute_id, jsonb["number"])
        if "text"    in jsonb:
            return cls(product_id, attribute_id, jsonb["text"])
        raise ValueError(f"Estructura jsonb desconocida: {jsonb}")

    def __repr__(self) -> str:
        return (
            f"ProductAttributeValue("
            f"product_id={self.product_id}, "
            f"attribute_id={self.attribute_id}, "
            f"value={self.value!r})"
        )


# ──────────────────────────────────────────────
# VariantGenerator
# ──────────────────────────────────────────────

class VariantGenerator:
    """
    Genera variantes como producto cartesiano de las opciones de un producto.

    Ejemplo con 2 opciones:
        Color  → [Negro, Blanco]
        Talla  → [42, 43, 44]
        → genera 6 variantes: NEG-42, NEG-43, NEG-44, BLA-42, BLA-43, BLA-44

    Uso:
        gen = VariantGenerator(
            product_id=1,
            options_with_values=[
                (color_opt, [negro, blanco]),
                (talla_opt, [t42, t43, t44]),
            ],
            base_price_cents=15000,
            sku_prefix="AM90",
            starting_id=1,
        )
        variants, vovs = gen.generate()
        # variants → lista de Variant
        # vovs     → lista de VariantOptionValue (pivote)
    """

    def __init__(
        self,
        product_id: int,
        options_with_values: list[tuple[ProductOption, list[ProductOptionValue]]],
        base_price_cents: int,
        sku_prefix: str = "",
        starting_id: int = 1,
    ):
        if not options_with_values:
            raise ValueError("Se necesita al menos una opción para generar variantes")
        if base_price_cents < 0:
            raise ValueError("base_price_cents debe ser >= 0")

        self.product_id          = product_id
        self.options_with_values = options_with_values
        self.base_price_cents    = base_price_cents
        self.sku_prefix          = sku_prefix
        self.starting_id         = starting_id

    def generate(self) -> tuple[list[Variant], list[VariantOptionValue]]:
        """
        Retorna (variants, variant_option_values).
        Los SKUs se arman como: PREFIX-VAL1-VAL2-...-ID
        """
        value_lists  = [values for _, values in self.options_with_values]
        combinations = list(cartesian_product(*value_lists))

        variants: list[Variant]            = []
        vovs:     list[VariantOptionValue] = []
        vid = self.starting_id

        for combo in combinations:
            variants.append(Variant(
                id=vid,
                product_id=self.product_id,
                sku=self._build_sku(combo, vid),
                price_cents=self.base_price_cents,
            ))
            for option_value in combo:
                vovs.append(VariantOptionValue(
                    variant_id=vid,
                    option_value_id=option_value.id,
                ))
            vid += 1

        return variants, vovs

    def _build_sku(self, combo: tuple[ProductOptionValue, ...], vid: int) -> str:
        parts = [self.sku_prefix] + [v.value[:4].upper().replace(" ", "") for v in combo]
        return "-".join(filter(None, parts)) + f"-{vid}"


# ──────────────────────────────────────────────
# Ejemplo de uso
# ──────────────────────────────────────────────

if __name__ == "__main__":

    # 1. Catálogo base
    cat     = Category(id=1, name="Zapatillas")
    product = Product(id=1, category_id=cat.id, title="Air Max 90", brand="Nike")

    # 2. Opciones del producto
    color_opt = ProductOption(id=1, product_id=product.id, name="Color", position=0)
    talla_opt = ProductOption(id=2, product_id=product.id, name="Talla", position=1)

    # 3. Valores de cada opción
    negro  = ProductOptionValue(id=1, option_id=color_opt.id, value="Negro",  sort_order=0)
    blanco = ProductOptionValue(id=2, option_id=color_opt.id, value="Blanco", sort_order=1)
    t42    = ProductOptionValue(id=3, option_id=talla_opt.id, value="42",     sort_order=0)
    t43    = ProductOptionValue(id=4, option_id=talla_opt.id, value="43",     sort_order=1)
    t44    = ProductOptionValue(id=5, option_id=talla_opt.id, value="44",     sort_order=2)

    # 4. Generar variantes automáticamente (2 × 3 = 6)
    gen = VariantGenerator(
        product_id=product.id,
        options_with_values=[
            (color_opt, [negro, blanco]),
            (talla_opt, [t42, t43, t44]),
        ],
        base_price_cents=15000,
        sku_prefix="AM90",
    )
    variants, vovs = gen.generate()

    print(f"Variantes generadas: {len(variants)}")
    for v in variants:
        print(f"  {v}")

    # 5. Atributos descriptivos
    peso_attr     = Attribute(id=1, key="peso_g",      name="Peso (g)",    data_type="number")
    material_attr = Attribute(id=2, key="material",    name="Material",    data_type="text")
    wp_attr       = Attribute(id=3, key="waterproof",  name="Impermeable", data_type="boolean")
    pais_attr     = Attribute(id=4, key="pais_origen", name="País",        data_type="enum")

    # 6. Valores permitidos para el enum
    arg = AttributeEnumValue(id=1, attribute_id=pais_attr.id, value="Argentina", sort_order=0)
    bra = AttributeEnumValue(id=2, attribute_id=pais_attr.id, value="Brasil",    sort_order=1)

    # 7. Configurar atributos de la categoría
    CategoryAttribute(category_id=cat.id, attribute_id=peso_attr.id,
                      is_filterable=True,  filter_type="range",      ui_control="slider")
    CategoryAttribute(category_id=cat.id, attribute_id=material_attr.id,
                      is_filterable=False)
    CategoryAttribute(category_id=cat.id, attribute_id=wp_attr.id,
                      is_filterable=True,  filter_type="toggle",     ui_control="toggle")
    CategoryAttribute(category_id=cat.id, attribute_id=pais_attr.id,
                      is_filterable=True,  is_required=True,
                      filter_type="enum_multi", ui_control="chips")

    # 8. Valores de atributos del producto
    pavs = [
        ProductAttributeValue(product_id=product.id, attribute_id=peso_attr.id,     value=310.0),
        ProductAttributeValue(product_id=product.id, attribute_id=material_attr.id, value="Cuero sintético"),
        ProductAttributeValue(product_id=product.id, attribute_id=wp_attr.id,       value=False),
        ProductAttributeValue(product_id=product.id, attribute_id=pais_attr.id,     value="Argentina", enum_value_id=arg.id),
    ]

    print(f"\nAtributos de {product.title}:")
    for pav in pavs:
        print(f"  {pav}  →  jsonb: {pav.to_jsonb()}")

    # 9. Round-trip desde jsonb (simula lo que hace el CRUD al leer de Postgres)
    print(f"\nRound-trip desde jsonb:")
    for pav in pavs:
        reconstructed = ProductAttributeValue.from_jsonb(
            pav.product_id, pav.attribute_id, pav.to_jsonb()
        )
        assert reconstructed.value == pav.value
        print(f"  ✓  {reconstructed}")
