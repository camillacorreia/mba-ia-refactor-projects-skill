import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    """Envio de e-mail. Sem SMTP configurado, vira no-op e só registra no log."""

    def __init__(self, host='', port=587, user='', password='', smtp_factory=smtplib.SMTP):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._smtp_factory = smtp_factory

    @classmethod
    def from_settings(cls, settings):
        return cls(settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password)

    @property
    def enabled(self):
        return bool(self._host and self._user and self._password)

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info('email_disabled to=%s subject=%r', to, subject)
            return False
        try:
            with self._smtp_factory(self._host, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, to, f"Subject: {subject}\n\n{body}")
            logger.info('email_sent to=%s', to)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception('email_failed to=%s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        return self.send_email(user.email, subject, body)
