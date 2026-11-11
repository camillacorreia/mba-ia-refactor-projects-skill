# Análise de projeto (Fase 1)

Objetivo: descobrir com evidência qual é a stack, o domínio e a arquitetura atual, e montar o inventário de rotas que a Fase 3 vai usar para validar.

## 1. Inventário de arquivos

Liste os arquivos de código, ignorando dependências, ambientes virtuais, caches, a própria skill e bancos locais:

```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.mjs" -o -name "*.cjs" \
  -o -name "*.rb" -o -name "*.php" -o -name "*.go" -o -name "*.java" -o -name "*.kt" -o -name "*.cs" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.claude/*" \
  -not -path "*/__pycache__/*" -not -path "*/dist/*" -not -path "*/build/*" -not -path "./.git/*" \
  | sort | xargs wc -l
```

O número em `Source files` é a quantidade de arquivos dessa lista. Arquivos `__init__.py` vazios contam, mas mencione se forem triviais. Lockfiles e `.http` não contam como código.

## 2. Linguagem

Decida pelo manifesto e confirme pela extensão dominante.

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, maioria `.py` | Python |
| `package.json` sem `typescript` e maioria `.js` | JavaScript (Node.js) |
| `package.json` com `typescript`, `tsconfig.json`, maioria `.ts` | TypeScript (Node.js) |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `*.csproj` | C# |

Versão da linguagem: `engines` no `package.json`, `python_requires`, `.python-version`, `.nvmrc`, `go.mod`. Se não houver, escreva "versão não declarada".

## 3. Framework

Procure a dependência no manifesto e confirme pelo import no código.

| Framework | Manifesto | Assinatura no código |
|---|---|---|
| Flask | `flask` | `Flask(__name__)`, `@app.route`, `Blueprint(`, `add_url_rule` |
| FastAPI | `fastapi` | `FastAPI()`, `@app.get`, `APIRouter` |
| Django | `django` | `urls.py`, `views.py`, `INSTALLED_APPS` |
| Express | `express` | `express()`, `app.get(`, `express.Router()` |
| Fastify | `fastify` | `fastify()`, `fastify.get(` |
| NestJS | `@nestjs/core` | `@Controller(`, `@Module(` |
| Rails | `rails` | `config/routes.rb`, `ApplicationController` |
| Laravel | `laravel/framework` | `routes/web.php`, `Route::get` |
| Spring Boot | `spring-boot-starter-web` | `@RestController`, `@GetMapping` |
| Gin / Echo | `gin-gonic/gin`, `labstack/echo` | `gin.Default()`, `e.GET(` |

Use a versão exata do manifesto (`flask==3.1.1`, `"express": "^4.18.2"`).

## 4. Banco de dados e acesso a dados

| Sinal | Conclusão |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite com SQL cru (Python) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite com SQL cru (Node) |
| `':memory:'` | Banco em memória: dados somem a cada boot |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | ORM SQLAlchemy |
| `sequelize`, `typeorm`, `prisma`, `mongoose`, `knex` | ORM / query builder Node |
| `psycopg`, `pg`, `mysql`, `pymongo` | Postgres, MySQL, MongoDB |

Liste as tabelas a partir de `CREATE TABLE`, `__tablename__`, `class X(db.Model)` ou schema do ORM.

## 5. Domínio

Descreva o domínio a partir dos nomes de tabelas, rotas e entidades, em uma frase com as entidades principais. Exemplos: "API de biblioteca (livros, membros, empréstimos, multas)", "Agendamento de clínica (pacientes, médicos, consultas, lembretes)". Se houver fluxo principal claro (checkout, matrícula, aprovação), mencione.

## 6. Inventário de rotas

Extraia todas as rotas com método, caminho e handler:

```bash
# Flask
grep -rn -E "@[a-zA-Z_]+\.route\(|add_url_rule\(" --include=*.py .
# Express / Fastify
grep -rn -E "\.(get|post|put|patch|delete)\(\s*['\"]/" --include=*.js --include=*.ts .
# FastAPI
grep -rn -E "@[a-zA-Z_]+\.(get|post|put|patch|delete)\(" --include=*.py .
```

Para Flask com Blueprint, some o `url_prefix` do registro ao caminho. Rotas sem `methods` em Flask são `GET`.

## 7. Arquitetura atual

Classifique com uma destas etiquetas e dê a evidência:

| Classificação | Quando usar |
|---|---|
| Monolítica sem camadas | Rotas, SQL e regra de negócio no mesmo arquivo ou classe (God Class) |
| Separação nominal | Existem arquivos chamados `models`/`controllers`, mas cada um mistura responsabilidades (ex.: "models" com SQL e regra de negócio, "controllers" com validação e notificação) |
| Camadas parciais | Existem pastas `models/`, `routes/`, `services/`, mas a regra de negócio e a serialização estão nas rotas, há serviços não usados ou utilitários duplicados |
| MVC / camadas adequadas | Rotas finas, controllers orquestram, models encapsulam dados e regras, config externa |

Registre também: entry point e comando de execução (README, `scripts.start`, `if __name__ == "__main__"`), porta, onde a configuração está (hardcoded, `.env`, variáveis de ambiente) e se existe seed ou criação automática de schema.

## 8. Como iniciar a aplicação

Anote o comando exato, porque a Fase 3 precisa subir a aplicação antes e depois:

| Stack | Comando típico | Porta |
|---|---|---|
| Flask com `app.run` | `python app.py`, ou `flask --app app run --port <P>` | 5000 |
| Flask com seed separado | `python seed.py` antes do boot | 5000 |
| Express | `npm start` ou `node <main>` | o que `listen` usar |
| FastAPI | `uvicorn main:app --port <P>` | 8000 |

Se o projeto não tem dependências instaladas, instale num ambiente isolado (`python -m venv .venv && .venv/bin/pip install -r requirements.txt`, `npm install`). Isso não altera arquivos versionados e é permitido na Fase 1.
