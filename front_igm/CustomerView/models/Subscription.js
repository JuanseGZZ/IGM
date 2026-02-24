
class Subscription{
    static STATE = ["waiting","paid","expired"]

    constructor(id,shop,plan,state,until_date){
        this.id = id;
        this.shop = shop;
        this.plan = plan;
        this.state = state;
        this.until_date = until_date
    }

    static fromJson(json){}
    toJson(){}
}