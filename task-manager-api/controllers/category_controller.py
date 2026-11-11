from controllers.common import require_object
from models.category import DEFAULT_COLOR, Category, validate_category_name, validate_color
from models.task import Task
from utils.errors import NotFoundError, ValidationError


def _get_category(category_id):
    category = Category.find(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    task_counts = Task.count_by(Task.category_id)
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = task_counts.get(category.id, 0)
        result.append(data)
    return result, 200


def create_category(payload):
    data = require_object(payload)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=validate_category_name(data['name']),
        description=data.get('description', ''),
        color=validate_color(data.get('color', DEFAULT_COLOR)),
    )
    category.save()
    return category.to_dict(), 201


def update_category(category_id, payload):
    category = _get_category(category_id)
    data = require_object(payload)

    if 'name' in data:
        category.name = validate_category_name(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = validate_color(data['color'])

    category.save()
    return category.to_dict(), 200


def delete_category(category_id):
    _get_category(category_id).delete()
    return {'message': 'Categoria deletada'}, 200
