from ..db import CrudCustomers
from ..models import Customer

class CostumerRepository:

    @staticmethod
    def create_costumer(data) -> Customer:
        c = CrudCustomers.create({
            "id": 1,
            "name": "Juan",
            "surname": "Perez",
            "email": "juan.perez@test.com",
            "mp_associated": 123
        })
        costumer = Customer.fromJson(c)