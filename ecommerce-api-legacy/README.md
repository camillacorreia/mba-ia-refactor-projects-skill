# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. Sem nenhuma variável de ambiente ela funciona com banco SQLite em memória, que recebe o seed automaticamente a cada boot.

Para usar as rotas administrativas, defina um token ao subir:

```bash
ADMIN_TOKEN=um-token-local npm start
```

e envie o mesmo valor no header `X-Admin-Token`. Sem `ADMIN_TOKEN`, essas rotas respondem 403.

## Configuração

Todas as variáveis estão em `.env.example`. O projeto não carrega `.env` sozinho: exporte as variáveis no shell ou use `node --env-file=.env src/app.js` (Node 20.6+).

| Variável | Default | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `DB_PATH` | `:memory:` | Arquivo SQLite |
| `PAYMENT_GATEWAY_KEY` | vazio | Chave do gateway; vazio usa o gateway simulado |
| `ADMIN_TOKEN` | vazio | Token das rotas admin (`X-Admin-Token`) |
| `LOG_LEVEL` | `info` | `debug`, `info`, `warn`, `error` ou `silent` |

## Rotas

| Método | Caminho | Auth |
|---|---|---|
| POST | `/api/checkout` | não |
| GET | `/api/admin/financial-report` | `X-Admin-Token` |
| DELETE | `/api/users/:id` | `X-Admin-Token` |

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── app.js              # entry point e composition root
├── config/             # configuração lida do ambiente
├── database/           # conexão (helpers com Promise e transação) e schema/seed
├── models/             # acesso a dados por tabela
├── services/           # casos de uso: checkout, relatório, usuários, gateway de pagamento
├── validators/         # validação do payload de checkout
├── controllers/        # orquestram requisição -> service -> resposta
├── routes/             # mapeamento método + caminho
├── middlewares/        # auth admin, async handler, error handler
├── lib/                # logger e hash de senha
└── errors.js           # erros de domínio com status HTTP
```
