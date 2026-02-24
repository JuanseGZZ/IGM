// inheritanceable class that perform the acttion to now witch payment is allready done

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms*1000));
}

function print(str){
    console.log(str);
}

class PaymentConfirmation{
    static timeSleep = [0.5,1,2,4,6,10]; // times sleeps in seconds -> 0.5, 1, 2, 4, 6,10.

    constructor(url,id){
        this.url = url; // url that the api payment state use to norify in whitch state the payment is.
    }

    async waitingFor(intTimeout,strPaymentId){ // that function is used to send questions to the back, while the time of we pase in timeout, until it say us the payment is confirmated.
        let i = 0;
        let confirmation = false;

        let startMs = 0;
        let nowMs = 0;
        let elapsedMs = 0;

        startMs = Date.now();

        while (!confirmation && elapsedMs < intTimeout*1000) {
            nowMs = Date.now();
            elapsedMs = nowMs - startMs;

            print("Times: "+PaymentConfirmation.timeSleep[i])
            confirmation = await this._checkPayment(strPaymentId);
            if (confirmation) return true;

            await sleep(PaymentConfirmation.timeSleep[i]);
            i++;
        }
        print("donete");

        return false; // timeout
    }

    async _checkPayment(id) {
        try {
            const res = await fetch(`${this.url}/payment/${id}`);
            if (!res.ok) return false;

            const data = await res.json();

            // assuming tha answer is kinnda { status: "confirmed" }
            return data.status === "confirmed";

        } catch {
            return false; // network trubles
        }
    }
}

// use:

const payment = new PaymentConfirmation("st.com");
let status1 = await payment.waitingFor(2,"15")? "done":"fail";
payment.url = "other.com";
let status2 = await payment.waitingFor(3,"16")? "done":"fail";

print(status1);
print(status2);