"""Pedido e itens: validação, consultas sem N+1 e gravação transacional."""
from collections import defaultdict

from src.errors import ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

PRODUTO_DESCONHECIDO = "Desconhecido"


def validar_criacao(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool) or not isinstance(itens, list):
        raise ValidationError("Dados inválidos")
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item de pedido inválido")
        produto_id, quantidade = item.get("produto_id"), item.get("quantidade")
        if not isinstance(produto_id, int) or isinstance(produto_id, bool):
            raise ValidationError("Item de pedido inválido: produto_id deve ser inteiro")
        if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
            raise ValidationError("Item de pedido inválido: quantidade deve ser inteiro maior que zero")
    return usuario_id, [{"produto_id": i["produto_id"], "quantidade": i["quantidade"]} for i in itens]


def validar_status(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status


def criar(db, usuario_id, itens):
    """Grava pedido, itens e baixa de estoque numa única transação.

    Todas as checagens acontecem antes da primeira escrita, na mesma ordem do código original
    (produto inexistente, depois estoque). A baixa é condicional para não deixar estoque negativo
    se dois pedidos concorrerem pelo mesmo produto.
    """
    with db:
        ids = sorted({item["produto_id"] for item in itens})
        placeholders = ",".join("?" * len(ids))
        produtos = {
            row["id"]: row
            for row in db.execute(f"SELECT id, nome, preco, estoque FROM produtos WHERE id IN ({placeholders})", ids)
        }
        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado", sucesso=False)
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)
            total = total + (produto["preco"] * item["quantidade"])

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
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if baixa.rowcount == 0:
                # Concorrência ou item repetido no mesmo pedido: o `with db` desfaz tudo.
                raise ValidationError("Estoque insuficiente para " + produto["nome"], sucesso=False)

    return {"pedido_id": pedido_id, "total": total}


def _montar(db, pedidos):
    if not pedidos:
        return []
    ids = [p["id"] for p in pedidos]
    placeholders = ",".join("?" * len(ids))
    itens = db.execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN ({placeholders})
        ORDER BY i.id
        """,
        ids,
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
            "id": p["id"],
            "usuario_id": p["usuario_id"],
            "status": p["status"],
            "total": p["total"],
            "criado_em": p["criado_em"],
            "itens": itens_por_pedido[p["id"]],
        }
        for p in pedidos
    ]


def listar(db, usuario_id=None):
    if usuario_id is None:
        pedidos = db.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    else:
        pedidos = db.execute("SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id", (usuario_id,)).fetchall()
    return _montar(db, pedidos)


def existe(db, pedido_id):
    return db.execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None


def atualizar_status(db, pedido_id, novo_status):
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))


def resumo(db):
    """Contagens e faturamento em uma consulta de agregação."""
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

