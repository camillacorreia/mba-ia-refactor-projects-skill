"""Usuário: serialização sem senha, cadastro com hash e autenticação."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import ValidationError

TIPO_PADRAO = "cliente"
_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def to_dict(row, incluir_criado_em=True):
    data = {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    if incluir_criado_em:
        data["criado_em"] = row["criado_em"]
    return data


def validar_cadastro(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not all(isinstance(v, str) for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha devem ser texto")
    return {"nome": nome, "email": email, "senha": senha}


def listar(db):
    return [to_dict(row) for row in db.execute("SELECT * FROM usuarios ORDER BY id")]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def criar(db, nome, email, senha, tipo=TIPO_PADRAO):
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def _senha_confere(db, row, senha):
    armazenada = row["senha"] or ""
    if armazenada.startswith(_HASH_PREFIXES):
        return check_password_hash(armazenada, senha)
    # Senha legada em texto puro (bancos criados antes da refatoração): confere e migra para hash.
    if hmac.compare_digest(armazenada.encode(), senha.encode()):
        with db:
            db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(senha), row["id"]))
        return True
    return False


def autenticar(db, email, senha):
    """Devolve o usuário (sem senha e sem criado_em, como o login original) ou None."""
    rows = db.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    for row in rows:
        if _senha_confere(db, row, senha):
            return to_dict(row, incluir_criado_em=False)
    return None
