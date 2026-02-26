import { Subscription } from "./Subscription.js";

export class Customer {
    constructor(id, name, surname, email, mpAssociated, subscription) {
        this.id = id; // number
        this.name = name; // string
        this.surname = surname; // string
        this.email = email; // string
        this.mpAssociated = mpAssociated; // number
        this.subscription = subscription; // Subscription
    }

    static fromJson(json) {
        if (!json) return null;

        return new Customer(
            Number(json.id),
            String(json.name),
            String(json.surname),
            String(json.email),
            Number(json.mpAssociated),
            json.subscription ? Subscription.fromJson(json.subscription) : null
        );
    }

    toJson() {
        return {
            id: this.id,
            name: this.name,
            surname: this.surname,
            email: this.email,
            mpAssociated: this.mpAssociated,
            subscription: this.subscription ? this.subscription.toJson() : null
        };
    }
}