from ..db import CrudCustomers
from ..models import Customer

CrudCustomers.refresh_meta()

c = CrudCustomers.create({
    "id": 1,
    "name": "Juan",
    "surname": "Perez",
    "email": "juan.perez@test.com",
    "mp_associated": 123
})
costumer = Customer.fromJson(c)


print(costumer.email)
input("")
CrudCustomers.delete(1)