from flask import Blueprint, jsonify, request

from src.controllers import produto_controller

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    body, status = produto_controller.listar()
    return jsonify(body), status


@bp.get("/produtos/busca")
def buscar_produtos():
    body, status = produto_controller.buscar(request.args)
    return jsonify(body), status


@bp.get("/produtos/<int:id>")
def buscar_produto(id):
    body, status = produto_controller.buscar_por_id(id)
    return jsonify(body), status


@bp.post("/produtos")
def criar_produto():
    body, status = produto_controller.criar(request.get_json(silent=True))
    return jsonify(body), status


@bp.put("/produtos/<int:id>")
def atualizar_produto(id):
    body, status = produto_controller.atualizar(id, request.get_json(silent=True))
    return jsonify(body), status


@bp.delete("/produtos/<int:id>")
def deletar_produto(id):
    body, status = produto_controller.deletar(id)
    return jsonify(body), status
