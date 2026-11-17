"""Autenticação administrativa: header X-Admin-Token ou Bearer token de um admin."""
import hmac
from functools import wraps

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models.user import ROLE_ADMIN
from utils.errors import ForbiddenError

_TOKEN_SALT = 'auth-token'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_TOKEN_SALT)


def issue_token(user):
    return _serializer().dumps({'sub': user.id, 'role': user.role})


def verify_token(token):
    if not token:
        return None
    try:
        return _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except (BadSignature, SignatureExpired):
        return None


def has_admin_credentials():
    expected = current_app.config.get('ADMIN_TOKEN') or ''
    provided = request.headers.get('X-Admin-Token', '')
    if expected and hmac.compare_digest(provided.encode(), expected.encode()):
        return True

    authorization = request.headers.get('Authorization', '')
    if authorization.startswith('Bearer '):
        claims = verify_token(authorization.removeprefix('Bearer ').strip())
        return bool(claims) and claims.get('role') == ROLE_ADMIN
    return False


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not has_admin_credentials():
            raise ForbiddenError('Acesso administrativo negado')
        return view(*args, **kwargs)
    return wrapper
