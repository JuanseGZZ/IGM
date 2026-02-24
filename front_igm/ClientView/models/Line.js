import { Product } from "./Product.js";

export class Line{
    constructor(product,unit_price,quantity){
        this.product = product; // Product()
        this.title = this.product.title; // str
        this.unit_price = unit_price; // int
        this.quantity = quantity; // int
    }

    static fromJson(lineJson){
        if (!lineJson) return null;

        const product = Product.fromJson(lineJson.product);

        return new Line(
            product,
            lineJson.unit_price,
            lineJson.quantity
        );
    };
    toJson(){
        return {
            "product":this.product.toJson(),
            "title":this.title,
            "unit_price":this.unit_price,
            "quantity":this.quantity
        }
    };
}