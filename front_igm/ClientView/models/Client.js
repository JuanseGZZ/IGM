import { Order } from "./Order.js";

export class Client{
    constructor(name,email,orders){
        this.name = name; // str
        this.email = email; // str [Id]
        this.orders = orders; // List<Order>
    }

    save(){};

    // json handlers
    static fromJson(json){
        if (!json) return null;
        const orders = (json.orders ?? []).map(o => Order.fromJson(o));
        return new Client(json.name, json.email, orders);
    };
    toJson(){
        return {
            "name": this.name,
            "email": this.email,
            "orders": (this.orders ?? []).map(order => order.toJson())
        };
    };
}