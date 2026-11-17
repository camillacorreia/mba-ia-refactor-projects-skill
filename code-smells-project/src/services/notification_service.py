"""Notificações de pedido. Não há gateway de e-mail/SMS/push configurado, então só registra no log."""
import logging


class NotificationService:
    def __init__(self, logger=None):
        self._logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self._logger.info("notificacao canal=email pedido_id=%s usuario_id=%s evento=pedido_criado", pedido_id, usuario_id)
        self._logger.info("notificacao canal=sms usuario_id=%s evento=pedido_recebido", usuario_id)
        self._logger.info("notificacao canal=push pedido_id=%s evento=novo_pedido", pedido_id)

    def pedido_aprovado(self, pedido_id):
        self._logger.info("notificacao pedido_id=%s evento=aprovado acao=preparar_envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        self._logger.info("notificacao pedido_id=%s evento=cancelado acao=devolver_estoque", pedido_id)
