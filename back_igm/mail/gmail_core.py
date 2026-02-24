import time
import base64
import sqlite3
import secrets
from typing import Optional, Dict, Any

import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import os


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
SCOPE = "https://www.googleapis.com/auth/gmail.send"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def _cfg() -> tuple[str, str, str]:
    cid = GOOGLE_CLIENT_ID
    csec = GOOGLE_CLIENT_SECRET
    ruri = "https://juanguzzardi.com/auth/google/callback"
    if not cid or not csec or not ruri:
        raise RuntimeError("Faltan envs: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI")
    return cid, csec, ruri


def _db(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def init_db(db_path: str = "gmail_oauth.sqlite3") -> None:
    con = _db(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS gmail_tokens (
                account_id TEXT PRIMARY KEY,
                refresh_token TEXT NOT NULL,
                access_token TEXT,
                access_token_expiry INTEGER,
                updated_at INTEGER NOT NULL
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_states (
                state TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL
            )
            """
        )
        con.commit()
    finally:
        con.close()


def _get_tokens(con: sqlite3.Connection, account_id: str) -> Optional[Dict[str, Any]]:
    cur = con.execute(
        "SELECT refresh_token, access_token, access_token_expiry FROM gmail_tokens WHERE account_id=?",
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"refresh_token": row[0], "access_token": row[1], "access_token_expiry": row[2]}


def _upsert_tokens(
    con: sqlite3.Connection,
    account_id: str,
    refresh_token: str,
    access_token: Optional[str],
    access_token_expiry: Optional[int],
) -> None:
    now = int(time.time())
    con.execute(
        """
        INSERT INTO gmail_tokens (account_id, refresh_token, access_token, access_token_expiry, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(account_id) DO UPDATE SET
            refresh_token=excluded.refresh_token,
            access_token=COALESCE(excluded.access_token, gmail_tokens.access_token),
            access_token_expiry=COALESCE(excluded.access_token_expiry, gmail_tokens.access_token_expiry),
            updated_at=excluded.updated_at
        """,
        (account_id, refresh_token, access_token, access_token_expiry, now),
    )
    con.commit()


def _save_state(con: sqlite3.Connection, state: str) -> None:
    con.execute(
        "INSERT INTO oauth_states (state, created_at) VALUES (?, ?)",
        (state, int(time.time())),
    )
    con.commit()


def _consume_state(con: sqlite3.Connection, state: str) -> bool:
    cur = con.execute("SELECT state FROM oauth_states WHERE state=?", (state,))
    if not cur.fetchone():
        return False
    con.execute("DELETE FROM oauth_states WHERE state=?", (state,))
    con.commit()
    return True


def start_oauth(account_id: str = "default", db_path: str = "gmail_oauth.sqlite3") -> str:
    """
    Funcion llamable.
    Devuelve la URL de Google para iniciar OAuth.
    NOTA: esta funcion debe ejecutarse en el MISMO server/DB que recibe el callback,
    o el state no va a validar.
    """
    cid, _, ruri = _cfg()
    init_db(db_path)

    state = secrets.token_urlsafe(24)

    con = _db(db_path)
    try:
        _save_state(con, state)
    finally:
        con.close()

    params = {
        "client_id": cid,
        "redirect_uri": ruri,   # debe coincidir EXACTO con el registrado en Google Cloud
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    # account_id no va en redirect_uri (Google no acepta query ahi)
    # lo pasas vos por fuera si queres, o usas account_id fijo.
    return requests.Request("GET", AUTH_URL, params=params).prepare().url




def refresh_token(account_id: str = "default", db_path: str = "gmail_oauth.sqlite3") -> str:
    """
    Funcion llamable.
    Devuelve access_token valido (cacheado o refrescado) y lo guarda en SQLite.
    """
    init_db(db_path)
    cid, csec, _ = _cfg()

    con = _db(db_path)
    try:
        t = _get_tokens(con, account_id)
        if not t:
            raise ValueError("No hay refresh_token guardado. Corre OAuth primero.")

        now = int(time.time())
        if t["access_token"] and t["access_token_expiry"] and (t["access_token_expiry"] - now) > 60:
            return t["access_token"]

        data = {
            "client_id": cid,
            "client_secret": csec,
            "refresh_token": t["refresh_token"],
            "grant_type": "refresh_token",
        }
        r = requests.post(TOKEN_URL, data=data, timeout=20)
        if r.status_code != 200:
            raise ValueError(f"Refresh failed: {r.status_code} {r.text}")

        payload = r.json()
        access_tok = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        expiry = now + expires_in

        _upsert_tokens(con, account_id, t["refresh_token"], access_tok, expiry)
        return access_tok
    finally:
        con.close()



def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    account_id: str = "default",
    db_path: str = "gmail_oauth.sqlite3",
) -> Dict[str, Any]:
    """
    Funcion llamable.
    Envia email por Gmail API. Usa refresh_token() antes.
    """
    access_tok = refresh_token(account_id=account_id, db_path=db_path)

    msg = MIMEMultipart()
    msg["To"] = to_email
    msg["From"] = "me"
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    r = requests.post(
        GMAIL_SEND_URL,
        headers={"Authorization": f"Bearer {access_tok}"},
        json={"raw": raw},
        timeout=20,
    )

    if r.status_code == 401:
        # 1 reintento forzado (por si token cacheado quedo viejo)
        access_tok = refresh_token(account_id=account_id, db_path=db_path)
        r = requests.post(
            GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {access_tok}"},
            json={"raw": raw},
            timeout=20,
        )

    if r.status_code != 200:
        raise ValueError(f"Send failed: {r.status_code} {r.text}")

    return r.json()
