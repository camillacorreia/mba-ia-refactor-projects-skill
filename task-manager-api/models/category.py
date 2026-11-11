import re

from database import db
from utils.errors import ValidationError
from utils.helpers import utcnow

DEFAULT_COLOR = '#000000'
COLOR_PATTERN = re.compile(r'^#[0-9a-fA-F]{6}$')


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Sem cascade de delete: ao apagar a categoria, o SQLAlchemy carrega as tasks
    # e grava category_id = NULL nelas na mesma transação. As tasks continuam existindo.
    tasks = db.relationship('Task', back_populates='category')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def find(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def validate_category_name(name):
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return name


def validate_color(color):
    if color is not None and (not isinstance(color, str) or not COLOR_PATTERN.match(color)):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return color
