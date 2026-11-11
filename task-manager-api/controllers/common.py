from utils.errors import ValidationError


def require_object(payload):
    """Corpo JSON precisa ser um objeto não vazio (mesma regra e mensagem do código original)."""
    if not payload or not isinstance(payload, dict):
        raise ValidationError('Dados inválidos')
    return payload


def parse_int_param(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f'Parâmetro {name} inválido') from None
