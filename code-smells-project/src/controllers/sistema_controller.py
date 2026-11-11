import logging

from flask import current_app

from src.config.settings import API_VERSION
from src.database import get_db
from src.models import sistema_model

logger = logging.getLogger(__name__)


def index():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": API_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }, 200


def health():
    try:
        counts = sistema_model.contar_registros(get_db())
    except Exception:
        logger.exception("Health check falhou")
        return {"status": "erro", "detalhes": "Banco de dados indisponível"}, 500
    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": API_VERSION,
        "ambiente": current_app.config["APP_ENV"],
    }, 200


def reset_database():
    sistema_model.apagar_tudo(get_db())
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}, 200
