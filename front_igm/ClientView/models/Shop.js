import { Product } from "./Product";
import { Client } from "./Client";

class Shop{
    constructor(id,name,products,clients){
        this.id = id;
        this.name = name;
        this.products = products;
        this.clients = clients;
    }

    static fromJson(json){}
    toJson(){}
}