"""Produto: regras de validação, serialização e acesso à tabela produtos."""
from src.errors import ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN_CHARS = 2
NOME_MAX_CHARS = 200


def to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validar(dados):
    """Valida o payload de criação e de atualização (mesmas regras) e devolve os campos normalizados."""
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN_CHARS:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_CHARS:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def listar(db):
    return [to_dict(row) for row in db.execute("SELECT * FROM produtos ORDER BY id")]


def buscar_por_id(db, produto_id):
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return to_dict(row) if row else None


def buscar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    condicoes, params = ["1=1"], []
    if termo:
        condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if preco_min:
        condicoes.append("preco >= ?")
        params.append(preco_min)
    if preco_max:
        condicoes.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(condicoes) + " ORDER BY id"
    return [to_dict(row) for row in db.execute(sql, params)]


def criar(db, campos):
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (campos["nome"], campos["descricao"], campos["preco"], campos["estoque"], campos["categoria"]),
        )
    return cursor.lastrowid


def atualizar(db, produto_id, campos):
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (campos["nome"], campos["descricao"], campos["preco"], campos["estoque"], campos["categoria"], produto_id),
        )


def possui_pedidos(db, produto_id):
    return db.execute("SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)).fetchone() is not None


def deletar(db, produto_id):
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
