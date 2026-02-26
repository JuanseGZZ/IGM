import os
import json
import time
import hmac
import base64
import hashlib
import secrets


class JWT:
    # Archivo de claves (un secreto HMAC por kid)
    KEY_FILE = os.path.join(os.path.dirname(__file__), "jwt_keys.json")

    def __init__(self, user: str, rango: str, access_ttl: int = 900, refresh_ttl: int = 7 * 24 * 3600):
        self.user = user
        self.rango = rango
        self.access_ttl = int(access_ttl)
        self.refresh_ttl = int(refresh_ttl)

        keys = self._load_or_create_keys()
        self.kid = keys["active_kid"]

        self.access_token = None
        self.refresh_token = None

        self._issue_new_pair()

    # -------------------------
    # Public API
    # -------------------------

    def refresh(self, rt: str) -> str:
        """
        Valida el refresh token recibido, rota AT/RT, actualiza el objeto y retorna el nuevo access token.
        """
        if not rt:
            raise ValueError("refresh token requerido")

        # Si queres forzar que solo refresque con el RT actual del objeto:
        if self.refresh_token is None or rt != self.refresh_token:
            raise ValueError("refresh token no coincide con el del objeto")

        payload = self._verify_jwt(rt, expected_type="refresh")

        # Extra validacion de identidad (opcional pero recomendable)
        if payload.get("sub") != self.user:
            raise ValueError("refresh token no corresponde a este usuario")

        # Rotacion: nuevo AT + nuevo RT
        self._issue_new_pair()
        return self.access_token

    @staticmethod
    def verify(access_token: str) -> dict:
        """
        Verifica firma (y exp) del access token usando el archivo de claves.
        Retorna el payload si es valido.
        """
        if not access_token:
            raise ValueError("access token requerido")

        keys = JWT._load_or_create_keys()
        header, payload = JWT._decode_no_verify(access_token)

        if payload.get("type") != "access":
            raise ValueError("no es access token")

        kid = header.get("kid") or payload.get("kid")
        if not kid:
            raise ValueError("token sin kid")

        secret = keys["keys"].get(kid)
        if not secret:
            raise ValueError("kid desconocido")

        JWT._verify_signature(access_token, secret)
        JWT._verify_exp(payload)

        return payload

    # -------------------------
    # Token issuing
    # -------------------------

    def _issue_new_pair(self) -> None:
        now = int(time.time())

        # Access Token
        at_payload = {
            "sub": self.user,
            "rango": self.rango,
            "type": "access",
            "iat": now,
            "exp": now + self.access_ttl,
            "kid": self.kid,
            "jti": secrets.token_hex(8),
        }
        self.access_token = self._sign_jwt(at_payload, kid=self.kid)

        # Refresh Token
        rt_payload = {
            "sub": self.user,
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_ttl,
            "kid": self.kid,
            "jti": secrets.token_hex(8),
        }
        self.refresh_token = self._sign_jwt(rt_payload, kid=self.kid)

    # -------------------------
    # JWT internals (HS256)
    # -------------------------

    @staticmethod
    def _b64e(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("utf-8")

    @staticmethod
    def _b64d(s: str) -> bytes:
        pad = "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode((s + pad).encode("utf-8"))

    @staticmethod
    def _encode_json(obj: dict) -> str:
        return JWT._b64e(json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

    @staticmethod
    def _decode_json(b64: str) -> dict:
        return json.loads(JWT._b64d(b64).decode("utf-8"))

    def _sign_jwt(self, payload: dict, kid: str) -> str:
        keys = self._load_or_create_keys()
        secret = keys["keys"][kid]

        header = {"alg": "HS256", "typ": "JWT", "kid": kid}

        h = self._encode_json(header)
        p = self._encode_json(payload)
        msg = f"{h}.{p}".encode("utf-8")

        sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
        s = self._b64e(sig)

        return f"{h}.{p}.{s}"

    def _verify_jwt(self, token: str, expected_type: str) -> dict:
        keys = self._load_or_create_keys()
        header, payload = self._decode_no_verify(token)

        if payload.get("type") != expected_type:
            raise ValueError(f"no es token tipo {expected_type}")

        kid = header.get("kid") or payload.get("kid")
        if not kid:
            raise ValueError("token sin kid")

        secret = keys["keys"].get(kid)
        if not secret:
            raise ValueError("kid desconocido")

        self._verify_signature(token, secret)
        self._verify_exp(payload)

        return payload

    @staticmethod
    def _decode_no_verify(token: str) -> tuple[dict, dict]:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("formato JWT invalido")

        header = JWT._decode_json(parts[0])
        payload = JWT._decode_json(parts[1])
        return header, payload

    @staticmethod
    def _verify_signature(token: str, secret: str) -> None:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("formato JWT invalido")

        h, p, s = parts
        msg = f"{h}.{p}".encode("utf-8")

        expected = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
        expected_b64 = JWT._b64e(expected)

        if not hmac.compare_digest(s, expected_b64):
            raise ValueError("firma invalida")

    @staticmethod
    def _verify_exp(payload: dict) -> None:
        exp = payload.get("exp")
        if exp is None:
            raise ValueError("token sin exp")

        if int(time.time()) > int(exp):
            raise ValueError("token expirado")

    # -------------------------
    # Key file
    # -------------------------

    @staticmethod
    def _load_or_create_keys() -> dict:
        path = JWT.KEY_FILE

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validacion minima
            if "active_kid" not in data or "keys" not in data or not data["keys"]:
                raise ValueError("archivo de claves invalido")
            return data

        # Si no existe, crea uno
        os.makedirs(os.path.dirname(path), exist_ok=True)

        kid = "k1"
        secret = secrets.token_urlsafe(48)  # secreto HMAC
        data = {"active_kid": kid, "keys": {kid: secret}}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data
    

    @staticmethod
    def decode_unverified(token: str) -> dict:
        # Solo para leer payload. NO verifica firma.
        _, payload = JWT._decode_no_verify(token)
        return payload

    def toJson(self) -> dict:
        return {
            "at": self.access_token,
            "rt": self.refresh_token,
        }

    @staticmethod
    def fromJson(data: dict) -> "JWT":
        at = data.get("at")
        rt = data.get("rt")

        if not at or not rt:
            raise ValueError("faltan at/rt")

        payload = JWT.decode_unverified(at)

        user = payload.get("sub")
        rango = payload.get("rango")
        if not user or not rango:
            raise ValueError("at no contiene sub/rango")

        # Crear objeto sin depender de TTLs persistidos
        obj = JWT(user=str(user), rango=str(rango))

        # Sobrescribir tokens generados en __init__
        obj.access_token = at
        obj.refresh_token = rt

        # Mantener el kid del token si viene
        obj.kid = payload.get("kid", obj.kid)

        return obj
    




    
def test():
    jwt = JWT(user="patroncito", rango="admin")

    at = jwt.access_token
    rt = jwt.refresh_token

    payload = JWT.verify(at)

    new_at = jwt.refresh(rt)
    new_rt = jwt.refresh_token