import logging

from flask import current_app

from controllers.common import get_or_404, require_payload
from database import commit, db
from models.category import Category
from models.task import DEFAULT_PRIORITY, STATUS_PENDING, Task, validate_priority, validate_status, validate_title
from models.user import User
from services import report_service
from utils.errors import ValidationError

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def _check_references(user_id, category_id):
    if user_id:
        get_or_404(User, user_id, USER_NOT_FOUND)
    if category_id:
        get_or_404(Category, category_id, CATEGORY_NOT_FOUND)


def _notify_assignment(task):
    if task.user is not None:
        current_app.extensions['notification_service'].notify_task_assigned(task.user, task)


def list_tasks():
    tasks = db.session.execute(
        db.select(Task).options(db.joinedload(Task.user), db.joinedload(Task.category)).order_by(Task.id)
    ).scalars().all()
    return [task.to_dict(include_overdue=True, include_relation_names=True) for task in tasks]


def get_task(task_id):
    return get_or_404(Task, task_id, TASK_NOT_FOUND).to_dict(include_overdue=True)


def create_task(payload):
    data = require_payload(payload)
    validate_title(data.get('title'))
    validate_status(data.get('status', STATUS_PENDING))
    validate_priority(data.get('priority', DEFAULT_PRIORITY))
    _check_references(data.get('user_id'), data.get('category_id'))

    task = Task(
        description=data.get('description', ''),
        status=STATUS_PENDING,
        priority=DEFAULT_PRIORITY,
        user_id=data.get('user_id'),
        category_id=data.get('category_id'),
    )
    fields = {key: data[key] for key in ('title', 'status', 'priority', 'due_date', 'tags') if data.get(key)}
    task.apply_changes(fields)

    db.session.add(task)
    commit()
    logger.info('task_created id=%s', task.id)
    _notify_assignment(task)
    return task.to_dict()


def update_task(task_id, payload):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    data = require_payload(payload)

    task.apply_changes(data)
    if 'user_id' in data or 'category_id' in data:
        _check_references(data.get('user_id'), data.get('category_id'))
    previous_user_id = task.user_id
    if 'user_id' in data:
        task.user_id = data['user_id']
    if 'category_id' in data:
        task.category_id = data['category_id']

    commit()
    logger.info('task_updated id=%s', task.id)
    if task.user_id and task.user_id != previous_user_id:
        _notify_assignment(task)
    return task.to_dict()


def delete_task(task_id):
    task = get_or_404(Task, task_id, TASK_NOT_FOUND)
    db.session.delete(task)
    commit()
    logger.info('task_deleted id=%s', task_id)
    return {'message': 'Task deletada com sucesso'}


def _int_param(args, name):
    value = args.get(name, '')
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f'Parâmetro {name} inválido')


def search_tasks(args):
    query = db.select(Task)
    text = args.get('q', '')
    if text:
        query = query.where(db.or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
    status = args.get('status', '')
    if status:
        query = query.where(Task.status == status)
    priority = _int_param(args, 'priority')
    if priority is not None:
        query = query.where(Task.priority == priority)
    user_id = _int_param(args, 'user_id')
    if user_id is not None:
        query = query.where(Task.user_id == user_id)

    tasks = db.session.execute(query.order_by(Task.id)).scalars().all()
    return [task.to_dict() for task in tasks]


def task_stats():
    return report_service.task_stats()
