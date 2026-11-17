from flask import Blueprint, jsonify, request

from src.controllers import produto_controller
from src.database import get_db

bp = Blueprint("produtos", __name__)


@bp.get("/produtos")
def listar_produtos():
    body, status = produto_controller.listar(get_db())
    return jsonify(body), status


@bp.get("/produtos/busca")
def buscar_produtos():
    body, status = produto_controller.pesquisar(get_db(), request.args)
    return jsonify(body), status


@bp.get("/produtos/<int:id>")
def buscar_produto(id):
    body, status = produto_controller.buscar(get_db(), id)
    return jsonify(body), status


@bp.post("/produtos")
def criar_produto():
    body, status = produto_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify(body), status


@bp.put("/produtos/<int:id>")
def atualizar_produto(id):
    body, status = produto_controller.atualizar(get_db(), id, request.get_json(silent=True))
    return jsonify(body), status


@bp.delete("/produtos/<int:id>")
def deletar_produto(id):
    body, status = produto_controller.deletar(get_db(), id)
    return jsonify(body), status
