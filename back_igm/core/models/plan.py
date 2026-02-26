from typing import Dict, Any


class Plan:
    def __init__(self, id: str, name: str, upTo: int, downTo: int, costPerProducts: int):
        self.id = id
        self.name = name
        self.costPerProducts = costPerProducts
        self.upTo = upTo
        self.downTo = downTo

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Plan":
        return Plan(
            id=str(data["id"]),
            name=str(data["name"]),
            upTo=int(data["upTo"]),
            downTo=int(data["downTo"]),
            costPerProducts=int(data["costPerProducts"])
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "upTo": self.upTo,
            "downTo": self.downTo,
            "costPerProducts": self.costPerProducts
        }