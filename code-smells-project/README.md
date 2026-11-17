# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, já refatorada para MVC.

## Como rodar

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py            # ou: .venv/bin/flask --app app run
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash). Bancos antigos com senha em texto puro são migrados para hash no boot.

## Configuração

Tudo vem de variáveis de ambiente, listadas em `.env.example`. Nenhuma é obrigatória para desenvolvimento.

| Variável | Default | Uso |
|---|---|---|
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DEBUG` | `false` | Debug do Flask (nunca ligue exposto na rede) |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `SECRET_KEY` | aleatória por boot | Assina os tokens do login |
| `ADMIN_TOKEN` | vazio | Token das rotas administrativas |
| `TOKEN_MAX_AGE_SECONDS` | `3600` | Validade do token do login |

## Rotas protegidas

`GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<id>`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas` e `POST /admin/reset-db` exigem credencial e respondem 403 sem ela. Valem duas formas:

```bash
# token administrativo
ADMIN_TOKEN=troque-isto .venv/bin/python app.py
curl -H "X-Admin-Token: troque-isto" http://127.0.0.1:5000/relatorios/vendas

# token do login de um usuário admin (campo "token" da resposta do POST /login)
curl -H "Authorization: Bearer <token>" http://127.0.0.1:5000/relatorios/vendas
```

`GET /usuarios/<id>` e `GET /pedidos/usuario/<id>` também aceitam o Bearer do próprio usuário. `POST /admin/query` (SQL arbitrário) foi removida.

## Estrutura

```
app.py                  entry point
src/app.py              create_app: config, banco, serviços, blueprints, error handlers
src/config/settings.py  configuração a partir do ambiente
src/database.py         conexão por requisição, schema e seed
src/models/             acesso a dados e regras por entidade
src/services/           checkout, relatório, notificação, token
src/controllers/        fluxo de cada ação
src/views/              blueprints (rotas)
src/middlewares/        autenticação e tratamento de erro
```
