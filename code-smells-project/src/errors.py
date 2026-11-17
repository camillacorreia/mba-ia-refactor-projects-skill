"""Erros de domínio. O error handler converte cada um no status HTTP correspondente."""


class AppError(Exception):
    status = 400

    def __init__(self, message, include_sucesso=False):
        super().__init__(message)
        self.message = message
        # Algumas respostas originais de erro traziam "sucesso": false; mantemos o formato.
        self.include_sucesso = include_sucesso

    def to_dict(self):
        body = {"erro": self.message}
        if self.include_sucesso:
            body["sucesso"] = False
        return body


class ValidationError(AppError):
    status = 400


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409
