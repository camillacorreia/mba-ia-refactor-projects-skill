from datetime import datetime

from database import db
from utils.errors import ValidationError
from utils.helpers import utc_now

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2  # prioridades 1 e 2 contam como "alta" nos relatórios
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


def validate_title(title):
    if not title:
        raise ValidationError('Título é obrigatório')
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
    is_int = isinstance(priority, int) and not isinstance(priority, bool)
    if not is_int or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
        raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
    return priority


def parse_due_date(value):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')


def serialize_tags(tags):
    if isinstance(tags, list):
        return TAG_SEPARATOR.join(tags)
    return tags


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    @staticmethod
    def overdue_filter(now=None):
        """Mesma regra de is_overdue(), em SQL."""
        now = now or utc_now()
        return db.and_(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_(CLOSED_STATUSES),
        )

    def is_overdue(self, now=None):
        if not self.due_date:
            return False
        now = now or utc_now()
        return self.due_date < now and self.status not in CLOSED_STATUSES

    def is_high_priority(self):
        return self.priority <= HIGH_PRIORITY_THRESHOLD

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
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if include_relation_names:
            data['user_name'] = self.user.name if self.user else None
            data['category_name'] = self.category.name if self.category else None
        return data

    def to_summary_dict(self):
        """Formato usado em /users/<id>/tasks."""
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

    def apply_changes(self, data):
        """Valida e aplica campos simples. user_id/category_id são checados pelo controller."""
        if 'title' in data:
            self.title = validate_title(data['title'])
        if 'description' in data:
            self.description = data['description']
        if 'status' in data:
            self.status = validate_status(data['status'])
        if 'priority' in data:
            self.priority = validate_priority(data['priority'])
        if 'due_date' in data:
            self.due_date = parse_due_date(data['due_date']) if data['due_date'] else None
        if 'tags' in data:
            self.tags = serialize_tags(data['tags'])
