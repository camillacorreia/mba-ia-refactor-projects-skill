import logging

from controllers.common import get_or_404, require_payload
from database import commit, db
from middlewares.auth import has_admin_credentials, issue_token
from models.task import Task
from models.user import DEFAULT_ROLE, VALID_ROLES, User, is_valid_email, is_valid_password
from utils.errors import ConflictError, ForbiddenError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'


def _validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def _ensure_email_available(email, current_user_id=None):
    existing = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if existing and existing.id != current_user_id:
        raise ConflictError('Email já cadastrado')


def list_users():
    task_count = db.select(db.func.count(Task.id)).where(Task.user_id == User.id).scalar_subquery()
    rows = db.session.execute(db.select(User, task_count).order_by(User.id)).all()
    return [{**user.to_dict(), 'task_count': count} for user, count in rows]


def get_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    tasks = db.session.execute(db.select(Task).where(Task.user_id == user_id)).scalars().all()
    return {**user.to_dict(), 'tasks': [task.to_dict() for task in tasks]}


def create_user(payload):
    data = require_payload(payload)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    role = data.get('role', DEFAULT_ROLE)

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    if not is_valid_password(password):
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    _ensure_email_available(email)
    _validate_role(role)
    if role != DEFAULT_ROLE and not has_admin_credentials():
        raise ForbiddenError('Definir papel exige credencial administrativa')

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    commit()
    logger.info('user_created id=%s', user.id)
    return user.to_dict()


def update_user(user_id, payload):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    data = require_payload(payload)

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not is_valid_email(data['email']):
            raise ValidationError('Email inválido')
        _ensure_email_available(data['email'], current_user_id=user_id)
        user.email = data['email']
    if 'password' in data:
        if not is_valid_password(data['password']):
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        user.role = _validate_role(data['role'])
    if 'active' in data:
        user.active = data['active']

    commit()
    return user.to_dict()


def delete_user(user_id):
    user = get_or_404(User, user_id, USER_NOT_FOUND)
    db.session.execute(db.delete(Task).where(Task.user_id == user_id))
    db.session.delete(user)
    commit()
    logger.info('user_deleted id=%s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def list_user_tasks(user_id):
    get_or_404(User, user_id, USER_NOT_FOUND)
    tasks = db.session.execute(db.select(Task).where(Task.user_id == user_id)).scalars().all()
    return [task.to_summary_dict() for task in tasks]


def login(payload):
    data = require_payload(payload)
    email, password = data.get('email'), data.get('password')
    if not email or not password or not isinstance(password, str):
        raise ValidationError('Email e senha são obrigatórios')

    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    commit()  # persiste a migração do hash MD5 legado, quando houver
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': issue_token(user),
    }
