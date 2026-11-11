"""Proteção das rotas administrativas por token (header X-Admin-Token)."""
import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError


def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided.encode(), expected.encode()):
            raise ForbiddenError("Acesso administrativo negado", sucesso=False)
        return view(*args, **kwargs)

    return wrapper
