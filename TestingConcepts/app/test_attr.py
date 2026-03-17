from attributes_repo import AttributeRepo
from models import Attribute

def save():
    atr = Attribute(None,"pais","pais","enum",True)
    atr.add_enum_value("Argentina")
    atr.add_enum_value("Brasil")

    print(atr.enum_values)

    saved = AttributeRepo().save(atr)
    print(saved)


#deleted = AttributeRepo().delete(1)
#print(deleted)