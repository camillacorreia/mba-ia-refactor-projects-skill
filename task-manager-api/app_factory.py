"""Composition root: monta a app a partir da configuração injetada."""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  registra os models antes do create_all
from config.settings import Settings
from database import db, enable_sqlite_foreign_keys
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def create_app(settings=None, notification_service=None):
    settings = settings or Settings()
    logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    if settings.secret_key_generated:
        logger.warning('SECRET_KEY não definida: usando chave aleatória (tokens expiram a cada restart)')
    if not settings.admin_token:
        logger.warning('ADMIN_TOKEN não definido: rotas administrativas só aceitam Bearer token de admin')

    app = Flask(__name__)
    app.config.update(settings.to_flask_config())

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)
    app.extensions['notification_service'] = notification_service or NotificationService.from_settings(settings)

    for blueprint in (system_bp, task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)

    with app.app_context():
        enable_sqlite_foreign_keys(db.engine)
        db.create_all()

    return app
