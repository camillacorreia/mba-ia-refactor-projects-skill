const { hashPassword } = require('../lib/password');
const { PAYMENT_STATUS } = require('../models/payment.model');

const TABLES = [
    `CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        pass TEXT
    )`,
    `CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT,
        price REAL,
        active INTEGER
    )`,
    `CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    )`,
    `CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    )`,
    `CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT,
        created_at DATETIME
    )`,
];

async function createSchema(db) {
    await db.run('PRAGMA foreign_keys = ON');
    for (const sql of TABLES) {
        await db.run(sql);
    }
}

// Dados de desenvolvimento. Só roda com o banco vazio, para não duplicar
// registros se DB_PATH apontar para um arquivo.
async function seed(db) {
    const { total } = await db.get('SELECT COUNT(*) AS total FROM users');
    if (total > 0) return;

    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', await hashPassword('123')]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)',
            ['Clean Architecture', 997.0, 'Docker', 497.0]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, ?, ?)',
            [997.0, PAYMENT_STATUS.PAID]);
    });
}

module.exports = { createSchema, seed };
