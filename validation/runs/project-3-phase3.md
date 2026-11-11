# Fase 3: task-manager-api (projeto 3)

Saída da Fase 3 da skill `/refactor-arch` depois da resposta `y`, retomando a sessão das Fases 1 e 2 com `claude -p "y" --resume <sessão>`. 6.7 min, 22 turnos, US$ 2.78.

Terminei a validação e estou fechando o resumo. Antes disso, um problema que eu causei e que você precisa saber.

Pra remover o `services/notification_service.py` eu usei `git rm`, que deixa a remoção no stage. Outra sessão rodando neste mesmo repositório fez o commit `07761fc` ("Refatora ecommerce-api-legacy...") às 20:17, e esse commit levou junto a remoção do `task-manager-api/services/notification_service.py`. Então hoje esse arquivo está apagado num commit que é sobre outro projeto. Não mexi no histórico. Se quiser separar, dá pra restaurar o arquivo com `git checkout 07761fc~1 -- task-manager-api/services/notification_service.py` e apagar de novo no commit desta refatoração. O resto do que fiz aqui não está staged.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                      # entry point: python app.py
├── app_factory.py              # create_app(): config, banco, blueprints, error handler
├── .env.example
├── README.md
├── requirements.txt
├── seed.py
├── database.py                 # db + init_db (create_all)
├── config/
│   └── settings.py
├── models/
│   ├── __init__.py             # registra os 3 mappers
│   ├── task.py                 # regras (is_overdue), validadores, constantes, consultas
│   ├── user.py                 # hash scrypt + migração MD5, to_dict sem senha
│   └── category.py
├── controllers/
│   ├── common.py
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── services/
│   └── report_service.py
├── routes/
│   ├── system_routes.py        # / e /health
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py      # /categories saiu de report_routes
│   └── report_routes.py
├── middlewares/
│   └── error_handler.py
└── utils/
    ├── errors.py
    └── helpers.py              # utcnow, calculate_percentage

## Changes by Finding
[CRITICAL] Hash de senha exposto -> password saiu de User.to_dict(), que é a única serialização de usuário
[CRITICAL] MD5 sem salt -> scrypt via werkzeug; um MD5 legado é aceito uma vez e regravado no login (testado numa cópia do seu banco)
[CRITICAL] Segredos hardcoded -> SECRET_KEY/DATABASE_URL vêm do ambiente via config/settings.py; a credencial SMTP saiu junto com o serviço morto
[CRITICAL] Nenhuma autenticação -> not fixed: muda o contrato de 15 rotas de escrita, fica como decisão de produto (documentado no README)
[HIGH] Regra de negócio nos handlers -> rotas de 1 linha, controllers orquestram, regras e validação nos models, agregação em report_service
[HIGH] Debug exposto e CORS aberto -> DEBUG=false e HOST=127.0.0.1 por padrão; CORS_ORIGINS configurável (padrão * como antes)
[HIGH] Sem composition root -> create_app(settings) em app_factory.py; o seed usa a factory
[HIGH] Exclusão sem integridade -> cascade explícito em User.tasks; política de categoria declarada. Correção do relatório: o "órfão" de categoria não existia, o backref já anulava o FK (a linha de base mostrou category_id: null)
[MEDIUM] N+1 -> joinedload em /tasks; GROUP BY em /users, /categories, /tasks/stats e /reports/summary
[MEDIUM] Validação ausente -> validadores únicos por campo; tipo errado agora dá 400 (prioridade, título, active, cor, tags, query params)
[MEDIUM] Duplicação -> Task.is_overdue é a única regra de atraso; to_dict/to_summary_dict; regex de email única
[MEDIUM] except genérico -> error handler global em JSON; zero except no código da aplicação
[MEDIUM] datetime.utcnow -> utils.helpers.utcnow() (naive UTC, mesmo formato de saída)
[MEDIUM] Query.get -> db.session.get / db.select
[LOW] Código morto -> imports e helpers sem uso removidos, NotificationService removido, marshmallow e requests fora do requirements
[LOW] Magic numbers -> constantes nos models (VALID_STATUSES, MIN/MAX_*, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS...)
[LOW] print -> logging (seed.py mantém print por ser script de CLI)
[LOW] Nomes curtos -> p1..p5, u, t, c, cat_data substituídos; campos da API intactos

## Intentional Behavior Changes
- `password` não aparece mais em GET /users/<id>, POST /users, PUT /users/<id> e POST /login (o resto da resposta é igual)
- Entrada de tipo errado que dava 500 HTML agora dá 400 JSON: priority não numérica, ?priority=x na busca, PUT /categories sem corpo
- Todo erro do framework (404 de rota, 405, 415, JSON malformado) sai como {"error": ...} em vez de HTML
- Novas rejeições com 400: active não booleano, cor fora de #RRGGBB, nome vazio no PUT de user/categoria, tags com item não string
- Erros 500 de commit usam a mensagem genérica "Erro interno" em vez de "Erro ao criar task" etc.
- python app.py escuta em 127.0.0.1 com debug desligado (HOST=0.0.0.0 e DEBUG=true restauram)

## Validation
  ✓ Application boots without errors (PORT=<p> python app.py e flask --app app run: 0 tracebacks, 0 deprecation; antes eram 113 avisos)
  ✓ All endpoints respond as before (22/22 rotas, 52 requisições: 49 status iguais, 3 de 500 para 400 intencionais; 9 corpos diferentes, todos listados acima)
  ✓ Anti-pattern re-scan: 2 remaining (token falso do login, AP-04 não corrigido; hashlib.md5 usado só para conferir hash legado antes de regravar)

## How to Run
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py      # apaga e recria os dados
.venv/bin/python app.py       # http://127.0.0.1:5000; config opcional em .env (ver .env.example)

## Validation Checklist
### Fase 1: Análise
✓ Linguagem detectada corretamente (Python, requirements.txt e 15 .py)
✓ Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
✓ Domínio descrito corretamente (tasks, users, categories, relatórios)
✓ Número de arquivos condiz (15 .py, ~1158 linhas, conferido com wc)
### Fase 2: Auditoria
✓ Relatório segue o template
✓ Cada finding tem arquivo e linhas exatos (conferidos com cat -n e grep -n)
✓ Ordenado de CRITICAL a LOW
✓ Mínimo de 5 findings (18)
✓ APIs deprecated incluídas (2, confirmadas com -W always)
✓ Pausou e pediu confirmação antes da Fase 3
✗ Precisão: o finding AP-10 exagerou a parte de categorias; a linha de base mostrou que o FK já era anulado
### Fase 3: Refatoração
✓ Estrutura MVC (models / controllers / routes, mais services e middlewares)
✓ Config extraída (config/settings.py; o re-scan não acha segredo literal)
✓ Models abstraem dados (consultas e escrita só nos models e no report_service)
✓ Routes separadas (só fazem o mapeamento de rota para controller)
✓ Controllers concentram o fluxo
✓ Error handling centralizado (middlewares/error_handler.py)
✓ Entry point claro (app.py -> app_factory.create_app)
✓ Aplicação inicia sem erros
✓ Endpoints originais respondem corretamente (diferenças todas intencionais)
================================
```

Sobre a validação: toda requisição de teste rodou em cópias do código em `/tmp/refactor-arch-task-manager-api`, porque o `seed.py` apaga o banco. O seu `instance/tasks.db` não foi tocado, e tem um backup dele nessa mesma pasta. Ele ainda tem hashes MD5, que vão sendo convertidos pra scrypt conforme cada usuário faz login.

Não fiz commit. O `.venv/` que criei está no `.gitignore`.
