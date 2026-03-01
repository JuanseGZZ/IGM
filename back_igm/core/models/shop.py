from .product import Product
from .client import Client

from typing import List, Dict, Any

class Shop:
    def __init__(self,id:str, name:str, products:List[Product],clients:List[Client]):
        self.id = id
        self.name = name
        self.products = products
        self.clients = clients

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Shop":
        return Shop(
            id=str(data["id"]),
            name=str(data["name"]),
            products=[Product.fromJson(p) for p in data.get("products", [])],
            clients=[Client.fromJson(c) for c in data.get("clients", [])]
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "products": [p.toJson() for p in self.products],
            "clients": [c.toJson() for c in self.clients]
        }