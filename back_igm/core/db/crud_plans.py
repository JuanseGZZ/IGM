from .crud_base import CrudBase


class CrudPlans(CrudBase):
    SCHEMA = "public"
    TABLE = "plans"