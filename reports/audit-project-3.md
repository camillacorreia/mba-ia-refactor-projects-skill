# Auditoria: task-manager-api (projeto 3)

Saída das Fases 1 e 2 da skill `/refactor-arch`, executada com `claude -p "/refactor-arch"` (Claude Code 2.1.326, modelo claude-opus-5-5) dentro de `task-manager-api/`, sem edição. Sessão 03c8603e-eadb-4560-b8e3-e81a251292e7, 121 s. Esta é a segunda execução, feita depois que a skill passou a exigir a correção do AP-04 com token administrativo; a primeira está no histórico do git (commit 694c5db).

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; .venv local com 3.14.6)
Framework:     Flask 3.0.0 (flask==3.0.0, Blueprints)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0
Database:      SQLite (`sqlite:///tasks.db`) via ORM Flask-SQLAlchemy (SQLAlchemy 2.1.8 instalado, sem pin)
Domain:        Gerenciador de tarefas (tasks, users, categories), com busca, estatísticas e relatórios de produtividade por usuário
Architecture:  Camadas parciais: existem `models/`, `routes/`, `services/`, `utils/`, mas regra de negócio, serialização e cálculo de atraso estão nas rotas, o CRUD de categorias mora em `report_routes.py`, `NotificationService` e quase todo `utils/helpers.py` não são usados, e a config está hardcoded em `app.py`
Source files:  15 files analyzed (~1158 lines; 3 `__init__.py` triviais)
Entry point:   app.py (`python seed.py` e depois `python app.py`, porta 5000)
DB tables:     users (User), categories (Category), tasks (Task); schema por `db.create_all()` no import de app.py:30-31
Endpoints:     22 routes
================================

| # | Método | Caminho | Handler | Arquivo:linha |
|---|---|---|---|---|
| 1 | GET | /health | health | app.py:22 |
| 2 | GET | / | index | app.py:26 |
| 3 | GET | /tasks | get_tasks | routes/task_routes.py:11 |
| 4 | GET | /tasks/<int:task_id> | get_task | routes/task_routes.py:65 |
| 5 | POST | /tasks | create_task | routes/task_routes.py:85 |
| 6 | PUT | /tasks/<int:task_id> | update_task | routes/task_routes.py:156 |
| 7 | DELETE | /tasks/<int:task_id> | delete_task | routes/task_routes.py:225 |
| 8 | GET | /tasks/search | search_tasks | routes/task_routes.py:240 |
| 9 | GET | /tasks/stats | task_stats | routes/task_routes.py:273 |
| 10 | GET | /users | get_users | routes/user_routes.py:10 |
| 11 | GET | /users/<int:user_id> | get_user | routes/user_routes.py:27 |
| 12 | POST | /users | create_user | routes/user_routes.py:42 |
| 13 | PUT | /users/<int:user_id> | update_user | routes/user_routes.py:92 |
| 14 | DELETE | /users/<int:user_id> | delete_user | routes/user_routes.py:134 |
| 15 | GET | /users/<int:user_id>/tasks | get_user_tasks | routes/user_routes.py:153 |
| 16 | POST | /login | login | routes/user_routes.py:185 |
| 17 | GET | /reports/summary | summary_report | routes/report_routes.py:12 |
| 18 | GET | /reports/user/<int:user_id> | user_report | routes/report_routes.py:103 |
| 19 | GET | /categories | get_categories | routes/report_routes.py:157 |
| 20 | POST | /categories | create_category | routes/report_routes.py:167 |
| 21 | PUT | /categories/<int:cat_id> | update_category | routes/report_routes.py:190 |
| 22 | DELETE | /categories/<int:cat_id> | delete_category | routes/report_routes.py:211 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (SQLite via Flask-SQLAlchemy)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Rotas privilegiadas sem autenticação, escalada de papel e token falso
ID: AP-04
File: routes/user_routes.py:210
Locations: routes/user_routes.py:10 (GET /users), routes/user_routes.py:27 (GET /users/<id>), routes/user_routes.py:52,71-78 (POST /users grava role do corpo), routes/user_routes.py:92,119-122 (PUT /users/<id> grava role do corpo), routes/user_routes.py:134 (DELETE /users/<id>), routes/report_routes.py:12 (GET /reports/summary), routes/report_routes.py:103 (GET /reports/user/<id>)
Description: login devolve 'token': 'fake-jwt-token-' + str(user.id), que nenhuma rota valida. Listagem e cadastro de qualquer usuário, alteração e exclusão de usuários e os relatórios globais não têm checagem de identidade. POST /users aceita {"role": "admin"} e grava direto em user.role.
Impact: Qualquer cliente anônimo cria um usuário admin, apaga qualquer usuário (com todas as tasks dele) e lê e-mails e métricas de todos. O "token" é previsível (fake-jwt-token-1 é o admin do seed).
Recommendation: Token administrativo via variável de ambiente (T-13) num decorator aplicado às rotas de gestão de usuários e relatórios, e no envio de role em POST/PUT /users. Login passa a devolver token assinado (itsdangerous com SECRET_KEY) no lugar do token fixo.

### [CRITICAL] Hash de senha (MD5) devolvido nas respostas da API
ID: AP-06
File: models/user.py:21
Locations: routes/user_routes.py:33 (GET /users/<id>), routes/user_routes.py:85 (POST /users), routes/user_routes.py:129 (PUT /users/<id>), routes/user_routes.py:209 (POST /login)
Description: User.to_dict() inclui 'password': self.password, e é a serialização usada no cadastro, na consulta, na atualização e no login.
Impact: Qualquer chamada a GET /users/1 devolve o hash MD5 sem salt do admin, que é revertido por rainbow table em segundos (o seed usa '1234').
Recommendation: Remover password de to_dict (T-12). Mudança intencional de contrato, registrada no resumo.

### [CRITICAL] Senha com MD5 sem salt
ID: AP-05
File: models/user.py:29
Locations: models/user.py:32
Description: set_password faz hashlib.md5(pwd.encode()).hexdigest() e check_password compara com o mesmo MD5.
Impact: Com AP-06, o hash vaza e a senha é recuperada trivialmente; mesmo sem vazamento, um dump do tasks.db expõe todas as senhas.
Recommendation: werkzeug.security generate_password_hash/check_password_hash (T-06), aceitando hash MD5 legado no login e regravando no formato novo.

### [CRITICAL] Segredos hardcoded no código
ID: AP-01
File: app.py:13
Locations: services/notification_service.py:7-10
Description: app.config['SECRET_KEY'] = 'super-secret-key-123'; NotificationService tem email_user = 'taskmanager@gmail.com' e email_password = 'senha123'. Senhas do seed (seed.py:19,26,33) são de dev e ficam só no seed.
Impact: Quem lê o repositório assina sessões/tokens com a SECRET_KEY e usa a conta SMTP.
Recommendation: Config em config/settings.py lida de variáveis de ambiente com .env.example (T-01); SMTP recebido por injeção.

### [HIGH] Regra de negócio e persistência dentro das rotas
ID: AP-07
File: routes/task_routes.py:86-154
Locations: routes/task_routes.py:157-223 (update_task), routes/user_routes.py:43-90 (create_user), routes/report_routes.py:13-101 (summary_report, 88 linhas), routes/report_routes.py:104-155, routes/report_routes.py:157-223 (CRUD de categorias dentro de report_routes)
Description: create_task valida título, status, prioridade, existência de user/categoria, converte data e tags, faz db.session.add/commit e monta a resposta no mesmo corpo. summary_report faz 13 consultas e todo o cálculo de relatório na rota. O CRUD de categorias está registrado no blueprint de relatórios.
Impact: Nenhuma regra é testável sem subir HTTP; create e update divergem (ver AP-13); mudar uma regra exige editar várias rotas.
Recommendation: Rotas finas, controllers por entidade, regras nos models e um services/report_service.py (T-04, T-03); categorias ganham routes/category_routes.py mantendo os mesmos caminhos.

### [HIGH] Debug do Werkzeug exposto e configuração insegura fixa no código
ID: AP-11
File: app.py:34
Locations: app.py:11-12, app.py:15
Description: app.run(debug=True, host='0.0.0.0', port=5000); CORS(app) liberado para qualquer origem; URI do banco fixa em 'sqlite:///tasks.db'.
Impact: O console do debugger em 0.0.0.0 permite execução remota de código por qualquer um na rede.
Recommendation: DEBUG, HOST, PORT, DATABASE_URL e CORS_ORIGINS vindos do ambiente com padrões seguros (T-01).

### [HIGH] Sem composition root e serviço que instancia a própria infraestrutura
ID: AP-09
File: app.py:9
Locations: app.py:30-31, services/notification_service.py:5-10, services/notification_service.py:15, seed.py:2
Description: app = Flask(__name__) e db.create_all() rodam no import do módulo; NotificationService cria smtplib.SMTP dentro de send_email e guarda self.notifications = [] em memória (estado mutável, AP-08, embora hoje nunca seja instanciado).
Impact: Não dá para subir a app com outro banco para teste; importar app.py já cria tasks.db no diretório corrente; o serviço de e-mail não é substituível por fake.
Recommendation: create_app() em app_factory com config injetada, app.py só chamando a factory (T-05); NotificationService recebendo config SMTP no construtor.

### [HIGH] Exclusão de categoria deixa tasks órfãs
ID: AP-10
File: routes/report_routes.py:211-223
Locations: models/task.py:13-14, routes/user_routes.py:140-145
Description: delete_category faz db.session.delete(cat) sem tratar tasks com category_id apontando para ela; as FKs não têm ondelete e o SQLite não aplica foreign keys por padrão. delete_user apaga as tasks uma a uma num loop antes do try.
Impact: Depois de DELETE /categories/1, as tasks continuam com category_id=1 e /tasks devolve category_name null para um id que não existe; um POST /categories novo pode reaproveitar o id e "herdar" tasks.
Recommendation: Na exclusão da categoria, desvincular tasks (category_id = NULL) na mesma transação; delete_user com delete em lote dentro de uma transação; PRAGMA foreign_keys=ON (T-09).

### [MEDIUM] Consultas N+1 em listagens e relatórios
ID: AP-12
File: routes/task_routes.py:41-57
Locations: routes/user_routes.py:22, routes/report_routes.py:55-56, routes/report_routes.py:163, routes/report_routes.py:15-28, routes/task_routes.py:275-279
Description: get_tasks chama User.query.get e Category.query.get por task; get_users faz len(u.tasks) lazy por usuário; summary_report consulta tasks por usuário e faz 12 COUNTs separados; get_categories conta tasks por categoria no loop.
Impact: GET /tasks com 1000 tasks faz até 2001 consultas.
Recommendation: joinedload/selectinload e agregações com GROUP BY (T-07).

### [MEDIUM] Validação ausente, inconsistente e duplicada
ID: AP-13
File: routes/task_routes.py:113
Locations: routes/task_routes.py:96,182, routes/task_routes.py:261,264, routes/report_routes.py:196-197, routes/report_routes.py:178-180, routes/user_routes.py:61,106, routes/task_routes.py:110,177, models/task.py:39, utils/helpers.py:75,110
Description: priority < 1 com {"priority": "alta"} lança TypeError (500); len(title) com título numérico idem; int(priority) na busca com ?priority=x dá 500; update_category faz 'name' in data com data None; color não é validado apesar de is_valid_color existir. A lista de status aparece em 5 lugares e a regex de e-mail em 3.
Impact: Input malformado vira 500 em vez de 400; regras divergem entre create e update.
Recommendation: Validação centralizada nos models com constantes únicas (T-04, T-14), devolvendo 400 nos casos que hoje caem em 500.

### [MEDIUM] Cálculo de atraso e serialização duplicados
ID: AP-14
File: routes/task_routes.py:30-39
Locations: routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-36, routes/report_routes.py:132-135, routes/task_routes.py:17-28, routes/user_routes.py:15-23, routes/user_routes.py:162-169
Description: O if aninhado "due_date < utcnow e status não é done/cancelled" aparece 6 vezes enquanto Task.is_overdue() (models/task.py:50) existe e não é chamado; get_tasks remonta à mão os campos de Task.to_dict().
Impact: Mudar a regra de atraso exige 7 edições; já existe risco de divergência entre /tasks/stats e /reports/summary.
Recommendation: Usar Task.is_overdue() e serializadores no model com variantes (T-12, T-04).

### [MEDIUM] Tratamento de erro genérico, sem handler global
ID: AP-15
File: routes/task_routes.py:62
Locations: routes/task_routes.py:137,151,204,221,236, routes/user_routes.py:87,130,149, routes/report_routes.py:186,207,221, utils/helpers.py:46,49,88
Description: except: sem tipo em 11 pontos; get_tasks embrulha a rota inteira em try/except: e devolve 'Erro interno' escondendo qualquer bug; cada rota repete o próprio try/rollback.
Impact: Erros reais somem sem log; 404 e 400 viram 500 quando o except pega a exceção errada.
Recommendation: Exceções de domínio e error handler global registrado no create_app (T-08).

### [MEDIUM] datetime.utcnow() deprecated
ID: AP-16
File: models/task.py:52
Locations: models/task.py:15-16, models/user.py:14, models/category.py:11, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,71,133, utils/helpers.py:38, services/notification_service.py:35, seed.py:66,67,69,70,74
Description: datetime.utcnow() está deprecated desde Python 3.12 e o .venv roda 3.14.6.
Impact: DeprecationWarning em cada chamada e remoção futura.
Recommendation: Helper utc_now() que devolve datetime.now(timezone.utc) sem tzinfo, preservando o formato naive gravado no SQLite e devolvido nos campos de data (T-11).

### [MEDIUM] Model.query.get() legado do SQLAlchemy 2.x
ID: AP-16
File: routes/task_routes.py:67
Locations: routes/task_routes.py:42,51,117,122,158,188,195,227, routes/user_routes.py:29,94,136,155, routes/report_routes.py:105,192,213
Description: 16 chamadas a X.query.get(id), API legada no SQLAlchemy 2.x (2.1.8 instalado, sem pin no requirements).
Impact: LegacyAPIWarning e quebra numa futura major.
Recommendation: db.session.get(Model, id) (T-11) e pin de SQLAlchemy no requirements.

### [LOW] Magic numbers e strings ignorando constantes que já existem
ID: AP-18
File: routes/task_routes.py:96-100
Locations: routes/task_routes.py:104,113,167-169,182, routes/user_routes.py:64,71,115,120, routes/report_routes.py:45,129,180, utils/helpers.py:110-116
Description: 3 e 200 para título, 1 e 5 para prioridade, 4 para senha, priority <= 2 como "alta prioridade", 7 dias, '#000000'; utils/helpers.py:110-116 define VALID_STATUSES, MAX_TITLE_LENGTH, MIN_PASSWORD_LENGTH e nenhum arquivo usa.
Impact: Limites mudam num lugar e não em outro.
Recommendation: Constantes de domínio num módulo único e usadas pelos models (T-14).

### [LOW] Nomes pouco descritivos
ID: AP-19
File: routes/report_routes.py:24-28
Locations: routes/report_routes.py:33,55, routes/task_routes.py:16,51, models/task.py:45, models/user.py:27, seed.py:16
Description: p1..p5, t, u, c, cat, p, pwd, d.
Impact: Leitura mais lenta das regras de relatório.
Recommendation: Renomear internamente mantendo os campos da API (T-14).

### [LOW] print no lugar de logging
ID: AP-20
File: routes/task_routes.py:149
Locations: routes/task_routes.py:153,219,234, routes/user_routes.py:83,89,147, utils/helpers.py:39,41, services/notification_service.py:21,24
Description: print(f"Task criada: {task.id} - {task.title}"), print(f"ERRO: {str(e)}") etc. seed.py:93-96 é CLI e pode continuar com print.
Impact: Sem nível nem contexto, nada vai para agregador de log.
Recommendation: logging com logger por módulo (T-15).

### [LOW] Imports, funções e serviços mortos
ID: AP-21
File: app.py:7
Locations: routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, utils/helpers.py:19-108, services/notification_service.py:4, models/task.py:38-60, models/user.py:34, requirements.txt:4-5
Description: import os, sys, json, datetime em app.py (só datetime é usado); json, os, sys, time em task_routes; hashlib, json em user_routes; format_date, calculate_percentage, json em report_routes. validate_email, sanitize_string, generate_id, log_action, parse_date, is_valid_color, process_task_data sem chamador; NotificationService nunca instanciado; Task.validate_status/validate_priority/is_overdue e User.is_admin sem uso; marshmallow e requests no requirements sem import.
Impact: Ruído e dependências instaladas sem motivo.
Recommendation: Remover o que é morto e passar a usar o que resolve duplicação (is_overdue, validadores, constantes).

## Deprecated APIs
datetime.utcnow() (Python 3.12+), 23 ocorrências, ver finding AP-16.
Model.query.get() (SQLAlchemy 2.x), 16 ocorrências, ver finding AP-16.

================================
Total: 18 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
