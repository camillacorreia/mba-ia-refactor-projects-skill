import logging

from controllers.common import require_object
from database import db
from models.task import Task
from models.user import (
    DEFAULT_ROLE,
    User,
    validate_email,
    validate_name,
    validate_password,
    validate_role,
)
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = 'Credenciais inválidas'


def _get_user(user_id):
    user = User.find(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def _ensure_email_available(email, current_user_id=None):
    existing = User.find_by_email(email)
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def list_users():
    task_counts = Task.count_by(Task.user_id)
    result = []
    for user in User.list_all():
        data = user.to_dict()
        data['task_count'] = task_counts.get(user.id, 0)
        result.append(data)
    return result, 200


def get_user(user_id):
    user = _get_user(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.list_by_user(user_id)]
    return data, 200


def create_user(payload):
    data = require_object(payload)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    validate_name(name)
    validate_email(email)
    validate_password(password, 'Senha deve ter no mínimo 4 caracteres')
    _ensure_email_available(email)
    validate_role(role)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    user.save()
    logger.info('Usuário criado id=%s', user.id)
    return user.to_dict(), 201


def update_user(user_id, payload):
    user = _get_user(user_id)
    data = require_object(payload)

    if 'name' in data:
        user.name = validate_name(data['name'])
    if 'email' in data:
        validate_email(data['email'])
        _ensure_email_available(data['email'], current_user_id=user_id)
        user.email = data['email']
    if 'password' in data:
        user.set_password(validate_password(data['password'], 'Senha muito curta'))
    if 'role' in data:
        user.role = validate_role(data['role'])
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Campo active deve ser booleano')
        user.active = data['active']

    user.save()
    return user.to_dict(), 200


def delete_user(user_id):
    _get_user(user_id).delete()  # as tasks do usuário saem junto (cascade no model)
    logger.info('Usuário deletado id=%s', user_id)
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id):
    _get_user(user_id)
    return [task.to_summary_dict() for task in Task.list_by_user(user_id)], 200


def login(payload):
    data = require_object(payload)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.find_by_email(email)
    if not user or not isinstance(password, str) or not user.check_password(password):
        raise UnauthorizedError(INVALID_CREDENTIALS)
    db.session.commit()  # grava o hash novo quando a senha ainda estava em MD5
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id),  # sem autenticação real ainda (AP-04, fora do escopo)
    }, 200
