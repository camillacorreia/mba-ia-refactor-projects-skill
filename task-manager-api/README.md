# task-manager-api

API de Task Manager em Python/Flask (tasks, usuários e categorias, com busca, estatísticas e relatórios). Foi refatorada para MVC com a skill `refactor-arch`.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional; sem .env a aplicação sobe com defaults de desenvolvimento
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (mude com `HOST` e `PORT`). O `seed.py` recria os dados de exemplo no SQLite (`instance/tasks.db`): rode antes do primeiro boot, senão as listagens voltam vazias.

## Configuração

Todas as variáveis estão em `.env.example`. As principais:

| Variável | Default | Uso |
|---|---|---|
| `SECRET_KEY` | aleatória a cada boot | Assina o token devolvido pelo `/login`. Obrigatória com `ENV=production` |
| `ADMIN_TOKEN` | vazio | Token do header `X-Admin-Token` nas rotas administrativas |
| `DEBUG` | `false` | Debugger do Flask; nunca ligue em rede pública |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `CORS_ORIGINS` | `*` | Origens liberadas, separadas por vírgula |
| `SMTP_*` | vazio | Notificação de task atribuída; vazio só registra no log |

## Rotas administrativas

`GET /users`, `GET /users/<id>`, `PUT /users/<id>`, `DELETE /users/<id>`, `GET /reports/summary` e `GET /reports/user/<id>` exigem credencial administrativa, assim como `POST /users` com `role` diferente de `user`. Sem credencial respondem 403. Duas formas aceitas:

```bash
# token administrativo da configuração
curl -H "X-Admin-Token: $ADMIN_TOKEN" http://127.0.0.1:5000/reports/summary

# token do login de um usuário com role admin
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login -H 'Content-Type: application/json' \
  -d '{"email": "joao@email.com", "password": "1234"}' | python -c 'import json,sys; print(json.load(sys.stdin)["token"])')
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:5000/users
```

Sem `ADMIN_TOKEN` definido, o header `X-Admin-Token` é sempre recusado e só o Bearer de admin funciona.

## Estrutura

```
app.py              entry point (python app.py)
app_factory.py      create_app(): config, banco, blueprints, error handlers
config/settings.py  configuração lida do ambiente
database.py         instância do SQLAlchemy e helper de commit
models/             entidades, validação e serialização
controllers/        fluxo de cada ação
services/           relatórios agregados e notificação por e-mail
routes/             blueprints (camada HTTP)
middlewares/        autenticação administrativa e tratamento de erro
utils/              erros de domínio e helpers de data
```
