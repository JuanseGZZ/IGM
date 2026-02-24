from typing import List
from order import Order

class Client:
    def __init__(self, name: str, email: str, orders: List[Order]):
        self.name = name
        self.email = email
        self.orders = orders

    def save():
        pass

    @staticmethod
    def fromJson(json):
        pass

    def toJson(self):
        pass