import os
import json
import time
import requests

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse

from credentials import CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, BASE_URL
from mercadopagoFW import create_payment_link, create_payment_with_commission
from ModelsYDB import init_db
from ModelsYDB import Organizers,Order

init_db()

app = FastAPI()

# ------------------------------ heritable apis

def log_request(request: Request, label: str):
    print("\n==============================")
    print(f"PAYMENT RETURN -> {label}")
    print("URL:", request.url)
    print("METHOD:", request.method)
    print("QUERY PARAMS:")
    print(dict(request.query_params))
    print("==============================\n")


@app.get("/success")
async def payment_success(request: Request):
    log_request(request, "SUCCESS")

    return {
        "status": "ok",
        "type": "success",
        "message": "payment approved, revisar logs"
    }


@app.get("/pending")
async def payment_pending(request: Request):
    log_request(request, "PENDING")

    return {
        "status": "ok",
        "type": "pending",
        "message": "payment pending, revisar logs"
    }


@app.get("/failure")
async def payment_failure(request: Request):
    log_request(request, "FAILURE")

    return {
        "status": "ok",
        "type": "failure",
        "message": "payment failed, revisar logs"
    }

#heritable api
@app.get("/attach/{associated}")
def attach(associated:str):
    # Redirige al OAuth de MercadoPago con "state" como id para mail o user, si es mail deberia ir cifrado. 
    url = (
        "https://auth.mercadopago.com/authorization"
        "?client_id=3017587446112951"
        "&response_type=code"
        "&platform_id=mp"
        "&redirect_uri=https://juanguzzardi.com/oauth/callback"
        f"&state={associated}"
    )
    return RedirectResponse(url=url, status_code=302)

#heritable api
@app.get("/oauth/callback")
def oauth_callback(request: Request):
    code = request.query_params.get("code")

    associated = request.query_params.get("state") 
    if associated == "" or associated == None:
        return PlainTextResponse(f"No vino un associated en el packet.")

    redirect_uri = "https://juanguzzardi.com/oauth/callback"

    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    r = requests.post("https://api.mercadopago.com/oauth/token", json=payload)
    if r.status_code != 200:
        return PlainTextResponse(f"Error al obtener token: {r.text}", status_code=400)

    data = r.json()

    user_id = str(data.get("user_id"))
    access_token=data.get("access_token")
    refresh_token=data.get("refresh_token")
    expires_in=data.get("expires_in")
    scope=data.get("scope")
    token_type=data.get("token_type")

    print("data: ", json.dumps(data, indent=2))

    organizer = Organizers(associated=associated,user_id=user_id,access_token=access_token,refresh_token=refresh_token,expires_in=expires_in,scope=scope,token_type=token_type)

    organizer.save()

    return PlainTextResponse(f"Organizador autorizado correctamente: {associated} | {user_id}")

#webhook question to mp abot a payment recived
def mp_get_payment(payment_id: str):
    r = requests.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        timeout=15,
    )
    return r.status_code, r.json()

@app.post("/webhooks/")
async def webhooks(request: Request):
    # 1) log body si existe
    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}

    print("Webhook recibido:", json.dumps(body, indent=2))
    print("Query params:", dict(request.query_params))

    # 2) extraer payment_id de donde venga
    qp = request.query_params

    payment_id = None
    if isinstance(body, dict):
        payment_id = (body.get("data") or {}).get("id")

    if not payment_id:
        payment_id = qp.get("data.id") or qp.get("id") or qp.get("resource")

    event_type = body.get("type") or qp.get("type") or qp.get("topic")

    if event_type != "payment" or not payment_id:
        print("Ignorado. type/topic:", event_type, "payment_id:", payment_id)
        return PlainTextResponse("IGNORED", status_code=200)

    # 3) pedir el pago real a MP (aca aparece external_reference)
    code, payment = mp_get_payment(str(payment_id))

    #print("MP payment status_code:", code)
    #print("MP payment:", json.dumps(payment, indent=2))

    if code != 200:
        return PlainTextResponse("MP_ERROR", status_code=200)

    external_reference = payment.get("external_reference")
    status = payment.get("status")           # approved, pending, rejected, etc
    status_detail = payment.get("status_detail")

    print("external_reference:", external_reference)
    print("status:", status, "detail:", status_detail)

    # 4) actualizar DB por external_reference (o por mp_id si preferis)
    if external_reference:
        order = Order.by_external_reference(external_reference)
        if order:
            order.state = str(status)
            order.mp_id = str(payment_id)
            order.save()
            print("Order actualizada:", external_reference, "->", status)
        else:
            print("No encontre order con external_reference:", external_reference)

    return PlainTextResponse("OK", status_code=200)

@app.get("/order/{id_ext_ref}") # tiene que ser el id interno, y, hay que hacer que cuando el webhook detecte un id interno lo marque como done, 
async def orderById(id_ext_ref:str):
    order = Order.by_external_reference(id_ext_ref)
    return { "state":f"{order.state}" }

# ------------------------------ framework functions <- falta hacer que creen en db el registro de pago.

# framework function
def create_commissioned_payment(associated:str,email:str,title:str, price:int, app_fee:int,external_reference:str):
    organizer = Organizers.find_by_associated(associated=associated)
    # si no hay un asociado con ese str
    if organizer == None:
        return RedirectResponse(url=f"/asociar/{associated}")

    expires_in = organizer.expires_in
    created_at = organizer.created_at
    now = int(time.time())

    # si expiro el AT
    if expires_in is not None and created_at is not None and now - int(created_at) >= int(expires_in):
        payload = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": organizer.refresh_token,
        }
        r = requests.post("https://api.mercadopago.com/oauth/token", json=payload)
        if r.status_code != 200:
            return PlainTextResponse(f"Error al refrescar token: {r.text}", status_code=400)

        data = r.json()

        organizer.access_token = data["access_token"]
        organizer.refresh_token = data["refresh_token"]
        organizer.expires_in = data["expires_in"]

        organizer.save()


    payment = create_payment_with_commission(
        title=title,
        price=price,
        payer_email=email,
        organizer_access_token=organizer.access_token,
        app_fee=app_fee, # it is not persentage, you must to calculate before.
        external_reference=external_reference
    )

    order = Order(
        user_email=email,
        external_reference=payment["external_reference"],
        mp_id=payment["id"],
        associated=associated
    )
    order.save()

    print(f"Usando {organizer.access_token} se genero un pago")
    return RedirectResponse(url=payment["init_point"], status_code=302)

#facade framework function
def create_payment(title:str, price:int, payer_email:str, external_reference:str):
    preference = create_payment_link(title, price, payer_email, external_reference=external_reference)
    response = requests.post(
        f"{BASE_URL}/checkout/preferences?access_token={ACCESS_TOKEN}",
        json=preference,
    )
    data = response.json()
    order = Order(
        user_email=payer_email,
        external_reference=data["external_reference"],
        mp_id=data["id"],
        associated="owner"
    )
    order.save()
    print(f"order: {order.associated}-{order.external_reference}-{order.mp_id}-{order.user_email}")

    return response.json()

    

# ------------------------------ testing

#testing api
@app.get("/crear_pago/{associated}")
def crear_pago_comisionado(associated: str, request: Request):
    payer_email = request.query_params.get("email", "test@test.com")
    payment = create_commissioned_payment(associated=associated,email=payer_email,title="Entrada evento",price=10.0,app_fee=2.0)
    return RedirectResponse(url=payment["init_point"], status_code=302)

# external reference es para saber que pedido fue cual. numero de pedido interno seria.
#testing api
@app.get("/crear_pago_normal")
def crear_pago_normal(request: Request):
    payer_email = request.query_params.get("email", "test@test.com")
    data = create_payment("Producto común", 2.0, payer_email, external_reference="pedido_123")
    return RedirectResponse(url=data["init_point"], status_code=302)

#testing api
@app.get("/", response_class=HTMLResponse)
def index():
    # Carga index.html que esta al mismo nivel que este main.py
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if not os.path.exists(html_path):
        return HTMLResponse(
            "<h1>Falta index.html al lado de main.py</h1>",
            status_code=500,
        )
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
    
# idk
@app.post("/notificaciones/")
async def notificaciones(request: Request):
    payload = await request.json()
    print("Notificación recibida:", json.dumps(payload, indent=2))
    return PlainTextResponse("OK", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)