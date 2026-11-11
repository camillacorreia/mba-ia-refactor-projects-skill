const sqlite3 = require('sqlite3');

// Abre o banco e expõe helpers com Promise. Nenhum outro módulo abre conexão.
function openDatabase(filename) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(filename, (err) => {
            if (err) return reject(err);
            resolve(wrap(raw));
        });
    });
}

function wrap(raw) {
    const run = (sql, params = []) => new Promise((resolve, reject) => {
        // function() e não arrow: o sqlite3 entrega lastID/changes em `this`.
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });

    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });

    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    const close = () => new Promise((resolve, reject) => {
        raw.close((err) => (err ? reject(err) : resolve()));
    });

    // Uma conexão só, então as transações entram numa fila: duas requisições
    // simultâneas não podem abrir BEGIN ao mesmo tempo na mesma conexão.
    let queue = Promise.resolve();
    const transaction = (work) => {
        const result = queue.then(async () => {
            await run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await run('COMMIT');
                return value;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };

    return { run, get, all, close, transaction };
}

module.exports = { openDatabase };
