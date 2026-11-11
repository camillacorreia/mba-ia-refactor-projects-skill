"""Configuração lida do ambiente, com defaults seguros para desenvolvimento."""
import logging
import os
import secrets

API_VERSION = "1.0.0"

logger = logging.getLogger(__name__)


def _env_bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self):
        self.env = os.getenv("APP_ENV", "desenvolvimento")
        self.debug = _env_bool("DEBUG", False)
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "5000"))
        self.database_path = os.getenv("DATABASE_PATH", "loja.db")
        self.cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
        # Vazio desliga as rotas administrativas (respondem 403).
        self.admin_token = os.getenv("ADMIN_TOKEN", "")

        secret_key = os.getenv("SECRET_KEY", "")
        if not secret_key:
            if self.env == "producao":
                raise RuntimeError("SECRET_KEY é obrigatória com APP_ENV=producao")
            secret_key = secrets.token_hex(32)
            self.secret_key_generated = True
        else:
            self.secret_key_generated = False
        self.secret_key = secret_key
