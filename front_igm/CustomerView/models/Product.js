

export class Product{
    constructor(id,title,price,description,image_url){
        this.id = id; // str
        this.title = title; // str
        this.price = price; // int
        this.description = description; // str
        this.image_url = image_url; // str
    }

    // to save state in db
    save(){}
    // to look for item by id
    static bringByTitle(title) {
        let product = Product();
        return product;
    }
    // to look for all items
    static bringAll(){
        let products = []; // List<Product>
        return products;
    }
    
    // json handlers
    static fromJson(json){
        if (!json) return null;

        return new Product(
            json.id,
            json.title,
            json.price,
            json.description,
            json.image_url
        );
    };
    toJson(){
        return {
            "id": this.id,
            "title": this.title,
            "price": this.price,
            "description": this.description,
            "image_url": this.image_url
        };
    };
    
}