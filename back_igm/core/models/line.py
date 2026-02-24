from product import Product
from typing import Dict, Any


class Line:
    def __init__(self,product:Product,quantity:int):
        self.product = product
        self.cuantity = quantity

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Line":
        return Line(
            product=Product.fromJson(data["product"]),
            quantity=int(data["quantity"])
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "product": self.product.toJson(),
            "quantity": self.quantity
        }