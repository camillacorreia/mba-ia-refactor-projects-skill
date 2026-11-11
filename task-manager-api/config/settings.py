"""Configuração lida do ambiente (e de um .env opcional), com defaults seguros para desenvolvimento."""
import os
import secrets

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'  # o Flask-SQLAlchemy resolve em instance/tasks.db
DEFAULT_PORT = 5000


def _as_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class Settings:
    def __init__(self, env):
        self.env = env.get('ENV', 'development')
        self.debug = _as_bool(env.get('DEBUG', 'false'))
        self.host = env.get('HOST', '127.0.0.1')
        self.port = int(env.get('PORT', DEFAULT_PORT))
        self.database_url = env.get('DATABASE_URL', DEFAULT_DATABASE_URL)
        self.cors_origins = [o.strip() for o in env.get('CORS_ORIGINS', '*').split(',') if o.strip()]
        self.log_level = env.get('LOG_LEVEL', 'INFO').upper()

        self.secret_key = env.get('SECRET_KEY')
        self.secret_key_generated = not self.secret_key
        if self.secret_key_generated:
            if self.env == 'production':
                raise RuntimeError('SECRET_KEY é obrigatória quando ENV=production')
            self.secret_key = secrets.token_hex(32)

    @classmethod
    def from_env(cls):
        load_dotenv()  # não sobrescreve variáveis já definidas no ambiente
        return cls(os.environ)
