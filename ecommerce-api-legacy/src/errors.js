// Erros de domínio. O errorHandler converte cada um em resposta de texto puro,
// que é o formato que a API sempre usou para erros.
class AppError extends Error {
    constructor(status, message) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(400, message); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(400, message); }
}

class ForbiddenError extends AppError {
    constructor(message = 'Acesso negado') { super(403, message); }
}

class NotFoundError extends AppError {
    constructor(message) { super(404, message); }
}

module.exports = { AppError, ValidationError, PaymentDeclinedError, ForbiddenError, NotFoundError };
