const { AppError } = require('../errors');

// Único ponto que transforma erro em resposta. Mantém texto puro, como a API
// sempre respondeu erros. Detalhe de erro inesperado só vai para o log.
function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) {
            return res.status(err.status).send(err.message);
        }
        if (err.type === 'entity.parse.failed') {
            return res.status(400).send('Bad Request');
        }
        logger.error('unhandled_error', { method: req.method, path: req.path, error: err.stack || err });
        return res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
