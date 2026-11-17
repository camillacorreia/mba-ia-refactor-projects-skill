from controllers.common import get_or_404, require_payload
from database import commit, db
from models.category import DEFAULT_COLOR, Category
from models.task import Task
from utils.errors import ValidationError

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def list_categories():
    rows = db.session.execute(
        db.select(Task.category_id, db.func.count(Task.id)).group_by(Task.category_id)
    ).all()
    counts = dict(rows)
    categories = db.session.execute(db.select(Category).order_by(Category.id)).scalars().all()
    return [category.to_dict(task_count=counts.get(category.id, 0)) for category in categories]


def create_category(payload):
    data = require_payload(payload)
    if not data.get('name'):
        raise ValidationError('Nome é obrigatório')

    category = Category(description='', color=DEFAULT_COLOR)
    category.apply_changes(data)
    db.session.add(category)
    commit()
    return category.to_dict()


def update_category(category_id, payload):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    if payload is None or not isinstance(payload, dict):
        raise ValidationError('Dados inválidos')
    category.apply_changes(payload)
    commit()
    return category.to_dict()


def delete_category(category_id):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    # Tasks da categoria ficam sem categoria, na mesma transação, em vez de apontar para um id inexistente.
    db.session.execute(db.update(Task).where(Task.category_id == category_id).values(category_id=None))
    db.session.delete(category)
    commit()
    return {'message': 'Categoria deletada'}
