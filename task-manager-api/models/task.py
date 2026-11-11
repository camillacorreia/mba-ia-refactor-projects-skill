from datetime import datetime

from database import db
from utils.errors import ValidationError
from utils.helpers import utcnow

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)  # tasks fechadas nunca ficam atrasadas
DEFAULT_STATUS = STATUS_PENDING

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como alta nos relatórios
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
DUE_DATE_FORMAT = '%Y-%m-%d'
TAGS_SEPARATOR = ','


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    def is_overdue(self, now=None):
        if not self.due_date or self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utcnow())

    def to_dict(self, include_overdue=False, include_relation_names=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(TAGS_SEPARATOR) if self.tags else [],
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if include_relation_names:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Formato reduzido usado em GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': str(self.created_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'overdue': self.is_overdue(),
        }

    # Consultas

    @classmethod
    def find(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls, with_relations=False):
        query = db.select(cls).order_by(cls.id)
        if with_relations:
            query = query.options(db.joinedload(cls.user), db.joinedload(cls.category))
        return db.session.execute(query).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.execute(db.select(cls).where(cls.user_id == user_id).order_by(cls.id)).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = db.select(cls).order_by(cls.id)
        if text:
            query = query.where(db.or_(cls.title.like(f'%{text}%'), cls.description.like(f'%{text}%')))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    @classmethod
    def count_by(cls, column):
        rows = db.session.execute(db.select(column, db.func.count(cls.id)).group_by(column)).all()
        return {key: total for key, total in rows}

    @classmethod
    def overdue_query(cls, now):
        return db.select(cls).where(
            cls.due_date.is_not(None),
            cls.due_date < now,
            cls.status.not_in(CLOSED_STATUSES),
        )

    @classmethod
    def list_overdue(cls, now):
        return db.session.execute(cls.overdue_query(now).order_by(cls.id)).scalars().all()

    @classmethod
    def count_overdue(cls, now):
        return db.session.execute(db.select(db.func.count()).select_from(cls.overdue_query(now).subquery())).scalar_one()

    # Escrita

    @classmethod
    def create(cls, **fields):
        task = cls(**fields)
        db.session.add(task)
        db.session.commit()
        return task

    def update(self, **fields):
        for name, value in fields.items():
            setattr(self, name, value)
        self.updated_at = utcnow()
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


# Validação de campos (compartilhada por create e update)

def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def parse_due_date(value, error_message):
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message) from None


def tags_to_column(tags):
    """Aceita lista de strings ou string já separada por vírgula."""
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return TAGS_SEPARATOR.join(tags)
    return tags
