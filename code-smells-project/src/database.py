"""Conexão SQLite por requisição (flask.g), criação de schema e seed."""
import logging
import sqlite3

from flask import current_app, g

from src.models import usuario_model

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    descricao TEXT,
    preco REAL,
    estoque INTEGER,
    categoria TEXT,
    ativo INTEGER DEFAULT 1,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT,
    tipo TEXT DEFAULT 'cliente',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    status TEXT DEFAULT 'pendente',
    total REAL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER REFERENCES pedidos(id),
    produto_id INTEGER REFERENCES produtos(id),
    quantidade INTEGER,
    preco_unitario REAL
);
"""

# Dados fictícios de desenvolvimento. As senhas são gravadas com hash no seed.
SEED_PRODUTOS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

SEED_USUARIOS = [
    ("Admin", "admin@loja.com", "admin123", usuario_model.TIPO_ADMIN),
    ("João Silva", "joao@email.com", "123456", usuario_model.TIPO_PADRAO),
    ("Maria Santos", "maria@email.com", "senha123", usuario_model.TIPO_PADRAO),
]


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _seed(conn):
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        SEED_PRODUTOS,
    )
    for nome, email, senha, tipo in SEED_USUARIOS:
        usuario_model.criar(conn, nome, email, senha, tipo, commit=False)


def init_db(path):
    conn = connect(path)
    try:
        with conn:
            conn.executescript(SCHEMA)
        with conn:
            _seed(conn)
        migradas = usuario_model.migrar_senhas_legadas(conn)
        if migradas:
            logger.info("senhas_legadas_migradas total=%s", migradas)
    finally:
        conn.close()


def init_app(app):
    init_db(app.config["DATABASE_PATH"])
    app.teardown_appcontext(close_db)
