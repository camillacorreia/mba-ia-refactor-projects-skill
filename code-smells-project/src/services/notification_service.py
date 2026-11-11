"""Notificações de pedido. Sem provedor configurado, só registra no log."""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, log=logger):
        self._log = log

    def pedido_criado(self, pedido_id, usuario_id):
        self._log.info("notificacao canal=email pedido_id=%s usuario_id=%s evento=pedido_criado", pedido_id, usuario_id)
        self._log.info("notificacao canal=sms pedido_id=%s evento=pedido_recebido", pedido_id)
        self._log.info("notificacao canal=push pedido_id=%s evento=novo_pedido", pedido_id)

    def pedido_aprovado(self, pedido_id):
        self._log.info("notificacao pedido_id=%s evento=pedido_aprovado acao=preparar_envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        self._log.info("notificacao pedido_id=%s evento=pedido_cancelado", pedido_id)
