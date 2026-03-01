from .product import Product
from typing import Dict, Any


class Line:
    def __init__(self,id:int,product:Product,quantity:int):
        self.id = id 
        self.product = product
        self.quantity = quantity

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Line":
        return Line(
            id = int(data["id"]),
            product=Product.fromJson(data["product"]),
            quantity=int(data["quantity"])
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id":self.id,
            "product": self.product.toJson(),
            "quantity": self.quantity
        }