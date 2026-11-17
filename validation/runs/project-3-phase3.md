# Fase 3: task-manager-api (projeto 3)

Saída da Fase 3 da skill `/refactor-arch` depois da resposta `y`, retomando a sessão das Fases 1 e 2 com `claude -p "y" --resume <sessão>`. 5.8 min, 21 turnos. Segunda execução, com o AP-04 corrigido.

A refatoração terminou e a validação passou: 22 de 22 rotas respondem como antes, e as diferenças são só as mudanças intencionais listadas abaixo. Não fiz commit nem mexi no stage do git; tudo está como mudança não staged na working tree.

Um finding da auditoria estava errado: o AP-10 dizia que apagar uma categoria deixava tasks órfãs. O banco da linha de base mostra que não deixa, porque o backref do ORM já zera o `category_id`. A correção que entrou só torna isso explícito e numa transação, sem mudar o comportamento.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                      # entry point: app = create_app(settings); python app.py
├── app_factory.py              # composition root: config, CORS, banco, blueprints, error handlers, NotificationService
├── .env.example
├── README.md
├── requirements.txt
├── seed.py
├── config/
│   └── settings.py             # Settings lida do ambiente (.env opcional)
├── database.py                 # db, commit() com rollback, PRAGMA foreign_keys
├── models/
│   ├── task.py                 # constantes, validação, is_overdue, overdue_filter, to_dict
│   ├── user.py                 # hash scrypt + migração MD5, roles, validação de e-mail/senha
│   └── category.py             # validação de nome e cor
├── controllers/
│   ├── common.py
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── services/
│   ├── report_service.py       # agregações com GROUP BY
│   └── notification_service.py # SMTP injetado, no-op sem config
├── routes/                     # camada HTTP (views)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py
│   ├── report_routes.py
│   └── system_routes.py
├── middlewares/
│   ├── auth.py                 # require_admin, issue_token, verify_token
│   └── error_handler.py
└── utils/
    ├── errors.py               # ValidationError, NotFoundError, ForbiddenError...
    └── helpers.py              # utc_now, calculate_percentage

## Changes by Finding
[CRITICAL] Rotas privilegiadas sem autenticação (AP-04) -> @require_admin (X-Admin-Token comparado com hmac.compare_digest, ou Bearer de usuário admin) em GET/PUT/DELETE /users/<id>, GET /users, /reports/summary e /reports/user/<id>; POST /users com role diferente de "user" exige credencial; login emite token assinado com itsdangerous (expira em TOKEN_MAX_AGE_SECONDS) no lugar de "fake-jwt-token-<id>"
[CRITICAL] Hash de senha nas respostas (AP-06) -> password removido de User.to_dict()
[CRITICAL] MD5 sem salt (AP-05) -> werkzeug generate_password_hash (scrypt); MD5 legado aceito uma vez no login e regravado em scrypt
[CRITICAL] Segredos hardcoded (AP-01) -> SECRET_KEY, ADMIN_TOKEN e SMTP_* lidos do ambiente; SECRET_KEY aleatória em dev e obrigatória com ENV=production
[HIGH] Regra de negócio nas rotas (AP-07) -> rotas de 2-3 linhas; fluxo em controllers/, regras nos models, relatórios em services/report_service.py; CRUD de categorias movido para routes/category_routes.py com os mesmos caminhos
[HIGH] Debug exposto e config fixa (AP-11) -> DEBUG=false, HOST=127.0.0.1, PORT, DATABASE_URL e CORS_ORIGINS vindos do ambiente
[HIGH] Sem composition root (AP-09) -> create_app() em app_factory.py; NotificationService recebe config/smtp_factory por injeção, sem lista global de notificações, e passa a ser chamado quando uma task é atribuída
[HIGH] Exclusão de categoria e órfãs (AP-10) -> UPDATE explícito de category_id = NULL e DELETE na mesma transação, delete_user em lote, PRAGMA foreign_keys=ON. Correção do relatório: a linha de base mostrou que o backref do ORM já zerava category_id, então o impacto descrito estava exagerado
[MEDIUM] N+1 (AP-12) -> joinedload em /tasks, subquery de contagem em /users, GROUP BY em /categories, /tasks/stats e /reports/summary
[MEDIUM] Validação (AP-13) -> validadores únicos no model para create e update; prioridade e título com tipo errado, ?priority=x e cor inválida respondem 400
[MEDIUM] Duplicação de atraso e serialização (AP-14) -> Task.is_overdue()/overdue_filter() como implementação única; to_dict com flags e to_summary_dict
[MEDIUM] Erro genérico (AP-15) -> erros de domínio + error handler global; zero except sem tipo
[MEDIUM] datetime.utcnow() (AP-16) -> utc_now() naive em UTC em models, serviços e seed
[MEDIUM] Query.get() (AP-16) -> db.session.get(); SQLAlchemy==2.1.8 fixado no requirements
[LOW] Magic numbers (AP-18) -> constantes nomeadas em models/task.py, user.py e category.py
[LOW] Nomes ruins (AP-19) -> renomeados internamente (p1..p5, t, u, c, td no seed), campos da API intactos
[LOW] print (AP-20) -> logging por módulo; prints restantes só no seed.py (saída de CLI)
[LOW] Código morto (AP-21) -> imports e helpers sem uso removidos; marshmallow e requests saíram do requirements

## Intentional Behavior Changes
- GET /users, GET /users/<id>, PUT /users/<id>, DELETE /users/<id>, GET /reports/summary e GET /reports/user/<id>: 200 -> 403 sem credencial; com X-Admin-Token ou Bearer de admin respondem como antes
- POST /users com role "admin" ou "manager" sem credencial: 201 -> 403
- Bearer de usuário que não é admin em rota administrativa: 403
- Campo "password" sumiu de GET /users/<id>, POST/PUT /users e do "user" do /login
- "token" do /login agora é assinado e expira, no lugar de "fake-jwt-token-<id>"
- POST /tasks com "priority": "alta" e GET /tasks/search?priority=alta: 500 -> 400 {"error": ...}
- POST/PUT /categories com cor fora do formato #RRGGBB, nome vazio no PUT ou PUT sem corpo JSON: 400 (antes aceitava, ou dava 500 sem corpo)
- PUT /tasks com data inválida usa a mesma mensagem do POST ("Formato de data inválido. Use YYYY-MM-DD")
- Falhas inesperadas devolvem {"error": "Erro interno"} (antes cada rota tinha uma mensagem própria, mesmo status 500)

## Validation
  ✓ Application boots without errors (PORT=<livre> ADMIN_TOKEN=... .venv/bin/python -W always app.py, após python seed.py; nenhum traceback ou DeprecationWarning no log)
  ✓ All endpoints respond as before (22/22 routes, 59 requisições: 47 iguais, 12 DIFF intencionais: 10x 403 de AP-04, 2x 500->400 de AP-13; payload de 13 GETs comparado campo a campo com o original: idêntico)
  ✓ Anti-pattern re-scan: 2 remaining (hashlib.md5 em models/user.py:56, usado só para migrar hash legado; print em seed.py:95-98, saída de CLI)

## How to Run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # opcional
python seed.py
python app.py           # http://127.0.0.1:5000
curl -H "X-Admin-Token: $ADMIN_TOKEN" http://127.0.0.1:5000/reports/summary

## Validation Checklist
### Fase 1: Análise
- ✓ Linguagem detectada corretamente (Python, requirements.txt, 3.14.6 no .venv)
- ✓ Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
- ✓ Domínio descrito corretamente (tasks, users, categories, relatórios)
- ✓ Número de arquivos condiz (15 .py, 1158 linhas, conferido com wc -l)
### Fase 2: Auditoria
- ✓ Relatório segue o template (blocos, Summary 4/4/6/4 = Total 18)
- ✓ Cada finding tem arquivo e linhas exatos (confirmados com grep -n); ✗ parcial no AP-10: impacto exagerado, corrigido acima
- ✓ Findings ordenados CRITICAL -> LOW
- ✓ Mínimo de 5 findings (18)
- ✓ APIs deprecated incluídas (utcnow e Query.get, confirmadas por warnings no log da linha de base)
- ✓ Pausou e pediu confirmação antes da Fase 3
### Fase 3: Refatoração
- ✓ Estrutura MVC (models/, controllers/, routes/ como views, services/, middlewares/)
- ✓ Configuração extraída (config/settings.py, .env.example, re-scan AP-01/AP-11 vazio)
- ✓ Models abstraem dados e regras (validação, is_overdue, serialização)
- ✓ Routes separadas e finas (só delegam ao controller)
- ✓ Controllers concentram o fluxo
- ✓ Error handling centralizado (middlewares/error_handler.py, zero except sem tipo)
- ✓ Entry point claro (python app.py, seed.py segue importando app e db)
- ✓ Aplicação inicia sem erros
- ✓ Endpoints originais respondem corretamente (22/22, diferenças só as intencionais)
================================
```

Para conferir a migração do MD5, criei num banco em memória um usuário com o hash antigo. O login funcionou, o hash virou scrypt e o segundo login também passou. Um token forjado `fake-jwt-token-1` agora recebe 403. Os artefatos da validação (spec, before/after e logs) ficaram em `$TMPDIR/refactor-arch-task-manager-api`, fora do repositório.
