from src.services import relatorio_service


def vendas(db):
    return {"dados": relatorio_service.relatorio_vendas(db), "sucesso": True}, 200
