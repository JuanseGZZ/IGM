import { Order } from "./Order.js";
import { JWT } from "./JWT.js";

export class Client{
    constructor(id,name,email,orders = [], jwt = null){
        this.id = id; // int pk
        this.name = name; // str
        this.email = email; // str 
        this.orders = orders; // List<Order>
        this.jwt = jwt; // JWT (at/rt)
    }

    save() {}

    static fromJson(json) {
        if (!json) return null;

        const orders = (json.orders ?? []).map(o => Order.fromJson(o));
        const jwt = json.jwt ? JWT.fromJson(json.jwt) : null;

        return new Client(json.id,json.name, json.email, orders, jwt);
    }
    toJson() {
        return {
            "id":this.id,
            "name": this.name,
            "email": this.email,
            "orders": (this.orders ?? []).map(o => o.toJson()),
            "jwt": this.jwt ? this.jwt.toJson() : null
        };
    }
}