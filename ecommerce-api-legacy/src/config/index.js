// Toda configuração vem do ambiente. Os defaults servem para desenvolvimento
// local e não contêm nenhum segredo real.
function loadConfig(env = process.env) {
    return Object.freeze({
        port: Number(env.PORT) || 3000,
        dbPath: env.DB_PATH || ':memory:',
        // Chave do gateway de pagamento. O gateway atual é simulado e não a usa
        // para chamada externa; ela fica aqui para quando a integração real entrar.
        paymentGatewayKey: env.PAYMENT_GATEWAY_KEY || '',
        // Sem ADMIN_TOKEN definido, as rotas administrativas respondem 403.
        adminToken: env.ADMIN_TOKEN || '',
        logLevel: env.LOG_LEVEL || 'info',
    });
}

module.exports = { loadConfig };
