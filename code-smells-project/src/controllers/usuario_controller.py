import logging

from src.errors import NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model
from src.services import auth_service

logger = logging.getLogger(__name__)


def listar(db):
    return {"dados": usuario_model.listar(db), "sucesso": True}, 200


def buscar(db, usuario_id):
    usuario = usuario_model.buscar_por_id(db, usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return {"dados": usuario, "sucesso": True}, 200


def criar(db, payload):
    dados = usuario_model.validar_cadastro(payload)
    usuario_id = usuario_model.criar(db, dados["nome"], dados["email"], dados["senha"])
    logger.info("usuario_criado id=%s", usuario_id)
    return {"dados": {"id": usuario_id}, "sucesso": True}, 201


def login(db, payload):
    payload = payload or {}
    email = payload.get("email", "")
    senha = payload.get("senha", "")
    if not email or not senha or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(db, email, senha)
    if not usuario:
        logger.info("login_falhou")
        raise UnauthorizedError("Email ou senha inválidos", include_sucesso=True)

    logger.info("login_ok usuario_id=%s", usuario["id"])
    return {
        "dados": usuario,
        "sucesso": True,
        "mensagem": "Login OK",
        "token": auth_service.emitir_token(usuario),
    }, 200
