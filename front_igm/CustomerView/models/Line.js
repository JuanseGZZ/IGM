import { Product } from "./Product.js";

export class Line{
    constructor(product,quantity){
        this.product = product; // Product()
        this.quantity = quantity; // int
    }

    static fromJson(lineJson){
        if (!lineJson) return null;

        const product = Product.fromJson(lineJson.product);

        return new Line(
            product,
            lineJson.quantity
        );
    };
    toJson(){
        return {
            "product":this.product.toJson(),
            "quantity":this.quantity
        }
    };
}