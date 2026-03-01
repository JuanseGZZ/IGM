from ..db import CrudCustomers

CrudCustomers.refresh_meta()

c = CrudCustomers.create({
    "id": 1,
    "name": "Juan",
    "surname": "Perez",
    "email": "juan.perez@test.com",
    "mp_associated": 123
})


print(c)
CrudCustomers.delete(1)