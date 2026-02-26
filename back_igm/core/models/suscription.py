from plan import Plan
from shop import Shop
import datetime

import json

class Suscription:
    STATE  = { "waiting","paid", "expired" }

    def __init__(self,id:int,shop:Shop,plan:Plan,state:int,until_date:datetime):
        self.id = id
        self.shop = shop
        self.plan = plan
        self.state = state


    def fromJson(json:json) -> Suscription:
        pass
    def toJson(self) -> json:
        pass