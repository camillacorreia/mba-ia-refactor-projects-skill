const crypto = require('node:crypto');
const { promisify } = require('node:util');

const scrypt = promisify(crypto.scrypt);
const SALT_BYTES = 16;
const KEY_LENGTH = 64;

// Formato gravado: scrypt$<salt hex>$<hash hex>
async function hashPassword(rawPassword) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derived = await scrypt(rawPassword, salt, KEY_LENGTH);
    return `scrypt$${salt}$${derived.toString('hex')}`;
}

// Senha usada quando o checkout cria a conta sem "pwd": aleatória e descartada,
// em vez do antigo default fixo "123456".
function randomPassword() {
    return crypto.randomBytes(24).toString('base64url');
}

module.exports = { hashPassword, randomPassword };
