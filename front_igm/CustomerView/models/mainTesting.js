import { Product } from "./Product.js";
import { Line } from "./Line.js";
import { Order } from "./Order.js";
import { Client } from "./Client.js";

let client = new Client("jhon","jhon@gmail.com",[]);

let product = new Product("1","droga",15,"para drogarese","www.com.com"); // los products deberian ser flyweigts (hay que hacer productFactory)
let product2 = new Product("2","alcohol",10,"para tomar","www.come.com");

let line = new Line(product,3);
let line2 = new Line(product2,5);

let order = new Order(1,client.email,0,[],"ARS");
order.addLine(line);
order.addLine(line2);

console.log(JSON.stringify(order.toJson(), null, 2));
