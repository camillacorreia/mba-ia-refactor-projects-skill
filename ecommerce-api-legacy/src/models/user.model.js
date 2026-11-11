function createUserModel(db) {
    return {
        findIdByEmail(email) {
            return db.get('SELECT id FROM users WHERE email = ?', [email]);
        },

        // passwordHash já vem pronto: o model não conhece o algoritmo de hash.
        async create({ name, email, passwordHash }) {
            const { lastID } = await db.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash],
            );
            return lastID;
        },

        // Matrículas e pagamentos saem junto via ON DELETE CASCADE (schema.js).
        async deleteById(id) {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
            return changes > 0;
        },
    };
}

module.exports = { createUserModel };
