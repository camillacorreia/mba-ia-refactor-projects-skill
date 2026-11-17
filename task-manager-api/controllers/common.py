from database import db
from utils.errors import NotFoundError, ValidationError


def require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def get_or_404(model, entity_id, message):
    entity = db.session.get(model, entity_id)
    if entity is None:
        raise NotFoundError(message)
    return entity
