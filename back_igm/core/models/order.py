from typing import List, Dict, Any
from line import Line


class Order:
    VALID_STATUS = ["pending", "paid", "canceled", "expired"]
    CURRENCYS = {"ARS", "USD"}

    def __init__(self, id: str, client_email: str, status: int, lines: List[Line], currency: str):
        self.id = id
        self.client_email = client_email
        self.status = Order.VALID_STATUS[status]
        self.lines = lines
        self.currency = currency

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Order":
        return Order(
            id=str(data["id"]),
            client_email=str(data["client_email"]),
            status=int(data["status"]),
            lines=[Line.fromJson(line) for line in data["lines"]],
            currency=str(data["currency"])
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_email": self.client_email,
            "status": self.status,
            "lines": [line.toJson() for line in self.lines],
            "currency": self.currency
        }
    
    def getTotal(self) -> float:
        if not self.lines:
            return 0.0

        return sum(line.product.price * line.quantity for line in self.lines)

    def addLine(self, line: Line) -> None:
        if not line:
            return

        if not self.lines:
            self.lines = []

        product_id = getattr(line.product, "id", None)
        if product_id is None:
            return

        for existing_line in self.lines:
            if getattr(existing_line.product, "id", None) == product_id:
                existing_line.quantity += line.quantity
                return

        self.lines.append(line)

    def removeLineByProductId(self, product_id: str) -> None:
        if not self.lines:
            return

        self.lines = [
            line for line in self.lines
            if getattr(line.product, "id", None) != product_id
        ]

    def removeAllLines(self) -> None:
        self.lines = []