# Auditoria: task-manager-api (projeto 3)

Saída das Fases 1 e 2 da skill `/refactor-arch`, executada com `claude -p "/refactor-arch"` (Claude Code 2.1.322, modelo claude-opus-5-5) dentro de `task-manager-api/`, sem edição. Sessão f10f4699-c309-4857-b7ba-59978b8e9785, 147 s.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; ambiente local 3.14.6)
Framework:     Flask 3.0.0 (flask==3.0.0)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0 (as três últimas não são importadas em lugar nenhum)
Database:      SQLite via ORM Flask-SQLAlchemy (SQLAlchemy 2.1.8 instalado), arquivo instance/tasks.db, schema por db.create_all() no import
Domain:        Gerenciador de tarefas (tasks, users, categories), com login, busca, estatísticas e relatórios de produtividade
Architecture:  Camadas parciais: existem models/, routes/, services/, utils/, mas validação, cálculo de atraso, agregação de relatório e serialização estão nos handlers; services/ e utils/ quase não são usados
Source files:  15 files analyzed (~1158 lines; 3 __init__.py, sendo 3 vazios e 1 de reexportação)
Entry point:   app.py (`python seed.py` e depois `python app.py`, porta 5000)
DB tables:     users (User), tasks (Task), categories (Category)
Endpoints:     22 routes
================================
```

| # | Método | Caminho | Handler | Arquivo:linha |
|---|---|---|---|---|
| 1 | GET | `/` | index | app.py:26 |
| 2 | GET | `/health` | health | app.py:22 |
| 3 | GET | `/tasks` | get_tasks | routes/task_routes.py:11 |
| 4 | GET | `/tasks/<int:task_id>` | get_task | routes/task_routes.py:65 |
| 5 | POST | `/tasks` | create_task | routes/task_routes.py:85 |
| 6 | PUT | `/tasks/<int:task_id>` | update_task | routes/task_routes.py:156 |
| 7 | DELETE | `/tasks/<int:task_id>` | delete_task | routes/task_routes.py:225 |
| 8 | GET | `/tasks/search` | search_tasks | routes/task_routes.py:240 |
| 9 | GET | `/tasks/stats` | task_stats | routes/task_routes.py:273 |
| 10 | GET | `/users` | get_users | routes/user_routes.py:10 |
| 11 | GET | `/users/<int:user_id>` | get_user | routes/user_routes.py:27 |
| 12 | POST | `/users` | create_user | routes/user_routes.py:42 |
| 13 | PUT | `/users/<int:user_id>` | update_user | routes/user_routes.py:92 |
| 14 | DELETE | `/users/<int:user_id>` | delete_user | routes/user_routes.py:134 |
| 15 | GET | `/users/<int:user_id>/tasks` | get_user_tasks | routes/user_routes.py:153 |
| 16 | POST | `/login` | login | routes/user_routes.py:185 |
| 17 | GET | `/reports/summary` | summary_report | routes/report_routes.py:12 |
| 18 | GET | `/reports/user/<int:user_id>` | user_report | routes/report_routes.py:103 |
| 19 | GET | `/categories` | get_categories | routes/report_routes.py:157 |
| 20 | POST | `/categories` | create_category | routes/report_routes.py:167 |
| 21 | PUT | `/categories/<int:cat_id>` | update_category | routes/report_routes.py:190 |
| 22 | DELETE | `/categories/<int:cat_id>` | delete_category | routes/report_routes.py:211 |

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

### [CRITICAL] Hash de senha exposto em todas as respostas de usuário
ID: AP-06
File: models/user.py:21
Locations: routes/user_routes.py:33, routes/user_routes.py:85, routes/user_routes.py:129, routes/user_routes.py:209
Description: User.to_dict() inclui 'password': self.password, e esse dicionário volta em GET /users/<id>, POST /users, PUT /users/<id> e no corpo de POST /login ('user': user.to_dict()).
Impact: Qualquer cliente lê o hash de qualquer usuário com GET /users/1. Como o hash é MD5 sem salt (ver AP-05), as senhas do seed ('1234', 'abcd', 'pass') saem por lookup em rainbow table em segundos.
Recommendation: Remover password de to_dict e ter uma serialização pública única no model (T-12). Mudança intencional de contrato: o campo password some das respostas.

### [CRITICAL] Senha com MD5 sem salt
ID: AP-05
File: models/user.py:29
Locations: models/user.py:32
Description: set_password grava hashlib.md5(pwd.encode()).hexdigest() e check_password compara com == contra o mesmo MD5.
Impact: MD5 sem salt é reversível por tabela pré-computada; senhas iguais geram hashes iguais; a comparação com == não é de tempo constante.
Recommendation: Trocar por werkzeug.security.generate_password_hash/check_password_hash (já vem com o Flask), aceitando hashes MD5 legados no login e regravando com o novo algoritmo quando a senha confere (T-06).

### [CRITICAL] Segredos hardcoded no código
ID: AP-01
File: app.py:13
Locations: services/notification_service.py:7-10, app.py:11
Description: app.config['SECRET_KEY'] = 'super-secret-key-123'; NotificationService fixa email_user = 'taskmanager@gmail.com' e email_password = 'senha123' com host smtp.gmail.com. A URI do banco também é literal. As senhas de seed (seed.py:19,26,33) são de usuários fictícios e ficam como dado de desenvolvimento.
Impact: Quem tem acesso ao repositório tem a chave de assinatura de sessão do Flask e a credencial SMTP; trocar qualquer um exige deploy de código.
Recommendation: Mover para config lida de variáveis de ambiente (SECRET_KEY, DATABASE_URL, SMTP_*), com .env.example sem valores reais (T-01).

### [CRITICAL] Nenhuma autenticação, inclusive em rotas destrutivas e de troca de papel
ID: AP-04
File: routes/user_routes.py:134-151
Locations: routes/user_routes.py:119-122, routes/user_routes.py:210, routes/report_routes.py:211-223, routes/report_routes.py:12
Description: DELETE /users/<id> apaga o usuário e todas as tasks dele sem checar identidade; PUT /users/<id> aceita 'role': 'admin' de qualquer cliente; o login devolve 'fake-jwt-token-' + str(user.id), que nenhuma rota verifica e é adivinhável.
Impact: Um cliente anônimo promove a si mesmo a admin, apaga qualquer usuário e lê o relatório de produtividade de todos.
Recommendation: Adicionar autenticação por token assinado e checagem de papel nas rotas destrutivas (T-13). Isso muda o contrato de 15 rotas de escrita; a recomendação é tratar como decisão de produto e, se não aprovada, registrar como "not fixed" e manter o login como está.

### [HIGH] Regra de negócio e agregação dentro dos handlers
ID: AP-07
File: routes/report_routes.py:12-101
Locations: routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/report_routes.py:103-155, routes/user_routes.py:42-90
Description: summary_report tem 89 linhas com 12 contagens, cálculo de atraso, produtividade por usuário e montagem da resposta; create_task/update_task validam título, status, prioridade, data e tags inline e chamam db.session direto. CRUD de categorias mora em report_routes.py:157-223, num blueprint de relatórios.
Impact: Nada disso é testável sem subir Flask e banco; a mesma regra aparece com variações em cada rota (ver AP-14).
Recommendation: Criar controllers/serviços (task_service, user_service, report_service, category_service) e deixar as rotas só com parse de request e resposta; mover categorias para blueprint próprio mantendo as URLs (T-04, T-03).

### [HIGH] Debug do Werkzeug exposto e CORS aberto fixos no código
ID: AP-11
File: app.py:34
Locations: app.py:15
Description: app.run(debug=True, host='0.0.0.0', port=5000) e CORS(app) sem lista de origens.
Impact: O debugger interativo do Werkzeug em 0.0.0.0 permite execução de código remoto a partir de qualquer stack trace; qualquer site pode chamar a API pelo navegador da vítima.
Recommendation: Ler DEBUG, HOST, PORT e CORS_ORIGINS do ambiente, com debug desligado por padrão (T-01).

### [HIGH] Sem composition root: app, config e schema criados no import
ID: AP-09
File: app.py:9-31
Locations: seed.py:2, seed.py:11-14, services/notification_service.py:15
Description: app = Flask(__name__) no nível do módulo, URI fixa 'sqlite:///tasks.db' e db.create_all() rodando no import (app.py:30-31). seed.py importa esse mesmo app e começa com Task.query.delete() / User.query.delete(). NotificationService instancia smtplib.SMTP dentro do próprio método.
Impact: Não dá para criar uma app de teste com outro banco; importar app.py já cria tabelas; rodar o seed num ambiente apontado errado apaga dados reais, porque o alvo não é configurável.
Recommendation: create_app(config) em app/__init__.py, app.py só chama create_app() e mantém python app.py; seed usa create_app (T-05).

### [HIGH] Exclusão de categoria deixa tasks órfãs; relacionamentos sem cascata
ID: AP-10
File: routes/report_routes.py:211-223
Locations: models/task.py:20-21, routes/user_routes.py:140-145
Description: delete_category faz db.session.delete(cat) sem tratar tasks com aquele category_id; o SQLite não aplica FK por padrão, então as tasks ficam apontando para um id inexistente. Os relacionamentos db.relationship('User', backref='tasks') não declaram cascade, e delete_user apaga tasks manualmente num laço.
Impact: Depois de DELETE /categories/1, GET /tasks mostra category_id: 1 com category_name: null, e PUT nessas tasks mantendo a categoria passa sem validação.
Recommendation: Declarar a política no model (desassociar category_id ao apagar categoria, cascade delete-orphan em User.tasks) e executar a exclusão numa transação única no serviço (T-09).

### [MEDIUM] Consultas N+1 em listagens e relatórios
ID: AP-12
File: routes/task_routes.py:42
Locations: routes/task_routes.py:51, routes/user_routes.py:22, routes/report_routes.py:56, routes/report_routes.py:163, routes/report_routes.py:15-28, routes/task_routes.py:275-279
Description: get_tasks faz User.query.get e Category.query.get para cada task; get_users acessa len(u.tasks) lazy por usuário; summary_report faz Task.query.filter_by(user_id=u.id).all() por usuário e 12 COUNT separados que um GROUP BY resolve; get_categories faz um count por categoria.
Impact: GET /tasks com 10 tasks dispara 21 queries; cresce linearmente com o volume.
Recommendation: joinedload/selectinload para user e category, GROUP BY para contagens por status, prioridade, usuário e categoria (T-07).

### [MEDIUM] Validação ausente e inconsistente entre create e update
ID: AP-13
File: routes/task_routes.py:113
Locations: routes/task_routes.py:167, routes/task_routes.py:182, routes/task_routes.py:261, routes/task_routes.py:264, routes/report_routes.py:196-197, routes/user_routes.py:102-103, routes/user_routes.py:124-125, routes/report_routes.py:180
Description: priority < 1 com priority = "alta" lança TypeError (500); len(data['title']) com title null no update lança TypeError; int(priority) no search com ?priority=x lança ValueError (500); update_category usa data sem checar None; update_user aceita name vazio e active não booleano; color não é validada embora is_valid_color exista.
Impact: Entradas inválidas comuns viram 500 em vez de 400, e create e update aceitam conjuntos diferentes de dados.
Recommendation: Validação única por entidade no model/serviço, compartilhada entre create e update, com 400 para tipo errado (T-04, T-14).

### [MEDIUM] Lógica de atraso, serialização e validação duplicadas
ID: AP-14
File: routes/task_routes.py:30-39
Locations: routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:17-28, routes/user_routes.py:61, routes/user_routes.py:106, routes/task_routes.py:140-144, routes/task_routes.py:209-213, routes/report_routes.py:67, routes/report_routes.py:151, routes/task_routes.py:296
Description: O bloco "due_date < utcnow e status fora de done/cancelled" aparece 6 vezes enquanto Task.is_overdue() (models/task.py:50-60) nunca é chamado; get_tasks remonta à mão os campos de Task.to_dict(); a regex de email está em 3 lugares (incluindo utils/helpers.py:21); o join de tags e o cálculo de completion_rate se repetem.
Impact: Mudar a regra de atraso exige editar 6 lugares; um esquecido gera respostas divergentes entre /tasks, /tasks/stats e /reports.
Recommendation: Usar Task.is_overdue e um serializador por entidade com variantes explícitas (T-12, T-04).

### [MEDIUM] Tratamento de erro com except genérico e sem handler global
ID: AP-15
File: routes/task_routes.py:62
Locations: routes/task_routes.py:137, routes/task_routes.py:151, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:87, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88, services/notification_service.py:23
Description: get_tasks embrulha o handler inteiro em try/except: e devolve {'error': 'Erro interno'} sem registrar nada; 11 rotas repetem o mesmo try/commit/rollback; não há errorhandler, então 404 de rota inexistente, 405 e 500 não tratados saem em HTML.
Impact: Bugs reais somem sem log; o cliente recebe ora JSON, ora HTML para o mesmo tipo de erro.
Recommendation: errorhandler global para HTTPException e Exception com resposta JSON e log, except com tipo específico onde é esperado (T-08).

### [MEDIUM] datetime.utcnow() deprecated no Python 3.12+
ID: AP-16
File: routes/task_routes.py:31
Locations: routes/task_routes.py:72, routes/task_routes.py:215, routes/task_routes.py:285, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, models/task.py:15, models/task.py:16, models/task.py:52, models/user.py:14, models/category.py:11, utils/helpers.py:38, services/notification_service.py:35, seed.py:66, seed.py:67, seed.py:69, seed.py:70, seed.py:74
Description: 22 chamadas a datetime.utcnow(); confirmado com python -W always no 3.14.6: "DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal".
Impact: Quebra quando a função for removida; hoje já polui o log a cada request.
Recommendation: Helper utcnow() único retornando datetime.now(timezone.utc) sem tzinfo, para manter o formato str() atual das respostas e a comparação com as colunas naive (T-11).

### [MEDIUM] Model.query.get() legado no SQLAlchemy 2.x
ID: AP-16
File: routes/task_routes.py:42
Locations: routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:227, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213
Description: 16 chamadas a X.query.get(id); confirmado no SQLAlchemy 2.1.8: "LegacyAPIWarning: The Query.get() method is considered legacy".
Impact: API marcada para remoção; emite warning em toda leitura por id.
Recommendation: db.session.get(Model, id) nos repositórios/serviços (T-11).

### [LOW] Código morto: imports, funções, serviço e dependências sem uso
ID: AP-21
File: utils/helpers.py:1-116
Locations: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:7-8, models/task.py:3, services/notification_service.py:1-48, models/task.py:38-60, models/user.py:34-38, requirements.txt:4-6
Description: Imports nunca usados (os, sys, json, time, hashlib, math, format_date, calculate_percentage); validate_email, sanitize_string, generate_id, log_action, is_valid_color, process_task_data e as constantes VALID_STATUSES etc. não têm chamador; NotificationService (com lista em memória self.notifications, que seria AP-08 se fosse instanciado) nunca é importado; Task.validate_status/validate_priority/is_overdue e User.is_admin não são chamados; marshmallow, requests e python-dotenv estão no requirements sem import.
Impact: O leitor acha que a validação de helpers.py está ativa quando não está; dependências extras aumentam a superfície de instalação.
Recommendation: Passar a usar o que resolve duplicação (is_overdue, constantes, validadores) e remover o resto; python-dotenv passa a ser usado pela config (T-14).

### [LOW] Magic numbers e listas de valores soltas
ID: AP-18
File: routes/task_routes.py:110
Locations: routes/task_routes.py:96-100, routes/task_routes.py:113, routes/task_routes.py:167-182, routes/user_routes.py:64, routes/user_routes.py:71, routes/user_routes.py:115, routes/user_routes.py:120, routes/report_routes.py:24-28, routes/report_routes.py:45, routes/report_routes.py:129, models/task.py:39, utils/helpers.py:75
Description: ['pending', 'in_progress', 'done', 'cancelled'] em 5 lugares, roles em 3, limites 3/200 de título, 4 de senha, 1-5 de prioridade, priority <= 2 como "alta", janela de 7 dias, mapeamento 1..5 -> critical..minimal.
Impact: Mudar uma regra (ex.: novo status) exige caçar literais em vários arquivos.
Recommendation: Constantes nomeadas no model de cada entidade (T-14).

### [LOW] print no lugar de logging
ID: AP-20
File: routes/task_routes.py:149
Locations: routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39, utils/helpers.py:41
Description: print(f"Task criada: {task.id} - {task.title}"), print(f"ERRO: {str(e)}") etc.
Impact: Sem nível nem destino configurável; erros de banco só aparecem no stdout.
Recommendation: logging.getLogger(__name__) com nível adequado (T-15).

### [LOW] Nomes de uma letra e abreviados
ID: AP-19
File: routes/report_routes.py:24-28
Locations: routes/task_routes.py:16, routes/user_routes.py:14, routes/report_routes.py:55, routes/report_routes.py:161, models/category.py:14, models/task.py:45, seed.py:78
Description: p1..p5 para contagens por prioridade, u, t, c, td, d, p como variáveis fora de laço curto.
Impact: Leitura mais lenta, especialmente em summary_report, onde p1 só faz sentido olhando o dicionário 60 linhas abaixo.
Recommendation: Renomear internamente sem mudar campos da API (T-14).

## Deprecated APIs
datetime.utcnow() (22 ocorrências, Python 3.12+), detalhado acima.
Query.get() (16 ocorrências, SQLAlchemy 2.x), detalhado acima.

================================
Total: 18 findings
================================
```

Uma observação antes da decisão. O AP-04 (autenticação) é o único finding cuja correção muda o contrato de muitas rotas, porque clientes que hoje chamam DELETE e PUT sem token passariam a receber 401. Minha recomendação é deixar esse fora da Fase 3 e registrar como "not fixed", a menos que você queira incluir. Os outros cabem sem quebrar contrato. A única mudança intencional seria o campo `password` sumir das respostas.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
