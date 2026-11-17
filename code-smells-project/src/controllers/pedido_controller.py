from src.models import pedido_model


def criar(db, service, payload):
    resultado = service.criar(db, payload)
    return {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201


def listar_todos(db):
    return {"dados": pedido_model.listar(db), "sucesso": True}, 200


def listar_do_usuario(db, usuario_id):
    return {"dados": pedido_model.listar(db, usuario_id=usuario_id), "sucesso": True}, 200


def atualizar_status(db, service, pedido_id, payload):
    service.atualizar_status(db, pedido_id, payload)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
