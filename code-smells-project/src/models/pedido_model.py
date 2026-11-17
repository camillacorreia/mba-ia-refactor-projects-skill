"""Pedidos e itens: validação, gravação transacional e consultas sem N+1."""
from collections import defaultdict

from src.errors import ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO]
PRODUTO_DESCONHECIDO = "Desconhecido"


class EstoqueInsuficiente(ValidationError):
    def __init__(self, nome_produto):
        super().__init__("Estoque insuficiente para " + nome_produto, include_sucesso=True)


class ProdutoInexistente(ValidationError):
    def __init__(self, produto_id):
        super().__init__("Produto " + str(produto_id) + " não encontrado", include_sucesso=True)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def validar_criacao(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_int(usuario_id):
        raise ValidationError("Usuario ID deve ser inteiro")
    if not itens or not isinstance(itens, list):
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict) or not _is_int(item.get("produto_id")):
            raise ValidationError("Cada item precisa de produto_id inteiro")
        if not _is_int(item.get("quantidade")) or item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser um inteiro positivo")
    return usuario_id, itens


def validar_status(dados):
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status


def criar(db, usuario_id, itens):
    """Grava pedido, itens e baixa de estoque numa única transação."""
    with db:
        produtos = {}
        for item in itens:
            produto = db.execute(
                "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            if produto is None:
                raise ProdutoInexistente(item["produto_id"])
            if produto["estoque"] < item["quantidade"]:
                raise EstoqueInsuficiente(produto["nome"])
            produtos[item["produto_id"]] = produto

        total = 0
        for item in itens:
            total = total + (produtos[item["produto_id"]]["preco"] * item["quantidade"])

        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid

        for item in itens:
            produto = produtos[item["produto_id"]]
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            # Baixa condicional: se outro pedido levou o estoque entre a checagem e aqui, desfaz tudo.
            baixou = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if baixou == 0:
                raise EstoqueInsuficiente(produto["nome"])

    return {"pedido_id": pedido_id, "total": total}


def listar(db, usuario_id=None):
    filtro, params = "", []
    if usuario_id is not None:
        filtro, params = "WHERE usuario_id = ?", [usuario_id]
    pedidos = db.execute(f"SELECT * FROM pedidos {filtro} ORDER BY id", params).fetchall()

    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN (SELECT id FROM pedidos {filtro})
        ORDER BY i.id
        """,
        params,
    ).fetchall()
    itens_por_pedido = defaultdict(list)
    for item in itens:
        itens_por_pedido[item["pedido_id"]].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido[row["id"]],
        }
        for row in pedidos
    ]


def atualizar_status(db, pedido_id, novo_status):
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def resumo_vendas(db):
    row = db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()
    return dict(row)
