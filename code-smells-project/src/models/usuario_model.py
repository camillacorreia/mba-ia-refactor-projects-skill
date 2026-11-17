"""Usuários: acesso a dados, hash de senha e serialização sem campos sensíveis."""
from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import ValidationError

TIPO_PADRAO = "cliente"
TIPO_ADMIN = "admin"
HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def to_session_dict(row):
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def validar_cadastro(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(isinstance(v, str) and v for v in (nome, email, senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    return {"nome": nome, "email": email, "senha": senha}


def listar(db):
    return [to_dict(row) for row in db.execute("SELECT * FROM usuarios ORDER BY id")]


def buscar_por_id(db, usuario_id):
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def existe(db, usuario_id):
    return db.execute("SELECT 1 FROM usuarios WHERE id = ?", (usuario_id,)).fetchone() is not None


def criar(db, nome, email, senha, tipo=TIPO_PADRAO, commit=True):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    if commit:
        db.commit()
    return cursor.lastrowid


def autenticar(db, email, senha):
    rows = db.execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()
    for row in rows:
        if row["senha"] and check_password_hash(row["senha"], senha):
            return to_session_dict(row)
    return None


def migrar_senhas_legadas(db):
    """Regrava com hash as senhas que ainda estão em texto puro (bancos criados antes da refatoração)."""
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    legadas = [r for r in rows if r["senha"] and not r["senha"].startswith(HASH_PREFIXES)]
    with db:
        for row in legadas:
            db.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (generate_password_hash(row["senha"]), row["id"]),
            )
    return len(legadas)
