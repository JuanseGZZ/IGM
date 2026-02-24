from plan import Plan
from shop import Shop
import datetime

import json

class Suscription:
    STATE  = { "waiting","paid", "expired" }

    def __init__(self,id:int,shop:Shop,state:int,until_date:datetime):
        pass

    def fromJson(json:json) -> Suscription:
        pass
    def toJson(self) -> json:
        pass