// Express 4 não captura rejeição de Promise: encaminha para o errorHandler.
module.exports = (handler) => (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
