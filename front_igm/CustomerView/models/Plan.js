
// plan free 1 to 9
// plan basic 10 to 100
// plan seller 101 to 1000
// plan shop 1001 to 100000
// plan unic * this is for own sistem for them *


export class Plan {
    constructor(id, name, upTo, downTo, costPerProducts) {
        this.id = id;                     // string
        this.name = name;                 // string
        this.costPerProducts = costPerProducts; // number
        this.upTo = upTo;                 // number
        this.downTo = downTo;             // number
    }

    static fromJson(json) {
        if (!json) return null;

        return new Plan(
            String(json.id),
            String(json.name),
            Number(json.upTo),
            Number(json.downTo),
            Number(json.costPerProducts)
        );
    }

    toJson() {
        return {
            "id": this.id,
            "name": this.name,
            "upTo": this.upTo,
            "downTo": this.downTo,
            "costPerProducts": this.costPerProducts
        };
    }
}