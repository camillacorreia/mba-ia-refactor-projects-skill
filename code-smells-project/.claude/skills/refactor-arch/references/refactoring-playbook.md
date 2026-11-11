# Playbook de refatoração (Fase 3)

Cada transformação diz qual anti-pattern resolve, os passos e um exemplo de antes e depois. Os exemplos usam domínios genéricos de propósito: adapte nomes, campos e formato de resposta ao projeto real, mantendo o contrato externo.

| ID | Transformação | Resolve |
|---|---|---|
| T-01 | Extrair configuração e segredos para o ambiente | AP-01, AP-11 |
| T-02 | Queries parametrizadas | AP-02 |
| T-03 | Quebrar God Class em camadas | AP-03, AP-09 |
| T-04 | Controller fino, regra de negócio no model/service | AP-07, AP-13, AP-14 |
| T-05 | Composition root e injeção de dependência no lugar de estado global | AP-08, AP-09 |
| T-06 | Hash de senha forte com migração transparente | AP-05 |
| T-07 | Eliminar N+1 com JOIN, eager loading ou agregação | AP-12 |
| T-08 | Error handler centralizado e erros de domínio | AP-15 |
| T-09 | Transação e integridade referencial | AP-10 |
| T-10 | Callbacks aninhados para async/await | AP-17 |
| T-11 | Substituir API deprecated | AP-16 |
| T-12 | Serialização única e sem campos sensíveis | AP-06, AP-14 |
| T-13 | Proteger endpoints administrativos | AP-04 |
| T-14 | Constantes nomeadas e nomes descritivos | AP-18, AP-19 |
| T-15 | Logging estruturado no lugar de print | AP-20 |

---

## T-01 Extrair configuração e segredos para o ambiente

Passos: criar o módulo de config; ler cada valor do ambiente com default seguro de desenvolvimento; gerar segredo aleatório quando ausente; tirar `debug=True` e `0.0.0.0` do código; criar `.env.example` sem valores reais; trocar todos os usos do literal pelo valor da config.

Antes (Python):
```python
app.config["SECRET_KEY"] = "chave-fixa-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```

Depois (Python):
```python
# src/config/settings.py
import os
import secrets

class Settings:
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "5000"))
        self.database_path = os.getenv("DATABASE_PATH", "app.db")

settings = Settings()

# app.py (entry point)
app = create_app(settings)
if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
```

Antes (Node):
```js
const config = { dbPass: "senha_prod_123", paymentKey: "pk_live_abc", port: 3000 };
```

Depois (Node):
```js
// src/config/index.js
module.exports = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
  dbPath: process.env.DB_PATH || ":memory:",
});
```

## T-02 Queries parametrizadas

Passos: trocar toda concatenação por placeholders do driver; para filtros dinâmicos, montar a lista de condições com placeholders e a lista de parâmetros em paralelo; nunca interpolar nome de coluna vindo do usuário (use lista branca).

Antes:
```python
cursor.execute("SELECT * FROM books WHERE title LIKE '%" + term + "%' AND year = " + str(year))
```

Depois:
```python
conditions, params = ["1=1"], []
if term:
    conditions.append("(title LIKE ? OR summary LIKE ?)")
    params += [f"%{term}%", f"%{term}%"]
if year:
    conditions.append("year = ?")
    params.append(int(year))
cursor.execute(f"SELECT * FROM books WHERE {' AND '.join(conditions)}", params)
```

Node (`sqlite3`, `pg`, `mysql2`): `db.get("SELECT * FROM books WHERE id = ?", [id])`.

## T-03 Quebrar God Class em camadas

Passos: listar as responsabilidades da classe (rotas, schema/seed, consultas, regra de negócio, integração); criar um arquivo por responsabilidade conforme `mvc-guidelines.md`; mover código sem mudar comportamento; o entry point passa a só montar as peças.

Antes (Node):
```js
class Manager {
  constructor() { this.db = new sqlite3.Database(":memory:"); }
  initDb() { /* CREATE TABLE + INSERT seed */ }
  setupRoutes(app) {
    app.post("/api/orders", (req, res) => { /* valida, consulta, cobra, grava, responde */ });
  }
}
```

Depois (Node):
```js
// src/app.js (composition root)
const db = await openDatabase(config.dbPath);
await createSchema(db);
const orderModel = createOrderModel(db);
const orderService = createOrderService({ db, orderModel, paymentGateway: createPaymentGateway(config) });
const app = express();
app.use(express.json());
app.use("/api", buildRoutes({ orderController: createOrderController({ orderService }) }));
app.use(errorHandler);
app.listen(config.port);
```

Python: um `models.py` que cobre vários domínios vira um arquivo por entidade (`models/book_model.py`, `models/member_model.py`...), e a regra que envolve mais de uma entidade vai para um service.

## T-04 Controller fino, regra de negócio no model/service

Passos: no handler, deixar só extrair entrada, chamar o model/service e montar a resposta; mover cálculos, validações de domínio e decisões para o model ou service; validação de entrada fica num validador/schema reaproveitado por create e update.

Antes:
```python
@bp.route("/invoices", methods=["POST"])
def create_invoice():
    data = request.get_json()
    if data["amount"] >= 800:
        fee = 0
    elif data["amount"] >= 300:
        fee = data["base_fee"] * 0.5
    else:
        fee = data["base_fee"]
    cursor.execute("INSERT INTO invoices ...", (...))
    print("ENVIANDO EMAIL")
    return jsonify({"id": cursor.lastrowid}), 201
```

Depois:
```python
# models/invoice_model.py
FREE_SHIPPING_TIERS = [(800, 0.0), (300, 0.5)]   # (valor mínimo, fração do frete cobrada)

def shipping_fee(amount, base_fee):
    for threshold, fraction in FREE_SHIPPING_TIERS:
        if amount >= threshold:
            return base_fee * fraction
    return base_fee

# controllers/invoice_controller.py
def create_invoice(payload):
    data = validate_invoice(payload)              # levanta ValidationError
    invoice_id = invoice_service.create(data)     # calcula frete, grava, notifica
    return {"id": invoice_id}, 201

# views/invoice_routes.py
@bp.route("/invoices", methods=["POST"])
def create_invoice_route():
    body, status = invoice_controller.create_invoice(request.get_json(silent=True))
    return jsonify(body), status
```

## T-05 Composition root e injeção de dependência

Passos: remover variáveis globais mutáveis; criar recursos (conexão, cache, serviços) no composition root; passar como parâmetro ou guardar no contexto da app/requisição (`flask.g`, `app.extensions`, closure de factory em Node).

Antes:
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
    return db_connection
```

Depois:
```python
# src/database.py
import sqlite3
from flask import current_app, g

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

Serviço com dependência injetada:
```python
class NotificationService:
    def __init__(self, mailer):           # mailer recebido, não criado aqui
        self._mailer = mailer
```

Cache em memória que precisa existir: encapsule numa classe criada no composition root e injete; não exporte um `{}` mutável de módulo.

## T-06 Hash de senha forte com migração transparente

Passos: gravar senhas com algoritmo próprio para senha (Werkzeug `generate_password_hash` com scrypt/pbkdf2, `bcrypt`, `crypto.scrypt` no Node); no login, se o valor salvo é legado (texto puro, MD5, hash caseiro), conferir pelo método antigo e regravar com o novo; atualizar o seed para gravar hash.

Antes:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

Depois (Python):
```python
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib, hmac

def set_password(self, raw):
    self.password = generate_password_hash(raw)

def check_password(self, raw):
    if self.password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(self.password, raw)
    legacy = hashlib.md5(raw.encode()).hexdigest()          # formato antigo
    if hmac.compare_digest(self.password, legacy):
        self.set_password(raw)                               # migra no primeiro login
        return True
    return False
```

Depois (Node):
```js
const crypto = require("node:crypto");
function hashPassword(raw) {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto.scryptSync(raw, salt, 64).toString("hex");
  return `scrypt$${salt}$${hash}`;
}
function verifyPassword(raw, stored) {
  const [, salt, hash] = stored.split("$");
  const candidate = crypto.scryptSync(raw, salt, 64);
  return crypto.timingSafeEqual(candidate, Buffer.from(hash, "hex"));
}
```

## T-07 Eliminar N+1

Passos: trocar a consulta por item por um JOIN, um `IN (...)` em lote, eager loading do ORM ou agregação com `GROUP BY`; manter a mesma ordem e formato de saída.

Antes:
```python
for order in orders:
    items = db.execute("SELECT * FROM items WHERE order_id = ?", (order["id"],)).fetchall()
    for item in items:
        product = db.execute("SELECT name FROM products WHERE id = ?", (item["product_id"],)).fetchone()
```

Depois:
```python
rows = db.execute("""
    SELECT i.order_id, i.product_id, i.quantity, i.unit_price, p.name AS product_name
    FROM items i LEFT JOIN products p ON p.id = i.product_id
    WHERE i.order_id IN (SELECT id FROM orders WHERE customer_id = ?)
""", (customer_id,)).fetchall()
items_by_order = defaultdict(list)
for row in rows:
    items_by_order[row["order_id"]].append(row)
```

SQLAlchemy:
```python
# antes: for b in books: b.author.name   (uma query por livro)
books = db.session.execute(
    db.select(Book).options(db.joinedload(Book.author), db.joinedload(Book.publisher))
).scalars().all()

# antes: for g in genres: Book.query.filter_by(genre_id=g.id).count()
counts = dict(db.session.execute(
    db.select(Book.genre_id, db.func.count(Book.id)).group_by(Book.genre_id)
).all())
```

Várias `COUNT(*)` por status viram uma consulta:
```sql
SELECT status, COUNT(*) FROM orders GROUP BY status
```

## T-08 Error handler centralizado

Passos: criar exceções de domínio com status; registrar um handler global; remover `try/except` repetidos das rotas; `except:` sem tipo vira o tipo esperado; nunca devolver `str(e)` de exceção inesperada ao cliente.

Python / Flask:
```python
# src/middlewares/error_handler.py
class AppError(Exception):
    status = 400
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class NotFoundError(AppError):
    status = 404

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message}), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno"}), 500
```

Node / Express:
```js
// src/middlewares/asyncHandler.js
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  if (err.status) return res.status(err.status).send(err.message);
  console.error(err);
  res.status(500).send("Erro interno");
};
```

Se o projeto respondia texto puro em erros (`res.status(404).send("...")`), o handler mantém texto puro.

## T-09 Transação e integridade referencial

Passos: agrupar leitura de validação e escritas na mesma transação; validar tudo antes da primeira escrita; baixa de estoque condicional (`UPDATE ... SET qty = qty - ? WHERE id = ? AND qty >= ?`) para não haver corrida; ao deletar entidade pai, tratar filhos (cascade, bloqueio com 409 ou exclusão explícita na mesma transação).

Antes:
```python
for item in items:
    stock = db.execute("SELECT stock FROM products WHERE id = " + str(item["id"])).fetchone()
    if stock < item["qty"]:
        return {"erro": "sem estoque"}
db.execute("INSERT INTO orders ...")
for item in items:
    db.execute("UPDATE products SET stock = stock - ...")
db.commit()
```

Depois:
```python
def create_order(db, customer_id, items):
    with db:                                   # sqlite3: commit no sucesso, rollback na exceção
        order_id = db.execute("INSERT INTO orders (customer_id, status, total) VALUES (?, 'pending', 0)",
                              (customer_id,)).lastrowid
        total = 0
        for item in items:
            product = db.execute("SELECT price FROM products WHERE id = ?", (item["id"],)).fetchone()
            if product is None:
                raise NotFoundError(f"Item {item['id']} não encontrado")
            updated = db.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                                 (item["qty"], item["id"], item["qty"])).rowcount
            if updated == 0:
                raise ValidationError("Estoque insuficiente")
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                       (order_id, item["id"], item["qty"], product["price"]))
            total += product["price"] * item["qty"]
        db.execute("UPDATE orders SET total = ? WHERE id = ?", (total, order_id))
    return order_id, total
```

Node `sqlite3`: `await run("BEGIN")`, operações, `await run("COMMIT")`, e `ROLLBACK` no `catch`.

## T-10 Callbacks aninhados para async/await

Passos: criar helpers que devolvem Promise para o driver (`get`, `all`, `run`); reescrever o fluxo em sequência com `await`; trocar contadores manuais por `Promise.all` ou uma consulta com JOIN; erros sobem para o error handler.

Antes:
```js
db.all("SELECT * FROM authors", [], (err, authors) => {
  let pending = authors.length;
  authors.forEach(a => {
    db.all("SELECT * FROM books WHERE author_id = ?", [a.id], (err, rows) => {
      pending--; if (pending === 0) res.json(report);
    });
  });
});
```

Depois:
```js
// src/database/connection.js
const all = (db, sql, params = []) =>
  new Promise((resolve, reject) => db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

// src/models/report.model.js
async function salesByAuthor(db) {
  return all(db, `
    SELECT a.id, a.name, b.title, s.amount, s.status
    FROM authors a
    LEFT JOIN books b ON b.author_id = a.id
    LEFT JOIN sales s ON s.book_id = b.id
    ORDER BY a.id, b.id`);
}
```

Para `run` em Node, resolva com `this` do callback (`function (err) { resolve({ lastID: this.lastID, changes: this.changes }) }`), porque arrow function perde o `lastID`.

## T-11 Substituir API deprecated

Passos: para cada ocorrência do AP-16, aplicar o equivalente da tabela do catálogo; rodar a aplicação com avisos ligados para confirmar que sumiram.

Antes:
```python
from datetime import datetime
loan = Loan.query.get(loan_id)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
if loan.return_by < datetime.utcnow(): ...
```

Depois:
```python
from datetime import datetime, timezone

def utcnow():
    # naive em UTC, compatível com colunas DateTime sem timezone já gravadas
    return datetime.now(timezone.utc).replace(tzinfo=None)

loan = db.session.get(Loan, loan_id)
created_at = db.Column(db.DateTime, default=utcnow)
if loan.return_by < utcnow(): ...
```

Atenção: comparar datetime com timezone com coluna sem timezone gera `TypeError`. Se o banco guarda datetimes naive, mantenha naive em UTC como acima.

Node:
```js
// antes
const buf = new Buffer(text);
const { pathname } = url.parse(req.url);
// depois
const buf = Buffer.from(text);
const { pathname } = new URL(req.url, `http://${req.headers.host}`);
```

## T-12 Serialização única e sem campos sensíveis

Passos: uma função de serialização por entidade (no model ou num presenter); remover senha, hash e segredos; reaproveitar em todas as rotas, com campos extras opcionais.

Antes:
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
# e em outra rota, o mesmo dicionário montado à mão campo a campo
```

Depois:
```python
def to_dict(self, include_loans=False):
    data = {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
    if include_loans:
        data["loans"] = [loan.to_dict() for loan in self.loans]
    return data
```

Remover campo sensível muda o formato da resposta: registre em "Intentional Behavior Changes".

## T-13 Proteger endpoints administrativos

Passos: criar middleware/decorator que exige token de admin vindo da config; se o token não estiver configurado, a rota responde 403 (desabilitada por padrão); rota que executa SQL arbitrário só deve existir se for indispensável, e nunca aberta.

Python:
```python
def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        provided = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(provided, expected):
            raise ForbiddenError("Acesso administrativo negado")
        return view(*args, **kwargs)
    return wrapper
```

Node:
```js
module.exports = (config) => (req, res, next) => {
  const token = req.get("X-Admin-Token") || "";
  if (!config.adminToken || token !== config.adminToken) return res.status(403).send("Acesso negado");
  next();
};
```

A rota continua existindo (o contrato de caminho e método se mantém), mas responde 403 sem credencial. Registre como mudança intencional.

## T-14 Constantes nomeadas e nomes descritivos

Passos: extrair números e strings de negócio para constantes no model ou num módulo de constantes; usar a mesma constante em create e update; renomear variáveis internas; manter nomes de campos externos da API.

Antes:
```js
let n = req.body.nm, m = req.body.ml, t = req.body.tk;
let ok = t.length === 32 ? "VALID" : "INVALID";
```

Depois:
```js
const VOUCHER_TOKEN_LENGTH = 32; // formato do voucher emitido pelo parceiro
const { nm: name, ml: email, tk: voucherToken } = req.body; // contrato externo mantido
const status = voucherToken.length === VOUCHER_TOKEN_LENGTH ? VoucherStatus.VALID : VoucherStatus.INVALID;
```

## T-15 Logging estruturado no lugar de print

Passos: usar o logger do framework (`app.logger`, `logging.getLogger(__name__)`, um logger simples em Node); nível adequado (`info`, `warning`, `error`); nunca logar senha, cartão ou segredo (mascarar: `**** **** **** 4444`); efeito colateral simulado (`print("SENDING EMAIL")`) vira chamada a um serviço de notificação injetado.

Antes:
```python
print("Login bem-sucedido: " + email)
print("SENDING EMAIL: order " + str(order_id))
```

Depois:
```python
logger = logging.getLogger(__name__)
logger.info("login_ok user_id=%s", user["id"])
notifier.order_created(order_id, customer_id)   # serviço injetado; em dev só registra no log
```
