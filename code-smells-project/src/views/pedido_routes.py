from flask import Blueprint, jsonify, request

from src.controllers import pedido_controller

bp = Blueprint("pedidos", __name__)


@bp.post("/pedidos")
def criar_pedido():
    body, status = pedido_controller.criar(request.get_json(silent=True))
    return jsonify(body), status


@bp.get("/pedidos")
def listar_todos_pedidos():
    body, status = pedido_controller.listar_todos()
    return jsonify(body), status


@bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    body, status = pedido_controller.listar_por_usuario(usuario_id)
    return jsonify(body), status


@bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    body, status = pedido_controller.atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify(body), status
