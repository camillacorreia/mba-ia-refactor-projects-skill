import logging

from src.models import sistema_model

logger = logging.getLogger(__name__)


def index(versao):
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": versao,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health(db, versao, ambiente):
    try:
        counts = sistema_model.contagens(db)
    except Exception:
        logger.exception("health_check_falhou")
        return {"status": "erro", "detalhes": "Banco de dados indisponível"}, 500
    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": versao,
        "ambiente": ambiente,
    }, 200


def resetar_banco(db):
    sistema_model.resetar(db)
    logger.warning("banco_de_dados_resetado")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200
