from flask import Blueprint, jsonify

from src.controllers import sistema_controller
from src.middlewares.auth import require_admin_token

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    body, status = sistema_controller.index()
    return jsonify(body), status


@bp.get("/health")
def health_check():
    body, status = sistema_controller.health()
    return jsonify(body), status


@bp.post("/admin/reset-db")
@require_admin_token
def reset_database():
    body, status = sistema_controller.reset_database()
    return jsonify(body), status

# /admin/query (SQL arbitrário) foi removida de propósito: não há uso legítimo para ela numa API.
