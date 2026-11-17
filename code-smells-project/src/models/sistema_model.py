"""Consultas de manutenção: contagens do health check e reset do banco."""

TABELAS_EM_ORDEM_DE_EXCLUSAO = ["itens_pedido", "pedidos", "produtos", "usuarios"]


def contagens(db):
    db.execute("SELECT 1")
    row = db.execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def resetar(db):
    with db:
        for tabela in TABELAS_EM_ORDEM_DE_EXCLUSAO:
            db.execute(f"DELETE FROM {tabela}")
