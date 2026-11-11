"""Casos de uso de pedido: criação com notificação e mudança de status."""
from src.errors import NotFoundError
from src.models import pedido_model


class PedidoService:
    def __init__(self, notifier):
        self._notifier = notifier

    def criar(self, db, usuario_id, itens):
        resultado = pedido_model.criar(db, usuario_id, itens)
        self._notifier.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado

    def atualizar_status(self, db, pedido_id, novo_status):
        if not pedido_model.existe(db, pedido_id):
            raise NotFoundError("Pedido não encontrado", sucesso=False)
        pedido_model.atualizar_status(db, pedido_id, novo_status)
        if novo_status == pedido_model.STATUS_APROVADO:
            self._notifier.pedido_aprovado(pedido_id)
        elif novo_status == pedido_model.STATUS_CANCELADO:
            self._notifier.pedido_cancelado(pedido_id)
