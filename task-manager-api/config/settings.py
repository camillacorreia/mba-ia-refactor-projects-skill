"""Configuração da aplicação lida do ambiente (com .env opcional)."""
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

DEFAULT_TOKEN_MAX_AGE_SECONDS = 8 * 60 * 60


def _as_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self, environ=None):
        env = os.environ if environ is None else environ

        self.env = env.get("ENV", "development")
        self.secret_key = env.get("SECRET_KEY") or ""
        if not self.secret_key:
            if self.env == "production":
                raise RuntimeError("SECRET_KEY é obrigatória com ENV=production")
            self.secret_key = secrets.token_hex(32)
            self.secret_key_generated = True
        else:
            self.secret_key_generated = False

        self.debug = _as_bool(env.get("DEBUG"), default=False)
        self.host = env.get("HOST", "127.0.0.1")
        self.port = int(env.get("PORT", "5000"))
        self.database_url = env.get("DATABASE_URL", "sqlite:///tasks.db")
        raw_origins = env.get("CORS_ORIGINS", "*").strip()
        self.cors_origins = "*" if raw_origins == "*" else [o.strip() for o in raw_origins.split(",") if o.strip()]

        self.admin_token = env.get("ADMIN_TOKEN", "")
        self.token_max_age_seconds = int(env.get("TOKEN_MAX_AGE_SECONDS", DEFAULT_TOKEN_MAX_AGE_SECONDS))

        self.smtp_host = env.get("SMTP_HOST", "")
        self.smtp_port = int(env.get("SMTP_PORT", "587"))
        self.smtp_user = env.get("SMTP_USER", "")
        self.smtp_password = env.get("SMTP_PASSWORD", "")

    def to_flask_config(self):
        return {
            "SECRET_KEY": self.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "ADMIN_TOKEN": self.admin_token,
            "TOKEN_MAX_AGE_SECONDS": self.token_max_age_seconds,
        }


settings = Settings()
