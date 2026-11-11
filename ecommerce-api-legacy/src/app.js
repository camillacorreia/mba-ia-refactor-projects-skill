// Entry point e composition root: lê a config, abre o banco, monta as camadas
// e sobe o servidor. Comando continua `npm start` (node src/app.js).
const express = require('express');
const { loadConfig } = require('./config');
const { createLogger } = require('./lib/logger');
const { openDatabase } = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const { createUserModel } = require('./models/user.model');
const { createCourseModel } = require('./models/course.model');
const { createEnrollmentModel } = require('./models/enrollment.model');
const { createPaymentModel } = require('./models/payment.model');
const { createAuditLogModel } = require('./models/auditLog.model');
const { createPaymentGateway } = require('./services/paymentGateway.service');
const { createCheckoutService } = require('./services/checkout.service');
const { createFinancialReportService } = require('./services/financialReport.service');
const { createUserService } = require('./services/user.service');
const { createCheckoutController } = require('./controllers/checkout.controller');
const { createReportController } = require('./controllers/report.controller');
const { createUserController } = require('./controllers/user.controller');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { buildRoutes } = require('./routes');

async function createApp(config, logger) {
    const db = await openDatabase(config.dbPath);
    await createSchema(db);
    await seed(db);

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);

    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = createCheckoutService({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel, paymentGateway, logger,
    });
    const financialReportService = createFinancialReportService({ enrollmentModel });
    const userService = createUserService({ db, userModel, auditLogModel });

    if (!config.adminToken) {
        logger.warn('ADMIN_TOKEN ausente, rotas administrativas respondem 403');
    }

    const app = express();
    app.use(express.json());
    app.use('/api', buildRoutes({
        checkoutController: createCheckoutController({ checkoutService }),
        reportController: createReportController({ financialReportService }),
        userController: createUserController({ userService }),
        adminAuth: createAdminAuth({ adminToken: config.adminToken }),
    }));
    app.use(createErrorHandler({ logger }));

    return { app, db };
}

async function start() {
    const config = loadConfig();
    const logger = createLogger({ level: config.logLevel });
    const { app } = await createApp(config, logger);
    app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        console.error(err);
        process.exit(1);
    });
}

module.exports = { createApp };
