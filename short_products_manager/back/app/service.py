import json

from .dto import (
    AttributeDTO, AttributeImplementationDTO,
    BrandDTO, ProductDTO, StateDTO, StockDTO, VariantDTO,
)
from .repository import (
    AttributeRepository, BrandRepository,
    ProductRepository, StockRepository, VariantRepository,
)


class ProductService:
    def __init__(self) -> None:
        self._brands   = BrandRepository()
        self._products = ProductRepository()
        self._attrs    = AttributeRepository()
        self._variants = VariantRepository()
        self._stocks   = StockRepository()

    # ── Bring ─────────────────────────────────────────────────────────────────

    def bring(self) -> StateDTO:
        brands_map = {b["id"]: BrandDTO(**b) for b in self._brands.get_all()}

        products: list[ProductDTO] = []
        for row in self._products.get_all():
            pid = row["id"]

            attrs = [
                AttributeDTO(
                    id=a["id"],
                    key=a["key"],
                    values=json.loads(a["attr_values"]),
                )
                for a in self._attrs.get_by_product(pid)
            ]

            variants = [
                VariantDTO(
                    id=v["id"],
                    price=v["price"],
                    implementations=[
                        AttributeImplementationDTO(**i)
                        for i in json.loads(v["implementations"])
                    ],
                    historical_stocks=[
                        StockDTO(**s)
                        for s in self._stocks.get_by_variant(v["id"])
                    ],
                )
                for v in self._variants.get_by_product(pid)
            ]

            products.append(
                ProductDTO(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"] or "",
                    brand=brands_map.get(row["brand_id"]) if row["brand_id"] else None,
                    attributes=attrs,
                    variants=variants,
                    photo=row["photo"],
                )
            )

        return StateDTO(products=products, brands=list(brands_map.values()))

    # ── Save ──────────────────────────────────────────────────────────────────

    def save(self, state: StateDTO) -> None:
        # Full replace — mirrors the frontend Bring/Save model.
        # Delete order avoids leaving orphaned child rows.
        self._stocks.delete_all()
        self._variants.delete_all()
        self._attrs.delete_all()
        self._products.delete_all()
        self._brands.delete_all()

        for brand in state.brands:
            self._brands.upsert({"id": brand.id, "name": brand.name})

        for product in state.products:
            self._products.upsert(
                {
                    "id":          product.id,
                    "name":        product.name,
                    "description": product.description,
                    "brand_id":    product.brand.id if product.brand else None,
                    "photo":       product.photo,
                }
            )
            for attr in product.attributes:
                self._attrs.upsert(
                    {
                        "id":         attr.id,
                        "product_id": product.id,
                        "key":        attr.key,
                        "attr_values": json.dumps(attr.values),
                    }
                )
            for variant in product.variants:
                self._variants.upsert(
                    {
                        "id":              variant.id,
                        "product_id":      product.id,
                        "price":           variant.price,
                        "implementations": json.dumps(
                            [i.model_dump() for i in variant.implementations]
                        ),
                    }
                )
                for stock in variant.historical_stocks:
                    self._stocks.upsert(
                        {
                            "id":              stock.id,
                            "variant_id":      variant.id,
                            "quantity":        stock.quantity,
                            "date":            stock.date,
                            "cost_unit_price": stock.cost_unit_price,
                        }
                    )
