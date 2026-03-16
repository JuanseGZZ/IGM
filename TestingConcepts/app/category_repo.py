from models import Category
from crud_base import CrudBase


class CategoryRepo(CrudBase[Category]):
    TABLE = "category"
    MODEL_CLASS = Category

    @classmethod
    def _obj_to_row(cls, obj: Category):
        return {
            "id": obj.id,
            "name": obj.name,
        }

    @classmethod
    def _row_to_obj(cls, row):
        if row is None:
            return None

        return Category(
            id=row["id"],
            name=row["name"],
            attributes=[],
        )