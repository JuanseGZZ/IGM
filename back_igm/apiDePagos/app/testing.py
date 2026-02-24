from main import create_commissioned_payment, create_payment
from credentials import BASE_URL,ACCESS_TOKEN
import requests
import json

#result = create_commissioned_payment("Lucia","pedro@pedro.pedro","test",2,0,"BR-18") # working
#print (result) 
#"<starlette.responses.RedirectResponse object at 0x00000161A63696A0>"
#Usando APP_USR-3017587446112951-021722-f0b1c8807f3f3d6329569fd4b66ec1ac-1179602589 se genero un pago
#{'additional_info': '', 'auto_return': 'approved', 'back_urls': {'failure': 'https://juanguzzardi.com/', 'pending': 'https://juanguzzardi.com/', 'success': 'https://juanguzzardi.com/'}, #'binary_mode': False, 'client_id': '3017587446112951', 'collector_id': 1179602589, 'coupon_code': None, 'coupon_labels': None, 'date_created': '2026-02-20T19:01:18.765-04:00', #'date_of_expiration': None, 'expiration_date_from': None, 'expiration_date_to': None, 'expires': False, 'external_reference': 'BR-15', 'id': #'1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f', 'init_point': 'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=1179602589-a909a37e-21ee-4ebe-9e7e-58ba1a183254', #'internal_metadata': None, 'items': [{'id': '', 'category_id': '', 'currency_id': 'ARS', 'description': '', 'title': 'test', 'quantity': 1, 'unit_price': 10}], 'marketplace': #'MP-MKT-3017587446112951', 'marketplace_fee': 1, 'metadata': {}, 'notification_url': None, 'operation_type': 'regular_payment', 'payer': {'phone': {'area_code': '', 'number': ''}, #'address': {'zip_code': '', 'street_name': '', 'street_number': None}, 'email': 'pedro@pedro.pedro', 'identification': {'number': '', 'type': ''}, 'name': '', 'surname': '', #'date_created': None, 'last_purchase': None}, 'payment_methods': {'default_card_id': None, 'default_payment_method_id': None, 'excluded_payment_methods': [{'id': ''}], #'excluded_payment_types': [{'id': ''}], 'installments': None, 'default_installments': None}, 'processing_modes': None, 'product_id': None, 'preference_expired': False, 'redirect_urls': #{'failure': '', 'pending': '', 'success': ''}, 'sandbox_init_point': 'https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f', #'site_id': 'MLA', 'shipments': {'default_shipping_method': None, 'receiver_address': {'zip_code': '', 'street_name': '', 'street_number': None, 'floor': '', 'apartment': '', 'city_name': #None, 'state_name': None, 'country_name': None, 'neighborhood': None}}, 'total_amount': None, 'last_updated': None, 'financing_group': ''}


#result2 = create_payment("Test",2,"pedro@pedro.pedro","AF-04")
#print (result2) 
#order: owner-AF-03-393413645-caf9744c-6062-4baa-bae7-c06184ca51cf-pedro@pedro.pedro
#{'additional_info': '', 'auto_return': 'approved', 'back_urls': {'failure': 'https://juanguzzardi.com/failure', 'pending': 'https://juanguzzardi.com/pending', 'success': 'https://#juanguzzardi.com/success'}, 'binary_mode': False, 'client_id': '3017587446112951', 'collector_id': 393413645, 'coupon_code': None, 'coupon_labels': None, 'date_created': #'2026-02-22T19:41:44.625-04:00', 'date_of_expiration': None, 'expiration_date_from': None, 'expiration_date_to': None, 'expires': False, 'external_reference': 'AF-03', 'id': #'393413645-caf9744c-6062-4baa-bae7-c06184ca51cf', 'init_point': 'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=393413645-caf9744c-6062-4baa-bae7-c06184ca51cf', #'internal_metadata': None, 'items': [{'id': '', 'category_id': '', 'currency_id': 'ARS', 'description': '', 'title': 'para falopa', 'quantity': 1, 'unit_price': 2}], 'marketplace': #'MP-MKT-3017587446112951', 'marketplace_fee': 0, 'metadata': {}, 'notification_url': None, 'operation_type': 'regular_payment', 'payer': {'phone': {'area_code': '', 'number': ''}, #'address': {'zip_code': '', 'street_name': '', 'street_number': None}, 'email': 'pedro@pedro.pedro', 'identification': {'number': '', 'type': ''}, 'name': '', 'surname': '', #'date_created': None, 'last_purchase': None}, 'payment_methods': {'default_card_id': None, 'default_payment_method_id': None, 'excluded_payment_methods': [{'id': ''}], #'excluded_payment_types': [{'id': ''}], 'installments': None, 'default_installments': None}, 'processing_modes': None, 'product_id': None, 'preference_expired': False, 'redirect_urls': #{'failure': '', 'pending': '', 'success': ''}, 'sandbox_init_point': 'https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=393413645-caf9744c-6062-4baa-bae7-c06184ca51cf', #'site_id': 'MLA', 'shipments': {'default_shipping_method': None, 'receiver_address': {'zip_code': '', 'street_name': '', 'street_number': None, 'floor': '', 'apartment': '', 'city_name': #None, 'state_name': None, 'country_name': None, 'neighborhood': None}}, 'total_amount': None, 'last_updated': None, 'financing_group': ''}





#PS C:\Users\juans\OneDrive\Escritorio\apiDePagos> & C:\Python314\python.exe c:/Users/juans/OneDrive/Escritorio/apiDePagos/app/main.py
#INFO:     Started server process [9464]
#INFO:     Waiting for application startup.
#INFO:     Application startup complete.
#INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
#INFO:     201.216.219.234:0 - "GET / HTTP/1.0" 200 OK
#INFO:     201.216.219.234:0 - "GET /favicon.ico HTTP/1.0" 404 Not Found
#Webhook recibido: {
#  "action": "payment.created",
#  "api_version": "v1",
#  "data": {
#    "id": "146660993271"
#  },
#  "date_created": "2026-02-22T23:46:07Z",
#  "id": 129237727005,
#  "live_mode": true,
#  "type": "payment",
#  "user_id": "393413645"
#}
#Query params: {'data.id': '146660993271', 'type': 'payment'}
#external_reference: AF-03
#status: approved detail: accredited
#Order actualizada: AF-03 -> approved
#INFO:     18.213.114.129:0 - "POST /webhooks/?data.id=146660993271&type=payment HTTP/1.0" 200 OK
#Notificación recibida: {
#  "resource": "146660993271",
#  "topic": "payment"
#}
#INFO:     54.88.218.97:0 - "POST /notificaciones/?id=146660993271&topic=payment HTTP/1.0" 200 OK
#INFO:     176.96.137.48:0 - "GET /.well-known/security.txt HTTP/1.0" 404 Not Found
#INFO:     176.96.137.48:0 - "GET /security.txt HTTP/1.0" 404 Not Found
#INFO:     Shutting down
#INFO:     Waiting for application shutdown.
#INFO:     Application shutdown complete.
#INFO:     Finished server process [9464]
#


# res




def buscar_pago_por_referencia(external_reference):
    response = requests.get(
        "https://api.mercadopago.com/v1/payments/search",
        params={"external_reference": external_reference},
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
    )
    return response.json()

def get_payment(payment_id, access_token): # solo con el id que llega por el webhook
    r = requests.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return r.json()


#print(buscar_pago_por_referencia("AF-01"))
#print(buscar_pago_por_referencia("393413645-ea88842f-199d-4319-b3cf-044ea1431d90"))
#print(json.dumps(get_payment("393413645-ea88842f-199d-4319-b3cf-044ea1431d90",ACCESS_TOKEN), indent=2, ensure_ascii=False))

def search_recent_payments(access_token, limit=20):
    r = requests.get(
        "https://api.mercadopago.com/v1/payments/search",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"sort": "date_created", "criteria": "desc", "limit": limit}
    )
    return r.json()

#data = search_recent_payments(ACCESS_TOKEN, 2)
#print(json.dumps(data, indent=2, ensure_ascii=False))













#PS C:\Users\juans\OneDrive\Escritorio\apiDePagos> & C:\Python314\python.exe c:/Users/juans/OneDrive/Escritorio/apiDePagos/app/main.py
#INFO:     Started server process [17276]
#INFO:     Waiting for application startup.
#INFO:     Application startup complete.
#INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
#Webhook recibido: {
#  "action": "payment.created",
#  "api_version": "v1",
#  "data": {
#    "id": "146418677581"
#  },
#  "date_created": "2026-02-20T23:12:05Z",
#  "id": 129300404678,
#  "live_mode": true,
#  "type": "payment",
#  "user_id": "1179602589"
#}
#INFO:     54.88.218.97:0 - "POST /webhooks/?data.id=146418677581&type=payment HTTP/1.0" 200 OK
#Notificación recibida: {
#  "resource": "146418677581",
#  "topic": "payment"
#}
#INFO:     18.215.140.160:0 - "POST /notificaciones/?id=146418677581&topic=payment HTTP/1.0" 200 OK
#INFO:     190.210.32.20:0 - "GET /?collection_id=146418677581&collection_status=approved&payment_id=146418677581&status=approved&external_reference=BR-15&payment_type=account_money&#merchant_order_id=38377772360&preference_id=1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f&site_id=MLA&processing_mode=aggregator&merchant_account_id=null HTTP/1.0" 200 OK
#INFO:     Shutting down
#INFO:     Waiting for application shutdown.
#INFO:     Application shutdown complete.
#INFO:     Finished server process [17276]
#PS C:\Users\juans\OneDrive\Escritorio\apiDePagos> 



#Usando APP_USR-3017587446112951-021722-f0b1c8807f3f3d6329569fd4b66ec1ac-1179602589 se genero un pago
#{'additional_info': '', 'auto_return': 'approved', 'back_urls': {'failure': 'https://juanguzzardi.com/', 'pending': 'https://juanguzzardi.com/', 'success': 'https://juanguzzardi.com/'}, #'binary_mode': False, 'client_id': '3017587446112951', 'collector_id': 1179602589, 'coupon_code': None, 'coupon_labels': None, 'date_created': '2026-02-20T19:01:18.765-04:00', #'date_of_expiration': None, 'expiration_date_from': None, 'expiration_date_to': None, 'expires': False, 'external_reference': 'BR-15', 'id': #'1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f', 'init_point': 'https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f', #'internal_metadata': None, 'items': [{'id': '', 'category_id': '', 'currency_id': 'ARS', 'description': '', 'title': 'test', 'quantity': 1, 'unit_price': 10}], 'marketplace': #'MP-MKT-3017587446112951', 'marketplace_fee': 1, 'metadata': {}, 'notification_url': None, 'operation_type': 'regular_payment', 'payer': {'phone': {'area_code': '', 'number': ''}, #'address': {'zip_code': '', 'street_name': '', 'street_number': None}, 'email': 'pedro@pedro.pedro', 'identification': {'number': '', 'type': ''}, 'name': '', 'surname': '', #'date_created': None, 'last_purchase': None}, 'payment_methods': {'default_card_id': None, 'default_payment_method_id': None, 'excluded_payment_methods': [{'id': ''}], #'excluded_payment_types': [{'id': ''}], 'installments': None, 'default_installments': None}, 'processing_modes': None, 'product_id': None, 'preference_expired': False, 'redirect_urls': #{'failure': '', 'pending': '', 'success': ''}, 'sandbox_init_point': 'https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=1179602589-e015d7c9-b8d8-4ad3-bddb-2135e0d75f2f', #'site_id': 'MLA', 'shipments': {'default_shipping_method': None, 'receiver_address': {'zip_code': '', 'street_name': '', 'street_number': None, 'floor': '', 'apartment': '', 'city_name': #None, 'state_name': None, 'country_name': None, 'neighborhood': None}}, 'total_amount': None, 'last_updated': None, 'financing_group': ''}


import requests
import json
from credentials import ACCESS_TOKEN


def test_mp_payment(payment_id: str):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"

    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        timeout=20
    )

    print("\n========== MP RAW ==========")
    print("status_code:", r.status_code)
    print("text:", r.text)

    try:
        data = r.json()
    except Exception:
        print("No es json")
        return

    print("\n========== MP PARSED ==========")
    print(json.dumps(data, indent=2))

    print("\n========== IMPORTANT ==========")
    print("payment_id:", data.get("id"))
    print("status:", data.get("status"))
    print("status_detail:", data.get("status_detail"))
    print("external_reference:", data.get("external_reference"))
    print("amount:", data.get("transaction_amount"))
    print("payer_email:", (data.get("payer") or {}).get("email"))
    print("date_approved:", data.get("date_approved"))
    print("================================\n")

#test_mp_payment("146418677581")



#INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
#Notificación recibida: {
#  "resource": "147121886474",
#  "topic": "payment"
#}
#INFO:     18.206.34.84:0 - "POST /notificaciones/?id=147121886474&topic=payment HTTP/1.0" 200 OK
#Webhook recibido: {
#  "action": "payment.created",
#  "api_version": "v1",
#  "data": {
#    "id": "147121886474"
#  },
#  "date_created": "2026-02-20T23:34:35Z",
#  "id": 129301015486,
#  "live_mode": true,
#  "type": "payment",
#  "user_id": "1179602589"
#}
#Query params: {'data.id': '147121886474', 'type': 'payment'}
#MP payment status_code: 200
#MP payment: {
#  "accounts_info": null,
#  "acquirer_reconciliation": [],
#  "additional_info": {
#    "ip_address": "190.210.32.20",
#    "items": [
#      {
#        "quantity": "1",
#        "title": "test",
#        "unit_price": "2"
#      }
#    ],
#    "tracking_id": "platform:v1-blacklabel,so:ALL,type:N/A,security:none"
#  },
#  "authorization_code": null,
#  "binary_mode": false,
#  "brand_id": null,
#  "build_version": "3.143.0-rc-4",
#  "call_for_authorize_id": null,
#  "captured": true,
#  "card": {},
#  "charges_details": [
#    {
#      "accounts": {
#        "from": "collector",
#        "to": "mp"
#      },
#      "amounts": {
#        "original": 0.08,
#        "refunded": 0
#      },
#      "base_amount": 2,
#      "client_id": 0,
#      "date_created": "2026-02-20T19:34:35.000-04:00",
#      "external_charge_id": "01KHYPFDZKAB5SEJPD24605N8C",
#      "id": "147121886474-001",
#      "last_updated": "2026-02-20T19:34:35.000-04:00",
#      "metadata": {
#        "reason": "",
#        "source": "proc-svc-charges",
#        "source_detail": "processing_fee_charge"
#      },
#      "name": "mercadopago_fee",
#      "rate": 4.1,
#      "refund_charges": [],
#      "reserve_id": null,
#      "type": "fee",
#      "update_charges": []
#    }
#  ],
#  "charges_execution_info": {
#    "internal_execution": {
#      "date": "2026-02-20T19:34:35.267-04:00",
#      "execution_id": "01KHYPFDYVRD3WWHB6HZAW5XK6"
#    }
#  },
#  "collector": {
#    "email": null,
#    "first_name": null,
#    "id": 1179602589,
#    "identification": {
#      "number": null,
#      "type": null
#    },
#    "last_name": null,
#    "operator_id": null,
#    "phone": null
#  },
#  "corporation_id": null,
#  "counter_currency": null,
#  "coupon_amount": 0,
#  "currency_id": "ARS",
#  "date_approved": "2026-02-20T19:34:35.000-04:00",
#  "date_created": "2026-02-20T19:34:35.000-04:00",
#  "date_last_updated": "2026-02-20T19:34:35.000-04:00",
#  "date_of_expiration": null,
#  "deduction_schema": null,
#  "description": "test",
#  "differential_pricing_id": null,
#  "external_reference": "BR-16",
#  "fee_details": [
#    {
#      "amount": 0.08,
#      "fee_payer": "collector",
#      "type": "mercadopago_fee"
#    }
#  ],
#  "financing_group": null,
#  "id": 147121886474,
#  "installments": 1,
#  "integrator_id": null,
#  "issuer_id": "2005",
#  "live_mode": true,
#  "marketplace_owner": 393413645,
#  "merchant_account_id": null,
#  "merchant_number": null,
#  "metadata": {},
#  "money_release_date": "2026-03-10T19:34:35.000-04:00",
#  "money_release_schema": null,
#  "money_release_status": "pending",
#  "notification_url": null,
#  "operation_type": "regular_payment",
#  "order": {
#    "id": "38378562092",
#    "type": "mercadopago"
#  },
#  "payer_id": 393413645,
#  "payment_method": {
#    "id": "account_money",
#    "issuer_id": "2005",
#    "type": "account_money"
#  },
#  "payment_method_id": "account_money",
#  "payment_type_id": "account_money",
#  "platform_id": null,
#  "point_of_interaction": {
#    "application_data": {
#      "name": "checkout-off",
#      "operating_system": null,
#      "version": "v2"
#    },
#    "business_info": {
#      "branch": "Merchant Services",
#      "sub_unit": "checkout_pro",
#      "unit": "online_payments"
#    },
#    "location": {
#      "source": "Payer",
#      "state_id": "AR-C"
#    },
#    "transaction_data": {
#      "e2e_id": null
#    },
#    "type": "CHECKOUT"
#  },
#  "pos_id": null,
#  "processing_mode": "aggregator",
#  "refunds": [],
#  "release_info": null,
#  "shipping_amount": 0,
#  "sponsor_id": null,
#  "statement_descriptor": null,
#  "status": "approved",
#  "status_detail": "accredited",
#  "store_id": null,
#  "tags": null,
#  "taxes_amount": 0,
#  "transaction_amount": 2,
#  "transaction_amount_refunded": 0,
#  "transaction_details": {
#    "acquirer_reference": null,
#    "external_resource_url": null,
#    "financial_institution": null,
#    "installment_amount": 0,
#    "net_received_amount": 1.92,
#    "overpaid_amount": 0,
#    "payable_deferral_period": null,
#    "payment_method_reference_id": null,
#    "total_paid_amount": 2
#  }
#}
#external_reference: BR-16
#status: approved detail: accredited
#Order actualizada: BR-16 -> approved
#INFO:     18.215.140.160:0 - "POST /webhooks/?data.id=147121886474&type=payment HTTP/1.0" 200 OK
#INFO:     190.210.32.20:0 - "GET /?collection_id=147121886474&collection_status=approved&payment_id=147121886474&status=approved&external_reference=BR-16&payment_type=account_money&#merchant_order_id=38378562092&preference_id=1179602589-124b5de4-3bd9-49f7-bd18-f598dbe4e65e&site_id=MLA&processing_mode=aggregator&merchant_account_id=null HTTP/1.0" 200 OK
#INFO:     Shutting down
#INFO:     Waiting for application shutdown.
#INFO:     Application shutdown complete.
#INFO:     Finished server process [17264]
#PS C:\Users\juans\OneDrive\Escritorio\apiDePagos> 



from ModelsYDB import Order


order = Order.by_external_reference("BR-17")
order.state = "none"
order.save()





#Notificación recibida: {
#  "resource": "146425997567",
#  "topic": "payment"
#}
#INFO:     54.88.218.97:0 - "POST /notificaciones/?id=146425997567&topic=payment HTTP/1.0" 200 OK
#Webhook recibido: {
#  "action": "payment.created",
#  "api_version": "v1",
#  "data": {
#    "id": "146425997567"
#  },
#  "date_created": "2026-02-20T23:58:12Z",
#  "id": 129301782926,
#  "live_mode": true,
#  "type": "payment",
#  "user_id": "1179602589"
#}
#Query params: {'data.id': '146425997567', 'type': 'payment'}
#external_reference: BR-18
#status: approved detail: accredited
#Order actualizada: BR-18 -> approved
#INFO:     18.215.140.160:0 - "POST /webhooks/?data.id=146425997567&type=payment HTTP/1.0" 200 OK
#INFO:     190.210.32.20:0 - "GET /?collection_id=146425997567&collection_status=approved&payment_id=146425997567&status=approved&external_reference=BR-18&payment_type=account_money&#merchant_order_id=38379367488&preference_id=1179602589-a909a37e-21ee-4ebe-9e7e-58ba1a183254&site_id=MLA&processing_mode=aggregator&merchant_account_id=null HTTP/1.0" 200 OK
#INFO:     Shutting down
#INFO:     Waiting for application shutdown.
#INFO:     Application shutdown complete.
#INFO:     Finished server process [3908]
#