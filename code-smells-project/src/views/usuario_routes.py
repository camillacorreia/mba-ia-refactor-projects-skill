from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
def listar_usuarios():
    body, status = usuario_controller.listar()
    return jsonify(body), status


@bp.get("/usuarios/<int:id>")
def buscar_usuario(id):
    body, status = usuario_controller.buscar_por_id(id)
    return jsonify(body), status


@bp.post("/usuarios")
def criar_usuario():
    body, status = usuario_controller.criar(request.get_json(silent=True))
    return jsonify(body), status


@bp.post("/login")
def login():
    body, status = usuario_controller.login(request.get_json(silent=True))
    return jsonify(body), status
