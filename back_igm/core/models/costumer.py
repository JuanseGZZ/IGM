from suscription import Suscription
import json


class Costumer:

    def __init__(self,id:int,name:str,surname:str,email:str,mpAssociated:int,suscription:Suscription):
        self.id = id
        self.name = name
        self.surname = surname
        self.email = email
        self.mpAssociated = mpAssociated
        self.suscription = suscription
    
    def fromJson(json:json) -> Costumer:
        pass
    def toJson(self) -> json:
        pass