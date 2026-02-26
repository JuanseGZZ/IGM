import { Product } from "./Product";
import { Client } from "./Client";

export class Shop {
    constructor(id, name, products = [], clients = []) {
        this.id = id;            // string
        this.name = name;        // string
        this.products = products; // Array<Product>
        this.clients = clients;   // Array<Client>
    }

    static fromJson(json) {
        if (!json) return null;

        return new Shop(
            String(json.id),
            String(json.name),
            (json.products || []).map(p => Product.fromJson(p)),
            (json.clients || []).map(c => Client.fromJson(c))
        );
    }

    toJson() {
        return {
            id: this.id,
            name: this.name,
            products: this.products ? this.products.map(p => p.toJson()) : [],
            clients: this.clients ? this.clients.map(c => c.toJson()) : []
        };
    }
}