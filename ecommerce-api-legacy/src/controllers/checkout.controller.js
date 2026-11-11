const { parseCheckoutPayload } = require('../validators/checkout.validator');

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            const order = parseCheckoutPayload(req.body);
            const { enrollmentId } = await checkoutService.checkout(order);
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };
