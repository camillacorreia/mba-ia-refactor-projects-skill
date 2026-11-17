"""Configuração lida do ambiente, com defaults seguros para desenvolvimento."""
import os
import secrets

API_VERSION = "1.0.0"


def _bool_env(name, default="false"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self):
        self.environment = os.getenv("APP_ENV", "desenvolvimento")
        self.debug = _bool_env("DEBUG")
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "5000"))
        self.database_path = os.getenv("DATABASE_PATH", "loja.db")
        self.cors_origins = os.getenv("CORS_ORIGINS", "*")
        self.admin_token = os.getenv("ADMIN_TOKEN", "")
        self.token_max_age_seconds = int(os.getenv("TOKEN_MAX_AGE_SECONDS", "3600"))

        self.secret_key_generated = not os.getenv("SECRET_KEY")
        self.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    def to_flask_config(self):
        return {
            "SECRET_KEY": self.secret_key,
            "DEBUG": self.debug,
            "DATABASE_PATH": self.database_path,
            "ADMIN_TOKEN": self.admin_token,
            "TOKEN_MAX_AGE_SECONDS": self.token_max_age_seconds,
            "APP_ENV": self.environment,
            "API_VERSION": API_VERSION,
        }
