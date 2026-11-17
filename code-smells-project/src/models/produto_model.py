"""Produtos: acesso a dados, regras de validação e serialização."""
import numbers

from src.errors import ConflictError, ValidationError

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_MIN_CARACTERES = 2
NOME_MAX_CARACTERES = 200


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
    return isinstance(value, numbers.Real) and not isinstance(value, bool)


def validar(dados):
    """Validação única usada no cadastro e na atualização."""
    if not dados:
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

    if not _is_number(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str) or len(nome) < NOME_MIN_CARACTERES:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX_CARACTERES:
        raise ValidationError("Nome muito longo")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
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
    sql = f"SELECT * FROM produtos WHERE {' AND '.join(condicoes)} ORDER BY id"
    return [to_dict(row) for row in db.execute(sql, params)]


def criar(db, dados):
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"]),
        )
    return cursor.lastrowid


def atualizar(db, produto_id, dados):
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (dados["nome"], dados["descricao"], dados["preco"], dados["estoque"], dados["categoria"], produto_id),
        )


def deletar(db, produto_id):
    with db:
        em_pedidos = db.execute(
            "SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)
        ).fetchone()
        if em_pedidos:
            raise ConflictError("Produto possui pedidos e não pode ser removido")
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
