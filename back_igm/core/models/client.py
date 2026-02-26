from typing import List, Dict, Any
from order import Order
from jwts import JWT

class Client:
    def __init__(self, name: str, email: str, orders: List[Order]):
        self.name = name
        self.email = email
        self.orders = orders
        self.jwt = JWT(email,"client")

    def save(self):
        pass

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Client":
        return Client(
            name=str(data["name"]),
            email=str(data["email"]),
            orders=[Order.fromJson(order) for order in data.get("orders", [])],
            jwt=JWT.fromJson(data["jwt"]) if data.get("jwt") else None,
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "orders": [order.toJson() for order in self.orders],
            "jwt": self.jwt.toJson() if self.jwt else None,
        }
    

def test():

    c = Client(name="jhon",email="jhon@mail.com",orders=[])

    print(c.email)
    print(c.jwt.access_token)

    try:
        print(JWT.verify("asdasd"))
    except:
        print("somthing was wrong")


#test()