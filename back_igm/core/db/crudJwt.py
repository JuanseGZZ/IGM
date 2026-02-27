# crudJwt.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, Protocol

from models import JWT


class JwtError(Exception):
    pass


class JwtValidationError(JwtError):
    pass


class JwtRefreshError(JwtError):
    pass


class JwtIssueError(JwtError):
    pass


class JwtRepositoryProtocol(Protocol):
    def save_pair(self, user: str, pair: Dict[str, str]) -> None: ...
    def load_pair(self, user: str) -> Optional[Dict[str, str]]: ...
    def delete_pair(self, user: str) -> None: ...


@dataclass(frozen=True)
class TokenPair:
    at: str
    rt: str

    def to_dict(self) -> Dict[str, str]:
        return {"at": self.at, "rt": self.rt}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TokenPair":
        at = d.get("at")
        rt = d.get("rt")
        if not at or not rt:
            raise JwtIssueError("token pair invalido (faltan at/rt)")
        return TokenPair(at=str(at), rt=str(rt))


class JwtCRUD:
    """
    Capa de negocio para JWT:
    - issue: crea par AT/RT y lo persiste via repository
    - validate: valida access token
    - refresh: valida refresh token contra el par persistido y rota
    - revoke: borra el par persistido
    """

    def __init__(self, repo: JwtRepositoryProtocol, access_ttl: int = 900, refresh_ttl: int = 7 * 24 * 3600):
        self.repo = repo
        self.access_ttl = int(access_ttl)
        self.refresh_ttl = int(refresh_ttl)

    def issue(self, user: str, rango: str) -> TokenPair:
        """
        Crea un JWT nuevo para user/rango, persiste el par AT/RT y lo retorna.
        """
        if not user or not rango:
            raise JwtIssueError("user y rango son requeridos")

        jwt = JWT(user=str(user), rango=str(rango), access_ttl=self.access_ttl, refresh_ttl=self.refresh_ttl)
        pair = TokenPair(at=jwt.access_token, rt=jwt.refresh_token)

        self.repo.save_pair(user=str(user), pair=pair.to_dict())
        return pair

    def validate(self, access_token: str) -> Dict[str, Any]:
        """
        Valida firma + exp del access token.
        Retorna payload si es valido.
        """
        try:
            return JWT.verify(access_token)
        except Exception as e:
            raise JwtValidationError(str(e))

    def refresh(self, user: str, refresh_token: str) -> TokenPair:
        """
        Refresca tokens para un user, usando el refresh_token provisto.
        Usa el par persistido como "source of truth".
        """
        if not user:
            raise JwtRefreshError("user requerido")
        if not refresh_token:
            raise JwtRefreshError("refresh_token requerido")

        stored = self.repo.load_pair(user=str(user))
        if not stored:
            raise JwtRefreshError("no hay sesion activa para este user")

        try:
            jwt = JWT.fromJson(stored)  # reconstruye objeto con at/rt persistidos
        except Exception as e:
            raise JwtRefreshError(f"pair persistido invalido: {e}")

        # Tu implementacion exige que el RT coincida con el del objeto
        try:
            jwt.refresh(refresh_token)
        except Exception as e:
            raise JwtRefreshError(str(e))

        new_pair = TokenPair(at=jwt.access_token, rt=jwt.refresh_token)
        self.repo.save_pair(user=str(user), pair=new_pair.to_dict())
        return new_pair

    def revoke(self, user: str) -> None:
        """
        Invalida la sesion eliminando el par persistido.
        """
        if not user:
            raise JwtError("user requerido")
        self.repo.delete_pair(user=str(user))

    def decode_unverified(self, token: str) -> Dict[str, Any]:
        """
        Solo lectura de payload sin verificar firma.
        """
        return JWT.decode_unverified(token)