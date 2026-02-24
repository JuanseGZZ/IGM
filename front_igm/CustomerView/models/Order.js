import { Line } from "./Line.js";

export class Order{
    static VALID_STATUS = ["pending","paid","canceled","expired"];

    constructor(id,client_email,status,lines,currency){
        this.id = id; // str
        this.client_email = client_email; // str
        this.status = Order.VALID_STATUS[status]; // int
        this.lines = lines ?? []; // list<Lines> 
        this.currency = currency; // str
    }

    getTotal(){
        if (!this.lines || this.lines.length === 0) return 0;

        return this.lines.reduce((acc, line) => {
            return acc + (line.unit_price * line.quantity);
        }, 0);
    }

    addLine(line){
        if (!line) return;

        if (!this.lines) this.lines = [];

        const productId = line.product?.id;
        if (productId === undefined || productId === null) return;

        const existingLine = this.lines.find(l => l.product?.id === productId);

        if (existingLine){
            existingLine.quantity += line.quantity;
            return;
        }

        this.lines.push(line);
    }

    removeLineByProductId(productId){
        if (!this.lines || this.lines.length === 0) return;

        this.lines = this.lines.filter(line => line.product?.id !== productId);
    }

    removeAllLines(){
        this.lines = [];
    }

    save(){};
    static getAllOrders(){};
    static getOrderByEmail(){};

    // json handlers
    static fromJson(json){
            if (!json) return null;

            const lines = (json.lines ?? []).map(l => Line.fromJson(l));

            // status se guarda como string, pero tu constructor espera index
            const statusIndex = Order.VALID_STATUS.indexOf(json.status);

            return new Order(
                json.id,
                json.client_email,
                statusIndex >= 0 ? statusIndex : 0,
                lines,
                json.currency
            );
    };
    toJson(){
        return {
            "id": this.id,
            "client_email": this.client_email,
            "status": this.status,
            "lines": (this.lines ?? []).map(line => line.toJson()),
            "currency": this.currency
        };
    };

}