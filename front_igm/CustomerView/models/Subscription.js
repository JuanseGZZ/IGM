
export class Subscription{
    static STATE = ["waiting","paid","expired"]

    constructor(id,shop,plan,state,until_date){
        this.id = id; // str
        this.shop = shop; // Array<Shop>
        this.plan = plan; // Array<Plan>
        this.state = Subscription.STATE[state]; // int
        this.until_date = until_date // idk
    }

    static fromJson(json){}
    toJson(){}
}