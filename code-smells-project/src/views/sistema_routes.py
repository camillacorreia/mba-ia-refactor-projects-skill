from flask import Blueprint, current_app, jsonify

from src.controllers import sistema_controller
from src.database import get_db
from src.middlewares.auth import require_admin

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    body, status = sistema_controller.index(current_app.config["API_VERSION"])
    return jsonify(body), status


@bp.get("/health")
def health_check():
    body, status = sistema_controller.health(
        get_db(), current_app.config["API_VERSION"], current_app.config["APP_ENV"]
    )
    return jsonify(body), status


@bp.post("/admin/reset-db")
@require_admin
def reset_database():
    body, status = sistema_controller.resetar_banco(get_db())
    return jsonify(body), status
