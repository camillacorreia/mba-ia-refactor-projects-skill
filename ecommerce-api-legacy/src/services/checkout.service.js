const { NotFoundError, PaymentDeclinedError } = require('../errors');
const { PAYMENT_STATUS } = require('../models/payment.model');
const { hashPassword, randomPassword } = require('../lib/password');

function createCheckoutService({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, logger }) {
    return {
        // Recebe o pedido já validado. Ordem: curso existe, pagamento aprovado,
        // e só então grava usuário, matrícula, pagamento e auditoria, tudo na
        // mesma transação.
        async checkout({ userName, email, password, courseId, cardNumber }) {
            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const { status } = await paymentGateway.charge({ cardNumber, amount: course.price });
            if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError();

            const { userId, enrollmentId } = await db.transaction(async () => {
                const existing = await userModel.findIdByEmail(email);
                const userId = existing
                    ? existing.id
                    : await userModel.create({
                        name: userName,
                        email,
                        passwordHash: await hashPassword(password || randomPassword()),
                    });

                const enrollmentId = await enrollmentModel.create({ userId, courseId: course.id });
                await paymentModel.create({ enrollmentId, amount: course.price, status });
                await auditLogModel.record(`Checkout curso ${course.id} por ${userId}`);
                return { userId, enrollmentId };
            });

            logger.info('checkout_completed', { userId, courseId: course.id, enrollmentId });
            return { enrollmentId };
        },
    };
}

module.exports = { createCheckoutService };
