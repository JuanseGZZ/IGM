import {Subscription} from "./Subscription"

class Customer{
    constructor(id,name,surname,email,mpAssociated,subscription){
        this.id = id; // int
        this.name = name; // str
        this.surname = surname; // str
        this.email = email;  // str
        this.mpAssociated = mpAssociated; // int 
        this.subscription = subscription; // Suscription()
        
    }

    static fromJson(json){}
    toJson(){}
}