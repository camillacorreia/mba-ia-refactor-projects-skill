"""Composition root: config, logging, banco, serviços, rotas e error handlers."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.services.pedido_service import PedidoService
from src.views import pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes

logger = logging.getLogger(__name__)


def create_app(settings=None):
    settings = settings or Settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if settings.secret_key_generated:
        logger.warning("SECRET_KEY não definida: usando chave aleatória gerada neste boot")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        DATABASE_PATH=settings.database_path,
        ADMIN_TOKEN=settings.admin_token,
        APP_ENV=settings.env,
    )
    CORS(app, origins=settings.cors_origins)

    database.init_app(app)
    app.extensions["pedido_service"] = PedidoService(notifier=NotificationService())

    for blueprint in (produto_routes.bp, usuario_routes.bp, pedido_routes.bp, relatorio_routes.bp, sistema_routes.bp):
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    return app
