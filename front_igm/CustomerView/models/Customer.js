
class Customer{
    constructor(id,name,surname,email,mpAsociated,subscription){
        this.id = id;
        this.name = name;
        this.surname = surname;
        this.email = email;
        this.mpAsociated = mpAsociated;
        this.subscription = subscription;
        
    }

    static fromJson(json){}
    toJson(){}
}