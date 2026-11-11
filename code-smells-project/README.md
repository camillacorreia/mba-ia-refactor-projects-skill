# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

Também funciona com o CLI do Flask: `flask --app app run --port 5000`.

## Configuração

Tudo vem de variáveis de ambiente, com defaults de desenvolvimento. Veja `.env.example`:

| Variável | Default | Uso |
|---|---|---|
| `APP_ENV` | `desenvolvimento` | Com `producao`, `SECRET_KEY` vira obrigatória |
| `SECRET_KEY` | aleatória por boot | Chave do Flask |
| `DEBUG` | `false` | Debugger do Werkzeug (nunca ligue exposto na rede) |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `CORS_ORIGINS` | `*` | Origens permitidas, separadas por vírgula |
| `ADMIN_TOKEN` | vazio | Libera `POST /admin/reset-db` com header `X-Admin-Token`; vazio responde 403 |

## Estrutura

```
app.py                 entry point (cria a app via create_app)
src/app.py             composition root: config, banco, serviços, blueprints, error handlers
src/config/            leitura do ambiente
src/database.py        conexão por requisição, schema e seed
src/models/            SQL parametrizado, validação e serialização por entidade
src/services/          casos de uso: pedido, relatório, notificação
src/controllers/       orquestração de cada ação
src/views/             blueprints com as rotas
src/middlewares/       error handler central e autenticação admin
```
