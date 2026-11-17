from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller
from src.database import get_db
from src.middlewares.auth import require_admin, require_admin_or_self

bp = Blueprint("usuarios", __name__)


@bp.get("/usuarios")
@require_admin
def listar_usuarios():
    body, status = usuario_controller.listar(get_db())
    return jsonify(body), status


@bp.get("/usuarios/<int:id>")
@require_admin_or_self("id")
def buscar_usuario(id):
    body, status = usuario_controller.buscar(get_db(), id)
    return jsonify(body), status


@bp.post("/usuarios")
def criar_usuario():
    body, status = usuario_controller.criar(get_db(), request.get_json(silent=True))
    return jsonify(body), status


@bp.post("/login")
def login():
    body, status = usuario_controller.login(get_db(), request.get_json(silent=True))
    return jsonify(body), status
