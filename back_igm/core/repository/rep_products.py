from db.crud_products import CrudProducts
from models.product import Product
from typing import List


class ProductRepository:

    @staticmethod
    def bring_all_products_from_shop(id_shop: str, limit: int = 50, offset: int = 0) -> List[Product]:
        rows = CrudProducts.list_by_shop(id_shop, limit, offset)

        return [Product.fromJson(row) for row in rows]