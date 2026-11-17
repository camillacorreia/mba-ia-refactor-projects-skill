from flask import Blueprint, jsonify

from src.controllers import relatorio_controller
from src.database import get_db
from src.middlewares.auth import require_admin

bp = Blueprint("relatorios", __name__)


@bp.get("/relatorios/vendas")
@require_admin
def relatorio_vendas():
    body, status = relatorio_controller.vendas(get_db())
    return jsonify(body), status
