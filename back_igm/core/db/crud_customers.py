from crud_base import CrudBase


class CrudCustomers(CrudBase):
    SCHEMA = "public"
    TABLE = "customers"