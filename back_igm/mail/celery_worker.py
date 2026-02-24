# celery_worker.py
import os
import time
from celery import Celery

from gmail_core import send_email


BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery("mailer", broker=BROKER_URL, backend=BROKER_URL)

# Importante: si tu worker se cae/reintenta, queremos evitar dobles envios por error de ACK.
# Para un MVP lo dejamos simple.
@celery_app.task(name="tasks.send_email_task")
def send_email_task(to_email: str, subject: str, body_text: str, account_id: str = "default", db_path: str = "gmail_oauth.sqlite3"):
    # envia 1 mail
    res = send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        account_id=account_id,
        db_path=db_path,
    )

    # rate limit fijo: 1 mail cada 45s
    time.sleep(45)

    return res
