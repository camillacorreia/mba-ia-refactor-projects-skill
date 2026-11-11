import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.errors import ValidationError
from utils.helpers import utcnow

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
MODERN_HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Apagar o usuário apaga as tasks dele na mesma transação.
    tasks = db.relationship('Task', back_populates='user', cascade='all, delete')

    def to_dict(self):
        """Serialização pública: nunca inclui a senha nem o hash."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Confere a senha; hash MD5 legado é aceito uma vez e regravado no formato novo."""
        if self.password.startswith(MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True
        return False

    # Consultas

    @classmethod
    def find(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).where(cls.email == email)).scalar_one_or_none()

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def count(cls):
        return db.session.execute(db.select(db.func.count(cls.id))).scalar_one()

    # Escrita

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def validate_email(email):
    if not is_valid_email(email):
        raise ValidationError('Email inválido')
    return email


def validate_password(password, too_short_message):
    if not isinstance(password, str):
        raise ValidationError('Senha inválida')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return password


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def validate_name(name):
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return name
