from database import db
from utils.errors import ValidationError
from utils.helpers import utc_now

DEFAULT_COLOR = '#000000'
COLOR_LENGTH = 7


def is_valid_color(color):
    return isinstance(color, str) and len(color) == COLOR_LENGTH and color.startswith('#')


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(COLOR_LENGTH), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self, task_count=None):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }
        if task_count is not None:
            data['task_count'] = task_count
        return data

    def apply_changes(self, data):
        if 'name' in data:
            if not data['name'] or not isinstance(data['name'], str):
                raise ValidationError('Nome é obrigatório')
            self.name = data['name']
        if 'description' in data:
            self.description = data['description']
        if 'color' in data:
            if not is_valid_color(data['color']):
                raise ValidationError('Cor inválida. Use o formato #RRGGBB')
            self.color = data['color']
