const { ValidationError } = require('../errors');

function createUserController({ userService }) {
    return {
        async remove(req, res) {
            const userId = Number(req.params.id);
            if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError();

            await userService.deleteUser(userId);
            res.send('Usuário deletado');
        },
    };
}

module.exports = { createUserController };
