const { NotFoundError } = require('../errors');

function createUserService({ db, userModel, auditLogModel }) {
    return {
        async deleteUser(userId) {
            await db.transaction(async () => {
                const deleted = await userModel.deleteById(userId);
                if (!deleted) throw new NotFoundError('Usuário não encontrado');
                await auditLogModel.record(`Usuário ${userId} deletado`);
            });
        },
    };
}

module.exports = { createUserService };
