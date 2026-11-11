import logging

from controllers.common import parse_int_param, require_object
from models.category import Category
from models.task import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    Task,
    parse_due_date,
    tags_to_column,
    validate_priority,
    validate_status,
    validate_title,
)
from models.user import User
from utils.errors import NotFoundError, ValidationError
from utils.helpers import calculate_percentage, utcnow

logger = logging.getLogger(__name__)

CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


def _get_task(task_id):
    task = Task.find(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_user_exists(user_id):
    if user_id and not User.find(user_id):
        raise NotFoundError('Usuário não encontrado')
    return user_id


def _ensure_category_exists(category_id):
    if category_id and not Category.find(category_id):
        raise NotFoundError('Categoria não encontrada')
    return category_id


def list_tasks():
    tasks = Task.list_all(with_relations=True)
    return [task.to_dict(include_overdue=True, include_relation_names=True) for task in tasks], 200


def get_task(task_id):
    return _get_task(task_id).to_dict(include_overdue=True), 200


def create_task(payload):
    data = require_object(payload)
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    # A ordem das checagens segue o código original, para manter o mesmo status quando há mais de um erro.
    fields = {
        'title': validate_title(data['title']),
        'description': data.get('description', ''),
        'status': validate_status(data.get('status', DEFAULT_STATUS)),
        'priority': validate_priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _ensure_user_exists(data.get('user_id')),
        'category_id': _ensure_category_exists(data.get('category_id')),
    }
    if data.get('due_date'):
        fields['due_date'] = parse_due_date(data['due_date'], CREATE_DATE_ERROR)
    if data.get('tags'):
        fields['tags'] = tags_to_column(data['tags'])

    task = Task.create(**fields)
    logger.info('Task criada id=%s', task.id)
    return task.to_dict(), 201


def update_task(task_id, payload):
    task = _get_task(task_id)
    data = require_object(payload)

    changes = {}
    if 'title' in data:
        changes['title'] = validate_title(data['title'])
    if 'description' in data:
        changes['description'] = data['description']
    if 'status' in data:
        changes['status'] = validate_status(data['status'])
    if 'priority' in data:
        changes['priority'] = validate_priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = _ensure_user_exists(data['user_id'])
    if 'category_id' in data:
        changes['category_id'] = _ensure_category_exists(data['category_id'])
    if 'due_date' in data:
        changes['due_date'] = parse_due_date(data['due_date'], UPDATE_DATE_ERROR) if data['due_date'] else None
    if 'tags' in data:
        changes['tags'] = tags_to_column(data['tags'])

    task.update(**changes)
    logger.info('Task atualizada id=%s', task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    _get_task(task_id).delete()
    logger.info('Task deletada id=%s', task_id)
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(args):
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')
    tasks = Task.search(
        text=args.get('q', ''),
        status=args.get('status', ''),
        priority=parse_int_param(priority, 'priority') if priority else None,
        user_id=parse_int_param(user_id, 'user_id') if user_id else None,
    )
    return [task.to_dict() for task in tasks], 200


def task_stats():
    total = Task.count()
    by_status = Task.count_by(Task.status)
    done = by_status.get('done', 0)
    return {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': Task.count_overdue(utcnow()),
        'completion_rate': calculate_percentage(done, total),
    }, 200
