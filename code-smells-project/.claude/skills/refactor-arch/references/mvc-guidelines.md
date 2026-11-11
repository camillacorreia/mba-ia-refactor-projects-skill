# Guidelines de arquitetura MVC (Fase 3)

## As camadas

Numa API não existe tela, então a "View" é a camada HTTP: declaração de rotas e formatação da resposta. O fluxo de uma requisição é sempre o mesmo:

```
requisição -> View/Route -> Controller -> Model (e Service, quando houver) -> banco
resposta   <- View/Route <- Controller <- Model
```

| Camada | Responsabilidade | Pode | Não pode |
|---|---|---|---|
| Config | Ler configuração do ambiente com defaults seguros para desenvolvimento | Ler `os.environ` / `process.env`, `.env` | Ter segredo literal |
| Model | Representar as entidades, acessar o banco e guardar as regras de domínio da entidade (validação, cálculos, invariantes) | SQL parametrizado ou ORM, transações, métodos como `is_overdue()`, `to_dict()` sem campos sensíveis | Conhecer `request`, `response`, status HTTP |
| Service (opcional) | Caso de uso que envolve várias entidades ou integração externa (checkout, notificação, relatório) | Chamar vários models, abrir transação, chamar gateway/e-mail recebido por injeção | Conhecer HTTP |
| Controller | Orquestrar o fluxo de uma ação: extrair e validar entrada, chamar model/service, escolher o status e montar o payload | Lançar erros de domínio (`NotFoundError`, `ValidationError`) | Conter SQL, regra de negócio pesada, `print` de efeito colateral |
| View / Routes | Mapear método + caminho para o controller e serializar a resposta | Registrar rotas, aplicar middleware de auth | Conter lógica |
| Middlewares | Tratamento de erro centralizado, autenticação, logging de requisição | Converter exceção em resposta JSON | Regra de negócio |
| Composition root (entry point) | Criar a app, ler config, conectar o banco, injetar dependências, registrar rotas e middlewares | Instanciar tudo | Lógica de requisição |

Regra de dependência: cada camada só importa a camada abaixo. Model nunca importa controller; controller nunca importa o framework de rotas além do objeto de request/response que recebe.

Regra de negócio "pesada" fica no model ou no service, nunca no controller. Controller com mais de ~25 linhas por ação é sinal de que algo deveria ter descido.

## Estrutura alvo por stack

### Python / Flask

```
<projeto>/
├── app.py                      # entry point: from src.app import create_app; app = create_app()
├── .env.example
├── requirements.txt
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): config, banco, blueprints, error handlers
    ├── config/
    │   └── settings.py         # classe Settings lida do ambiente
    ├── database.py             # conexão/sessão por app ou por requisição, init de schema e seed
    ├── models/
    │   └── <entidade>_model.py
    ├── services/               # só se houver caso de uso entre entidades
    │   └── <caso_de_uso>_service.py
    ├── controllers/
    │   └── <entidade>_controller.py
    ├── views/
    │   └── <entidade>_routes.py   # Blueprint por recurso
    └── middlewares/
        ├── error_handler.py
        └── auth.py             # se houver rota administrativa
```

O `app.py` da raiz continua existindo para que `python app.py` (o comando original) funcione. Se o projeto tem `seed.py` que importa `from app import app, db`, mantenha esses nomes exportados no `app.py` da raiz.

Use app factory (`create_app`) em vez de criar `Flask(__name__)` no import de um módulo compartilhado.

### Node.js / Express

```
<projeto>/
├── .env.example
├── package.json                # "main" e "start" apontam para src/server.js ou src/app.js
└── src/
    ├── app.js                  # entry point original: cria a app e chama listen
    ├── config/
    │   └── index.js            # config a partir de process.env
    ├── database/
    │   ├── connection.js       # abre o banco e expõe helpers async (run/get/all com Promise)
    │   └── schema.js           # criação de tabelas e seed
    ├── models/
    │   └── <entidade>.model.js
    ├── services/
    │   └── <caso_de_uso>.service.js
    ├── controllers/
    │   └── <entidade>.controller.js
    ├── routes/                 # a "View" da API
    │   └── index.js
    └── middlewares/
        ├── errorHandler.js
        └── asyncHandler.js
```

Dependências entram por factory: `createCheckoutService({ db, paymentGateway, logger })`. Nenhum módulo abre conexão por conta própria.

### Outras stacks

Mesmo desenho, com a convenção do framework: FastAPI (`routers/` como views, `schemas/` Pydantic para validação), Django (já é MTV: views finas, regras em models/services), Rails/Laravel (controllers finos, regras em models ou service objects). Não invente pastas que o framework já resolve de outro jeito.

## Projeto parcialmente organizado

Quando já existem `models/`, `routes/`, `services/`, `utils/`:

1. Mantenha os nomes que já estão certos. `routes/` cumpre o papel de views; não renomeie para `views/` só por estética.
2. Crie o que falta: `controllers/` com a lógica que hoje está nas rotas, `config/` com o que está hardcoded no entry point, `middlewares/` com o error handler.
3. Mova regras repetidas para o model (ex.: se o model já tem um método `is_<estado>()`, ele vira a única implementação e as cópias nas rotas saem).
4. Use os utilitários que já existem antes de escrever novos; remova os que ficaram sem uso.
5. Serviços instanciados mas nunca chamados: ou passam a ser chamados no fluxo certo com dependência injetada, ou saem.

## Configuração

Toda configuração vem do ambiente, com default seguro para desenvolvimento:

| Variável | Default em desenvolvimento |
|---|---|
| `SECRET_KEY` | gerada aleatoriamente no boot (`secrets.token_hex(32)` / `crypto.randomBytes(32)`) com aviso no log |
| `DEBUG` | `false` |
| `HOST` | `127.0.0.1` |
| `PORT` | a porta original do projeto |
| `DATABASE_URL` / `DB_PATH` | o arquivo/URI original |
| `CORS_ORIGINS` | `*` só se for o comportamento original, documentado |
| credenciais externas (SMTP, gateway) | vazias; o serviço vira no-op e loga que está desabilitado |

A aplicação precisa subir sem nenhuma variável definida, senão o boot quebra para quem só clonou o repositório. Segredos de produção são obrigatórios apenas quando `ENV=production`.

## Error handling centralizado

Um único lugar converte exceções em resposta:

- Erros de domínio com status: `ValidationError` (400), `UnauthorizedError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ConflictError` (409).
- Qualquer outra exceção vira 500 com mensagem genérica no corpo e o detalhe só no log.
- O formato do corpo de erro segue o que o projeto já usava (`{"erro": ...}` ou `{"error": ...}`) para não quebrar clientes.
