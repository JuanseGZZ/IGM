
import requests
import json

from credentials import CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN, BASE_URL

from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
until = now + timedelta(minutes=2)

def create_payment_link(title, price, payer_email, external_reference):
    return {
        "items": [{"title": title, "quantity": 1, "currency_id": "ARS", "unit_price": price}], # <- hacer un sistema de multi items que se carguen
        "payer": {"email": payer_email},
        "external_reference": external_reference,
        "back_urls": {
            "success": "https://juanguzzardi.com/success",
            "pending": "https://juanguzzardi.com/pending",
            "failure": "https://juanguzzardi.com/failure"
        },
        "auto_return": "approved",
        "notification_url": "https://juanguzzardi.com/webhooks/",
        "payment_methods": {
            "excluded_payment_types": [
                {"id": "ticket"},        # efectivo
                {"id": "credit_card"},   # tarjetas de crédito
                {"id": "atm"}            # cajero
            ]
        },

        "expires": True,
        "expiration_date_from": now.isoformat(),
        "expiration_date_to": until.isoformat()
    }

# se usa el token ese porque es el token del cliente enbebido con la app.
def create_payment_with_commission(title, price, payer_email, organizer_access_token, app_fee,external_reference): 
    # Define tus credenciales y el URL de la API de Mercado Pago
    url = "https://api.mercadopago.com/checkout/preferences" 
    
    headers = {
        "Authorization": f"Bearer {organizer_access_token}",
        "Content-Type": "application/json"
    } 
    
    # Configura el cuerpo de la solicitud con los datos de split del pago
    preference_data = {
        "items": [ # <- hacer un sistema de multi items que se carguen
            {
                "title": title, # "Entrada evento"
                "quantity": 1,
                "currency_id": "ARS",  # Reemplaza con el símbolo de tu moneda local
                "unit_price": price
            }
        ],
        "payer": {
        "email": payer_email
        },
        "external_reference": external_reference,
        "back_urls": {
            "success": "https://juanguzzardi.com/",
            "failure": "https://juanguzzardi.com/",
            "pending": "https://juanguzzardi.com/"
        },
        "auto_return": "approved",
        "marketplace_fee": app_fee,  # Esta línea indica tu comisión o fee, es un numero calculado no un porsentaje y tiene que ser menor al monto y la comision de mp.
        "notification_url": "https://juanguzzardi.com/webhooks/",
        "payment_methods": {
            "excluded_payment_types": [
                {"id": "ticket"},        # efectivo
                {"id": "credit_card"},   # tarjetas de crédito
                {"id": "atm"}            # cajero
            ]
        },

        "expires": True,
        "expiration_date_from": now.isoformat(),
        "expiration_date_to": until.isoformat()
    } 
    
    # Envía la solicitud POST
    response = requests.post(url, headers=headers, data=json.dumps(preference_data)) 
    
    # Comprueba la respuesta
    preference = response.json() 
    return preference


def ask_for_payment_by_reference(external_reference):
    response = requests.get(
        "https://api.mercadopago.com/v1/payments/search",
        params={"external_reference": external_reference},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    return response.json()