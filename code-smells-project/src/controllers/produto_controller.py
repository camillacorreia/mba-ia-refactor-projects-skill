import logging

from src.database import get_db
from src.errors import ConflictError, NotFoundError, ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _float_ou_none(valor, campo):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(campo + " deve ser numérico")


def listar():
    produtos = produto_model.listar(get_db())
    logger.info("Listando %d produtos", len(produtos))
    return {"dados": produtos, "sucesso": True}, 200


def buscar_por_id(produto_id):
    produto = produto_model.buscar_por_id(get_db(), produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", sucesso=False)
    return {"dados": produto, "sucesso": True}, 200


def buscar(args):
    resultados = produto_model.buscar(
        get_db(),
        termo=args.get("q", ""),
        categoria=args.get("categoria"),
        preco_min=_float_ou_none(args.get("preco_min"), "preco_min"),
        preco_max=_float_ou_none(args.get("preco_max"), "preco_max"),
    )
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200


def criar(dados):
    campos = produto_model.validar(dados)
    produto_id = produto_model.criar(get_db(), campos)
    logger.info("Produto criado id=%s", produto_id)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(produto_id, dados):
    db = get_db()
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    campos = produto_model.validar(dados)
    produto_model.atualizar(db, produto_id, campos)
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(produto_id):
    db = get_db()
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    if produto_model.possui_pedidos(db, produto_id):
        raise ConflictError("Produto possui pedidos e não pode ser removido", sucesso=False)
    produto_model.deletar(db, produto_id)
    logger.info("Produto deletado id=%s", produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200
