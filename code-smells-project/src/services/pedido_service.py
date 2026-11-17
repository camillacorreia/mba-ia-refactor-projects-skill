"""Casos de uso de pedido: checkout e mudança de status, com notificação injetada."""
from src.errors import ValidationError
from src.models import pedido_model, usuario_model


class PedidoService:
    def __init__(self, notifier):
        self._notifier = notifier

    def criar(self, db, dados):
        usuario_id, itens = pedido_model.validar_criacao(dados)
        if not usuario_model.existe(db, usuario_id):
            raise ValidationError("Usuário " + str(usuario_id) + " não encontrado", include_sucesso=True)
        resultado = pedido_model.criar(db, usuario_id, itens)
        self._notifier.pedido_criado(resultado["pedido_id"], usuario_id)
        return resultado

    def atualizar_status(self, db, pedido_id, dados):
        novo_status = pedido_model.validar_status(dados)
        pedido_model.atualizar_status(db, pedido_id, novo_status)
        if novo_status == pedido_model.STATUS_APROVADO:
            self._notifier.pedido_aprovado(pedido_id)
        elif novo_status == pedido_model.STATUS_CANCELADO:
            self._notifier.pedido_cancelado(pedido_id)
