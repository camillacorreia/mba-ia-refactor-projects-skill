from src.errors import NotFoundError, ValidationError
from src.models import produto_model


def listar(db):
    return {"dados": produto_model.listar(db), "sucesso": True}, 200


def buscar(db, produto_id):
    produto = produto_model.buscar_por_id(db, produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", include_sucesso=True)
    return {"dados": produto, "sucesso": True}, 200


def _float_ou_none(valor, campo):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(campo + " deve ser numérico") from None


def pesquisar(db, args):
    resultados = produto_model.buscar(
        db,
        termo=args.get("q", ""),
        categoria=args.get("categoria"),
        preco_min=_float_ou_none(args.get("preco_min"), "preco_min"),
        preco_max=_float_ou_none(args.get("preco_max"), "preco_max"),
    )
    return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200


def criar(db, payload):
    dados = produto_model.validar(payload)
    produto_id = produto_model.criar(db, dados)
    return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201


def atualizar(db, produto_id, payload):
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    dados = produto_model.validar(payload)
    produto_model.atualizar(db, produto_id, dados)
    return {"sucesso": True, "mensagem": "Produto atualizado"}, 200


def deletar(db, produto_id):
    if not produto_model.buscar_por_id(db, produto_id):
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(db, produto_id)
    return {"sucesso": True, "mensagem": "Produto deletado"}, 200
