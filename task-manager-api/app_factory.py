"""Composition root: monta a aplicação a partir da configuração."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from database import init_db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def create_app(settings=None):
    settings = settings or Settings.from_env()
    logging.basicConfig(level=settings.log_level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
    )
    if settings.secret_key_generated:
        app.logger.warning('SECRET_KEY não definida; usando chave aleatória gerada no boot')

    CORS(app, origins=settings.cors_origins)
    init_db(app)

    for blueprint in (system_bp, task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    return app
