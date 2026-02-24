
class Subscription{
    static STATE = ["paid","waiting","expired"]

    constructor(id,shop,plan,state,expired){
        this.id = id;
        this.shop = shop;
        this.plan = plan;
        this.state = state;
        this.expired = expired
    }

    static fromJson(json){}
    toJson(){}
}