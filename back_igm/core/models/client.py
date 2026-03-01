from typing import List, Dict, Any
from .order import Order
from .jwts import JWT

class Client:
    def __init__(self,id: int, name: str, email: str, orders: List[Order],jwt: JWT = None):
        self.id = id
        self.name = name
        self.email = email
        self.orders = orders
        self.jwt = jwt if jwt else JWT(email, "client")

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Client":
        return Client(
            id=int(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            orders=[Order.fromJson(order) for order in data.get("orders", [])],
            jwt=JWT.fromJson(data["jwt"]) if data.get("jwt") else None,
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id":self.id,
            "name": self.name,
            "email": self.email,
            "orders": [order.toJson() for order in self.orders],
            "jwt": self.jwt.toJson() if self.jwt else None,
        }
    

def test():

    c = Client(id = 1,name="jhon",email="jhon@mail.com",orders=[])

    print(c.email)
    print(c.jwt.access_token)

    try:
        print(JWT.verify("asdasd"))
    except:
        print("somthing was wrong")


#test()