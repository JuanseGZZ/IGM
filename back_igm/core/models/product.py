import json
from typing import Dict,Any

class Product:
    def __init__(self,id:str,title:str,price:float,description:str,image_url:str):
        self.id = id
        self.title = title
        self.price = price
        self.description = description
        self.image_url = image_url

    @staticmethod
    def fromJson(json: Dict[str:Any]) -> "Product":
        return Product(
            id=str(json["id"]),
            title=str(json["title"]),
            price=float(json["price"]),
            description=str(json["description"]),
            image_url=str(json["image_url"])
        )

    def toJson(self) -> json:
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "description": self.description,
            "image_url": self.image_url
        }