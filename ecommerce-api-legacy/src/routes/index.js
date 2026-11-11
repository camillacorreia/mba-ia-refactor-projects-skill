const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

// "View" da API: só mapeia método + caminho para o controller.
function buildRoutes({ checkoutController, reportController, userController, adminAuth }) {
    const router = express.Router();

    router.post('/checkout', asyncHandler(checkoutController.checkout));
    router.get('/admin/financial-report', adminAuth, asyncHandler(reportController.financialReport));
    router.delete('/users/:id', adminAuth, asyncHandler(userController.remove));

    return router;
}

module.exports = { buildRoutes };
