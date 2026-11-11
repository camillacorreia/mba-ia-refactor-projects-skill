import logging

from src.database import get_db
from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar():
    return {"dados": usuario_model.listar(get_db()), "sucesso": True}, 200


def buscar_por_id(usuario_id):
    usuario = usuario_model.buscar_por_id(get_db(), usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return {"dados": usuario, "sucesso": True}, 200


def criar(dados):
    campos = usuario_model.validar_cadastro(dados)
    usuario_id = usuario_model.criar(get_db(), campos["nome"], campos["email"], campos["senha"])
    logger.info("Usuario criado id=%s", usuario_id)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")
    usuario = usuario_model.autenticar(get_db(), email, senha)
    if not usuario:
        logger.info("Login falhou")
        raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
    logger.info("Login ok usuario_id=%s", usuario["id"])
    return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
