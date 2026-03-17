from psycopg import sql
from psycopg.rows import dict_row

from config import conn
from crud_base import CrudBase
from models import Attribute


class AttributeRepo(CrudBase[Attribute]):
    TABLE = "atribute"
    MODEL_CLASS = Attribute

    @classmethod
    def _obj_to_row(cls, obj: Attribute):
        return {
            "id": obj.id,
            "key": obj.key,
            "name": obj.name,
            "data_type": obj.data_type,
            "is_static": obj.is_static,
        }

    @classmethod
    def _save_enum_values(cls, attribute: Attribute):
        if attribute.id is None:
            raise ValueError("No se pueden guardar enum_values sin id")

        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM enum_values WHERE atribute_id = %s",
                (attribute.id,),
            )

            if attribute.data_type == "enum":
                for value in attribute.enum_values:
                    cur.execute(
                        """
                        INSERT INTO enum_values (atribute_id, value)
                        VALUES (%s, %s)
                        """,
                        (attribute.id, value),
                    )

    @classmethod
    def _load_enum_values(cls, attribute_id: int):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT value
                FROM enum_values
                WHERE atribute_id = %s
                ORDER BY id
                """,
                (attribute_id,),
            )
            return [row[0] for row in cur.fetchall()]

    @classmethod
    def _row_to_obj(cls, row):
        if row is None:
            return None

        attribute = Attribute(
            id=row["id"],
            key=row["key"],
            name=row["name"],
            data_type=row["data_type"],
            is_static=row["is_static"],
        )

        if attribute.data_type == "enum":
            attribute.enum_values = cls._load_enum_values(attribute.id)

        return attribute

    @classmethod
    def save(cls, obj: Attribute) -> Attribute:
        saved = super().save(obj)
        cls._save_enum_values(saved)
        conn.commit()
        return cls.read(saved.id)

    @classmethod
    def read(cls, obj_id: int):
        return super().read(obj_id)

    @classmethod
    def delete(cls, obj_id: int) -> bool:
        return super().delete(obj_id)