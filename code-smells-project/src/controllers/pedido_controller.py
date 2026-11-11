from flask import current_app

from src.database import get_db
from src.models import pedido_model


def _service():
    return current_app.extensions["pedido_service"]


def criar(dados):
    usuario_id, itens = pedido_model.validar_criacao(dados)
    resultado = _service().criar(get_db(), usuario_id, itens)
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_todos():
    return {"dados": pedido_model.listar(get_db()), "sucesso": True}, 200


def listar_por_usuario(usuario_id):
    return {"dados": pedido_model.listar(get_db(), usuario_id=usuario_id), "sucesso": True}, 200


def atualizar_status(pedido_id, dados):
    novo_status = pedido_model.validar_status(dados)
    _service().atualizar_status(get_db(), pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
