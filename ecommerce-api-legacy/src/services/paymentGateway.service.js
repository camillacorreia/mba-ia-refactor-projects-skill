const { PAYMENT_STATUS } = require('../models/payment.model');

// Gateway simulado: aprova cartões que começam com este prefixo (bandeira Visa
// nos cartões de teste do api.http) e recusa o resto. É a regra original.
const APPROVED_CARD_PREFIX = '4';
const VISIBLE_CARD_DIGITS = 4;

function maskCard(cardNumber) {
    return `****${cardNumber.slice(-VISIBLE_CARD_DIGITS)}`;
}

// apiKey vem da config por injeção e nunca vai para log.
function createPaymentGateway({ apiKey, logger }) {
    if (!apiKey) {
        logger.warn('PAYMENT_GATEWAY_KEY ausente, usando gateway simulado');
    }

    return {
        async charge({ cardNumber, amount }) {
            const status = cardNumber.startsWith(APPROVED_CARD_PREFIX)
                ? PAYMENT_STATUS.PAID
                : PAYMENT_STATUS.DENIED;
            logger.info('payment_processed', { card: maskCard(cardNumber), amount, status });
            return { status };
        },
    };
}

module.exports = { createPaymentGateway, maskCard, APPROVED_CARD_PREFIX };
