const LEVELS = { debug: 10, info: 20, warn: 30, error: 40, silent: 100 };

function createLogger({ level = 'info' } = {}) {
    const threshold = LEVELS[level] ?? LEVELS.info;

    const write = (name, stream) => (message, context = {}) => {
        if (LEVELS[name] < threshold) return;
        const fields = Object.entries(context).map(([key, value]) => `${key}=${value}`).join(' ');
        stream(`${new Date().toISOString()} ${name.toUpperCase()} ${message}${fields ? ' ' + fields : ''}`);
    };

    return {
        debug: write('debug', console.log),
        info: write('info', console.log),
        warn: write('warn', console.warn),
        error: write('error', console.error),
    };
}

module.exports = { createLogger };
