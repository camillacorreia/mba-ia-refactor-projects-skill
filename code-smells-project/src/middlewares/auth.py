"""Autorização: token administrativo (X-Admin-Token) ou Bearer emitido pelo login."""
import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError
from src.models.usuario_model import TIPO_ADMIN
from src.services.auth_service import verificar_token


def _tem_token_admin():
    esperado = current_app.config.get("ADMIN_TOKEN") or ""
    recebido = request.headers.get("X-Admin-Token", "")
    return bool(esperado) and hmac.compare_digest(recebido.encode(), esperado.encode())


def _claims_bearer():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return verificar_token(header.removeprefix("Bearer ").strip())


def _is_admin():
    if _tem_token_admin():
        return True
    claims = _claims_bearer()
    return bool(claims) and claims.get("tipo") == TIPO_ADMIN


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _is_admin():
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)
    return wrapper


def require_admin_or_self(param):
    """Admin ou o próprio usuário (Bearer com sub igual ao id da rota)."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if _is_admin():
                return view(*args, **kwargs)
            claims = _claims_bearer()
            if claims and claims.get("sub") == kwargs.get(param):
                return view(*args, **kwargs)
            raise ForbiddenError("Acesso negado")
        return wrapper
    return decorator
