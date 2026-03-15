from repository import Repositories
from models import Attribute


with Repositories() as repos:
    
    # guardar algo nuevo
    repos.attribute.save(Attribute(1,"peso_g","Peso (g)","number",is_static=True))
    print(repos.attribute.get_all())
