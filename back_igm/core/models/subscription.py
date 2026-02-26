from plan import Plan
from shop import Shop
from typing import Dict, Any

class Subscription:
    STATE = ["waiting", "paid", "expired"]

    def __init__(self, id: str, shop: Shop, plan: Plan,
                 cantProducts: int, state: int, until_date):
        self.id = id
        self.shop = shop
        self.plan = plan
        self.cantProducts = cantProducts
        self.state = Subscription.STATE[state]
        self.until_date = until_date

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Subscription":
        return Subscription(
            id=str(data["id"]),
            shop=Shop.fromJson(data["shop"]),
            plan=Plan.fromJson(data["plan"]),
            cantProducts=int(data["cantProducts"]),
            state=int(data["state"]),
            until_date=data["until_date"]
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "shop": self.shop.toJson() if self.shop else None,
            "plan": self.plan.toJson() if self.plan else None,
            "cantProducts": self.cantProducts,
            "state": Subscription.STATE.index(self.state),
            "until_date": self.until_date
        }