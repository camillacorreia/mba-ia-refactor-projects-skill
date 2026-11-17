import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import utc_now

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER
MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
_MODERN_HASH_PREFIXES = ('scrypt:', 'pbkdf2:')


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_password(password):
    return isinstance(password, str) and len(password) >= MIN_PASSWORD_LENGTH


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
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
        if self.password.startswith(_MODERN_HASH_PREFIXES):
            return check_password_hash(self.password, raw_password)
        legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
        if hmac.compare_digest(self.password, legacy_hash):
            self.set_password(raw_password)
            return True
        return False

    def is_admin(self):
        return self.role == ROLE_ADMIN
