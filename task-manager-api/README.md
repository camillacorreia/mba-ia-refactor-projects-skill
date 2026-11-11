# task-manager-api

API de Task Manager em Python/Flask (tasks, usuários e categorias, com busca, estatísticas e relatórios). Usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py      # apaga e recria os dados de exemplo
.venv/bin/python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite fica em `instance/tasks.db`; rode o `seed.py` antes do primeiro boot, senão as listagens voltam vazias. Atenção: o seed apaga todos os registros existentes.

Também funciona com `flask --app app run --port 5000`.

## Configuração

Tudo vem de variáveis de ambiente ou de um arquivo `.env` na raiz (veja `.env.example`). Nenhuma é obrigatória em desenvolvimento.

| Variável | Padrão | Uso |
|---|---|---|
| `ENV` | `development` | Em `production`, `SECRET_KEY` vira obrigatória |
| `SECRET_KEY` | aleatória por boot | Chave de sessão do Flask |
| `DEBUG` | `false` | Liga o debugger do Werkzeug; nunca use exposto na rede |
| `HOST` | `127.0.0.1` | Use `0.0.0.0` para aceitar conexões externas |
| `PORT` | `5000` | Porta do `python app.py` |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI do SQLAlchemy |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `LOG_LEVEL` | `INFO` | Nível do logging |

## Estrutura

```
app.py              entry point (python app.py)
app_factory.py      create_app(): config, banco, blueprints, error handlers
config/settings.py  leitura do ambiente
database.py         instância do SQLAlchemy e criação do schema
models/             entidades, regras de domínio, validação de campos e consultas
controllers/        fluxo de cada ação: entrada, chamada ao model/serviço, status
services/           casos de uso entre entidades (relatórios)
routes/             blueprints: só mapeiam método + caminho para o controller
middlewares/        error handler central (erros sempre em JSON {"error": ...})
utils/              erros de domínio e helpers de data/porcentagem
seed.py             dados de exemplo
```

## Senhas

Senhas são gravadas com scrypt (Werkzeug). Bancos criados antes da refatoração têm hashes MD5: eles continuam aceitos no login e são regravados em scrypt no primeiro login bem-sucedido de cada usuário.

## Limitações conhecidas

Não há autenticação real. O `token` devolvido por `POST /login` não é verificado por nenhuma rota, e todas as rotas de escrita (incluindo `DELETE /users/<id>` e troca de `role`) estão abertas.
