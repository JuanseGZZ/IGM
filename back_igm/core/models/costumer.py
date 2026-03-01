from typing import Dict, Any, List
from .subscription import Subscription
from .jwts import JWT


class Customer:
    def __init__(self, id: int, name: str, surname: str,
                 email: str, mpAssociated: int, subscription: List[Subscription], jwt: JWT = None):
        self.id = id
        self.name = name
        self.surname = surname
        self.email = email
        self.mpAssociated = mpAssociated
        self.subscription = subscription or []
        self.jwt = jwt if jwt else JWT(email, "client")

    @staticmethod
    def fromJson(data: Dict[str, Any]) -> "Customer":
        
        return Customer(
            id=int(data["id"]),
            name=str(data["name"]),
            surname=str(data["surname"]),
            email=str(data["email"]),
            mpAssociated=int(data["mp_associated"]),
            subscription=[Subscription.fromJson(s) for s in data.get("subscription", [])],
            jwt=JWT.fromJson(data["jwt"]) if data.get("jwt") else None
        )

    def toJson(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "mp_associated": self.mpAssociated,
            "subscription": [s.toJson() for s in (self.subscription or [])],
            "jwt": self.jwt.toJson() if self.jwt else None,
        }