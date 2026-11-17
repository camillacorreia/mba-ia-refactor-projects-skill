"""Emissão e verificação do token assinado devolvido pelo login."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_SALT = "auth-token"


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def emitir_token(usuario):
    return _serializer().dumps({"sub": usuario["id"], "tipo": usuario["tipo"]})


def verificar_token(token):
    if not token:
        return None
    try:
        return _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except (BadSignature, SignatureExpired):
        return None
