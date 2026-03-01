import { Subscription } from "./Subscription.js";
import { JWT } from "./jwts.js";

export class Customer {
    constructor(id, name, surname, email, mpAssociated = 0, subscription = [], jwt = null) {
        this.id = id; // number
        this.name = name; // string
        this.surname = surname; // string
        this.email = email; // string
        this.mpAssociated = mpAssociated; // number
        this.subscription = subscription; // List<Subscription>
        this.jwt = jwt; // JWT (at/rt)
    }

    static fromJson(json) {
        if (!json) return null;

        const subs = (json.subscription ?? []).map(s => Subscription.fromJson(s));
        const jwt = json.jwt ? JWT.fromJson(json.jwt) : null;

        return new Customer(
            Number(json.id),
            String(json.name),
            String(json.surname),
            String(json.email),
            Number(json.mp_associated),
            subs,
            jwt
        );
    }

    toJson() {
        return {
            "id": this.id,
            "name": this.name,
            "surname": this.surname,
            "email": this.email,
            "mp_associated": this.mpAssociated,
            "subscription": (this.subscription ?? []).map(s => s.toJson()),
            "jwt": this.jwt ? this.jwt.toJson() : null
        };
    }
}