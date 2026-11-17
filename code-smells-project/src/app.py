"""Composition root: config, banco, serviços, blueprints e error handlers."""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Settings
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.services.pedido_service import PedidoService
from src.views import pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes


def create_app(settings=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = settings or Settings()

    if settings.secret_key_generated:
        logging.getLogger(__name__).warning("SECRET_KEY não definida; usando chave aleatória (tokens expiram a cada boot)")

    app = Flask(__name__)
    app.config.update(settings.to_flask_config())
    origins = settings.cors_origins
    CORS(app, origins="*" if origins == "*" else [o.strip() for o in origins.split(",") if o.strip()])

    database.init_app(app)
    app.extensions["pedido_service"] = PedidoService(notifier=NotificationService())

    for module in (produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes):
        app.register_blueprint(module.bp)
    register_error_handlers(app)
    return app
