# app.py
# Gmail OAuth2 + Gmail API sender
# - start_oauth(): funcion (devuelve URL)
# - refresh_token(): funcion
# - send_email(): funcion (llama refresh_token antes)
# - callback endpoint: /auth/google/callback (obligatorio para Google)
# - TODO guardado en SQLite (tokens + state)

import time
import requests
from fastapi import FastAPI, HTTPException
from gmail_core import start_oauth, init_db,_consume_state,_cfg,_db,_upsert_tokens

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
SCOPE = "https://www.googleapis.com/auth/gmail.send"


app = FastAPI()

@app.get("/auth/google/callback")
def auth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    account_id: str = "default",
    db_path: str = "gmail_oauth.sqlite3",
):
    """
    Endpoint obligatorio (Google vuelve aca).
    Guarda refresh/access en SQLite.
    """
    if error:
        raise HTTPException(400, f"Google error: {error}")
    if not code or not state:
        raise HTTPException(400, "Missing code/state")

    init_db(db_path)
    cid, csec, ruri = _cfg()

    con = _db(db_path)
    try:
        if not _consume_state(con, state):
            raise HTTPException(400, "Invalid state")
    finally:
        con.close()

    data = {
        "client_id": cid,
        "client_secret": csec,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": ruri,
    }
    r = requests.post(TOKEN_URL, data=data, timeout=20)
    if r.status_code != 200:
        raise HTTPException(400, {"status": r.status_code, "body": r.text})

    tokens = r.json()
    refresh_tok = tokens.get("refresh_token")
    if not refresh_tok:
        raise HTTPException(
            400,
            "No refresh_token returned. Revoca acceso de la app en tu cuenta Google y reintenta.",
        )

    access_tok = tokens.get("access_token")
    expires_in = int(tokens.get("expires_in", 3600))
    expiry = int(time.time()) + expires_in

    con = _db(db_path)
    try:
        _upsert_tokens(con, account_id, refresh_tok, access_tok, expiry)
    finally:
        con.close()

    return {"ok": True, "saved_account_id": account_id}


from celery_worker import send_email_task
def enqueue_email(
    to_email: str,
    subject: str,
    body_text: str,
    account_id: str = "default",
    db_path: str = "gmail_oauth.sqlite3",
) -> str:
    """
    Encola el envio. Devuelve task_id.
    """
    job = send_email_task.delay(to_email, subject, body_text, account_id, db_path)
    return job.id

if __name__ == "__main__":
    import uvicorn
    init_db("gmail_oauth.sqlite3")
    uvicorn.run("app:app", host="0.0.0.0", port=9000, reload=True)
