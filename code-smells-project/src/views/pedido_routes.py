from flask import Blueprint, current_app, jsonify, request

from src.controllers import pedido_controller
from src.database import get_db
from src.middlewares.auth import require_admin, require_admin_or_self

bp = Blueprint("pedidos", __name__)


def _service():
    return current_app.extensions["pedido_service"]


@bp.post("/pedidos")
def criar_pedido():
    body, status = pedido_controller.criar(get_db(), _service(), request.get_json(silent=True))
    return jsonify(body), status


@bp.get("/pedidos")
@require_admin
def listar_todos_pedidos():
    body, status = pedido_controller.listar_todos(get_db())
    return jsonify(body), status


@bp.get("/pedidos/usuario/<int:usuario_id>")
@require_admin_or_self("usuario_id")
def listar_pedidos_usuario(usuario_id):
    body, status = pedido_controller.listar_do_usuario(get_db(), usuario_id)
    return jsonify(body), status


@bp.put("/pedidos/<int:pedido_id>/status")
@require_admin
def atualizar_status_pedido(pedido_id):
    body, status = pedido_controller.atualizar_status(get_db(), _service(), pedido_id, request.get_json(silent=True))
    return jsonify(body), status
