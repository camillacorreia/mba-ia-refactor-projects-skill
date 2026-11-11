from src.database import get_db
from src.services import relatorio_service


def vendas():
    return {"dados": relatorio_service.relatorio_vendas(get_db()), "sucesso": True}, 200
