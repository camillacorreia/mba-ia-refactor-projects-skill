const { ValidationError } = require('../errors');

const isFilledString = (value) => typeof value === 'string' && value.trim() !== '';

// Campos externos da API (usr, eml, pwd, c_id, card) são o contrato e não mudam;
// por dentro viram nomes legíveis.
function parseCheckoutPayload(body = {}) {
    const { usr: userName, eml: email, pwd: password, c_id: rawCourseId, card: cardNumber } = body;
    const courseId = Number(rawCourseId);

    if (!isFilledString(userName) || !isFilledString(email) || !isFilledString(cardNumber)) {
        throw new ValidationError();
    }
    if (!rawCourseId || !Number.isInteger(courseId)) {
        throw new ValidationError();
    }
    if (password !== undefined && password !== null && typeof password !== 'string') {
        throw new ValidationError();
    }

    return { userName, email, password: password || undefined, courseId, cardNumber };
}

module.exports = { parseCheckoutPayload };
