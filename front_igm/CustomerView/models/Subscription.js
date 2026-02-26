import { Plan } from "./Plan.js";
import { Shop } from "./Shop.js";

export class Subscription {
    static STATE = ["waiting", "paid", "expired"];

    constructor(id, shop, plan, cantProducts, state, until_date) {
        this.id = id; // string
        this.shop = shop; // Shop
        this.plan = plan; // Plan
        this.cantProducts = cantProducts; // number
        this.state = Subscription.STATE[state]; // number index
        this.until_date = until_date; // string | Date
    }

    static fromJson(json) {
        if (!json) return null;

        return new Subscription(
            String(json.id),
            Shop.fromJson(json.shop),
            Plan.fromJson(json.plan),
            Number(json.cantProducts),
            Number(json.state),
            json.until_date
        );
    }

    toJson() {
        return {
            id: this.id,
            shop: this.shop ? this.shop.toJson() : null,
            plan: this.plan ? this.plan.toJson() : null,
            cantProducts: this.cantProducts,
            state: Subscription.STATE.indexOf(this.state),
            until_date: this.until_date
        };
    }
}