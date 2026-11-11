const crypto = require('node:crypto');
const { ForbiddenError } = require('../errors');

const tokensMatch = (provided, expected) => {
    const a = Buffer.from(provided);
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
};

// Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado,
// as rotas administrativas ficam desabilitadas (403).
function createAdminAuth({ adminToken }) {
    return (req, res, next) => {
        const provided = req.get('X-Admin-Token') || '';
        if (!adminToken || !tokensMatch(provided, adminToken)) {
            return next(new ForbiddenError());
        }
        next();
    };
}

module.exports = { createAdminAuth };
