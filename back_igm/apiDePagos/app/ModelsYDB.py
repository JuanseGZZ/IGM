import os
import sqlite3
DB_PATH = "organizers.db"


class Organizers:
    def __init__(
        self,
        associated="",
        user_id="",
        access_token="",
        refresh_token="",
        expires_in=0,
        scope="",
        token_type="",
        created_at=0,
    ):
        self.associated = associated
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in
        self.scope = scope
        self.token_type = token_type
        self.created_at = created_at

    def save(self):
        if not self.associated:
            raise ValueError("associated no puede ser vacio (es la PK).")

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO organizers (
                    associated, user_id, access_token, refresh_token,
                    expires_in, scope, token_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(associated) DO UPDATE SET
                    user_id = excluded.user_id,
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_in = excluded.expires_in,
                    scope = excluded.scope,
                    token_type = excluded.token_type,
                    created_at = strftime('%s','now')
                """,
                (
                    self.associated,
                    self.user_id,
                    self.access_token,
                    self.refresh_token,
                    int(self.expires_in or 0),
                    self.scope,
                    self.token_type,
                ),
            )

            conn.commit()

            # refresco created_at en el objeto (opcional pero util)
            cur.execute(
                "SELECT created_at FROM organizers WHERE associated = ?",
                (self.associated,),
            )
            row = cur.fetchone()
            if row is not None:
                self.created_at = int(row["created_at"] or 0)

            return self
        finally:
            conn.close()

    @staticmethod
    def find_by_associated(associated: str):
        if not associated:
            return None

        conn = sqlite3.connect(DB_PATH)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT associated, user_id, access_token, refresh_token,
                       expires_in, scope, token_type, created_at
                FROM organizers
                WHERE associated = ?
                LIMIT 1
                """,
                (associated,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            return Organizers(
                associated=row["associated"],
                user_id=row["user_id"] or "",
                access_token=row["access_token"] or "",
                refresh_token=row["refresh_token"] or "",
                expires_in=int(row["expires_in"] or 0),
                scope=row["scope"] or "",
                token_type=row["token_type"] or "",
                created_at=int(row["created_at"] or 0),
            )
        finally:
            conn.close()


class Order:
    def __init__(self, user_email, external_reference, mp_id, associated="none", state="procesing", until=0):
        self.user_email = user_email
        self.external_reference = external_reference
        self.mp_id = mp_id
        self.associated = associated
        self.state = state
        self.until = until

    def save(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO orders (external_reference, mp_id, user_email, associated, state, until)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_reference) DO UPDATE SET
                mp_id = excluded.mp_id,
                user_email = excluded.user_email,
                associated = excluded.associated,
                state = excluded.state,
                until = excluded.until
        """, (
            self.external_reference,
            self.mp_id,
            self.user_email,
            self.associated,
            self.state,
            self.until
        ))

        conn.commit()
        conn.close()

    @staticmethod
    def by_external_reference(external_reference):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
    
        cur.execute("""
            SELECT user_email, external_reference, mp_id, associated, state, until
            FROM orders
            WHERE external_reference = ?
            LIMIT 1
        """, (external_reference,))
    
        row = cur.fetchone()
        conn.close()
    
        if not row:
            return None
    
        return Order(*row)
    
    @staticmethod
    def by_mp_id(mp_id):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
    
        cur.execute("""
            SELECT user_email, external_reference, mp_id, associated, state, until
            FROM orders
            WHERE mp_id = ?
            LIMIT 1
        """, (mp_id,))
    
        row = cur.fetchone()
        conn.close()
    
        if not row:
            return None
    
        return Order(*row)
    

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS organizers (
                associated TEXT PRIMARY KEY,
                user_id TEXT,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_in INTEGER,
                scope TEXT,
                token_type TEXT,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )
        conn.commit()
        conn.close()
