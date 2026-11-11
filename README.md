# Criação de Skills: Refatoração Arquitetural Automatizada

Entrega do desafio do módulo Desenvolvimento de Software e Aplicações com IA (MBA em IA da Full Cycle). O enunciado completo está no [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill#readme).

A skill `refactor-arch` audita um projeto backend legado e o refatora para MVC em três fases: análise da stack, auditoria de anti-patterns com relatório por severidade (e pausa para aprovação) e refatoração validada contra uma linha de base dos endpoints. Ela foi executada pelo Claude Code nos três projetos deste repositório: dois em Python/Flask e um em Node.js/Express.

## Análise Manual

Antes de escrever a skill, li o código dos três projetos inteiro. Os problemas abaixo seguem a escala do enunciado (CRITICAL, HIGH, MEDIUM, LOW), com arquivo e linha do código original. Cada um virou um sinal de detecção no catálogo da skill, mas escrito de forma genérica, sem nomes destes projetos, para não transformar a skill numa lista de respostas.

### Projeto 1: code-smells-project (Python/Flask, API de e-commerce)

Quatro arquivos: `app.py` registra rotas e ainda tem duas rotas administrativas com SQL, `controllers.py` mistura validação, regra e "notificações" com `print`, `models.py` faz SQL de quatro domínios, e `database.py` guarda uma conexão global.

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | SQL injection por concatenação em quase todas as queries | `models.py:28`, `47-50`, `58-60`, `110`, `127-128`, `280`, `289-297` e outras | `login_usuario` monta `WHERE email = '...' AND senha = '...'`: um email `' OR '1'='1' --` entra sem senha. A busca por termo deixa ler qualquer tabela |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário e outro que apaga o banco, sem autenticação | `app.py:47-78` | `POST /admin/query` aceita qualquer SQL vindo do corpo, e `POST /admin/reset-db` zera as quatro tabelas. Qualquer pessoa com acesso à rede apaga a loja |
| 3 | CRITICAL | `SECRET_KEY` hardcoded e devolvida pelo `/health` | `app.py:7`, `controllers.py:285-289` | A chave que assina sessões está no código e ainda é publicada num endpoint aberto, junto com `debug` e caminho do banco |
| 4 | CRITICAL | Senhas em texto puro, comparadas no SQL e devolvidas na listagem de usuários | `database.py:75-79`, `models.py:83`, `99`, `110` | `GET /usuarios` devolve a senha de todos, incluindo a do admin |
| 5 | HIGH | Conexão SQLite global e mutável, compartilhada entre threads | `database.py:4-10` | `global db_connection` com `check_same_thread=False`: uma conexão para todas as requisições, sem fechamento, impossível de trocar em teste |
| 6 | HIGH | Criação de pedido sem transação, com checagem de estoque separada da baixa | `models.py:133-169` | Dois pedidos simultâneos passam pela checagem e deixam estoque negativo. Uma falha no meio grava pedido sem itens |
| 7 | HIGH | `debug=True` e `host="0.0.0.0"` fixos | `app.py:8`, `88` | O debugger do Werkzeug exposto na rede permite execução remota de código |
| 8 | MEDIUM | N+1 nas listagens de pedidos | `models.py:187-199`, `219-231` | Para cada pedido, uma query de itens; para cada item, uma query do produto |
| 9 | MEDIUM | Erro interno devolvido ao cliente com `str(e)` em todos os handlers | `controllers.py:10-12`, `21-22`, `60-62` e demais | Vaza detalhes de SQL e da estrutura do banco. `login` com corpo vazio vira 500 em vez de 400 (`controllers.py:169-170`) |
| 10 | MEDIUM | Serialização e validação duplicadas | `models.py:12-21`, `31-40`, `304-313`; `controllers.py:28-50` e `72-90` | O mesmo dicionário de produto aparece três vezes. `atualizar_produto` não valida categoria nem tamanho do nome, que a criação valida |
| 11 | LOW | Magic numbers nas faixas de desconto e listas de valores soltas | `models.py:256-262`, `controllers.py:52`, `242` | `10000`, `0.1`, `5000`, `0.05` sem nome; listas de categorias e status repetidas |
| 12 | LOW | `print` como log e como "envio" de e-mail, SMS e push | `controllers.py:8`, `57`, `179`, `208-210`, `248-250` | Sem nível nem contexto, e o login loga o email de cada tentativa |
| 13 | LOW | Import não usado e nome que sombreia builtin | `models.py:2`, `database.py:2`; `controllers.py:56`, `160` | `import sqlite3` e `import os` sem uso; variável `id` |

### Projeto 2: ecommerce-api-legacy (Node.js/Express, LMS com checkout)

Três arquivos: `app.js` sobe o Express, `AppManager.js` é uma classe que faz tudo, e `utils.js` guarda configuração, cache global e a "criptografia".

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais de produção hardcoded | `utils.js:1-7` | Senha do banco, chave `pk_live_` do gateway de pagamento e usuário SMTP no código |
| 2 | CRITICAL | God Class `AppManager` | `AppManager.js:4-139` | Uma classe abre o banco, cria schema, faz seed, registra as três rotas, decide pagamento, matrícula, auditoria e relatório |
| 3 | CRITICAL | Número do cartão e chave do gateway impressos no log | `AppManager.js:45` | `console.log` com o cartão completo e a chave a cada checkout |
| 4 | CRITICAL | "Hash" de senha caseiro e senha padrão | `utils.js:17-23`, `AppManager.js:68` | `badCrypto` repete os 2 primeiros caracteres do base64 da senha: senhas que começam igual viram o mesmo "hash". Sem senha no corpo, grava `"123456"` |
| 5 | CRITICAL | Relatório financeiro e exclusão de usuário sem autenticação | `AppManager.js:80`, `131` | Qualquer um lê faturamento por aluno e apaga usuários |
| 6 | HIGH | Checkout sem transação e exclusão que deixa órfãos | `AppManager.js:50-63`, `131-136` | Matrícula, pagamento e auditoria em três escritas soltas. O próprio `DELETE /api/users/:id` responde que "as matrículas e pagamentos ficaram sujos no banco" |
| 7 | HIGH | Estado global mutável exportado | `utils.js:9-15`, `25` | `globalCache` cresce a cada checkout e nunca é lido; `totalRevenue` é exportado e nunca atualizado |
| 8 | MEDIUM | Callback hell com contadores manuais | `AppManager.js:37-77`, `83-128` | Quatro níveis de callback; `coursesPending` e `enrPending` controlados à mão; `err` ignorado nos níveis internos (`92`, `104`, `106`, `133`) |
| 9 | MEDIUM | N+1 no relatório financeiro | `AppManager.js:92-106` | Uma query de matrículas por curso e mais duas (usuário e pagamento) por matrícula |
| 10 | MEDIUM | Validação ausente e respostas de erro inconsistentes | `AppManager.js:35`, `133-135` | Email e curso não são validados; `DELETE` responde 200 mesmo quando o usuário não existe ou dá erro |
| 11 | LOW | Nomes de uma letra e `self = this` | `AppManager.js:26`, `29-33` | `u`, `e`, `p`, `cid`, `cc` dentro de uma função de 50 linhas |
| 12 | LOW | Regra de aprovação por magic string | `AppManager.js:46` | `cc.startsWith("4")` decide se o pagamento passa, sem nome nem explicação |
| 13 | LOW | Import morto | `AppManager.js:2` | `totalRevenue` importado e nunca usado |

APIs deprecated: não encontrei uso de API obsoleta neste projeto (Express 4.18, `sqlite3` 5.1, `Buffer.from` já é a forma atual).

### Projeto 3: task-manager-api (Python/Flask, gerenciador de tarefas)

Este já tem `models/`, `routes/`, `services/` e `utils/`, mas a separação é só de nome: as rotas fazem tudo, os models têm métodos que ninguém usa e os utilitários estão duplicados nas rotas.

| # | Severidade | Problema | Onde | Por que importa |
|---|---|---|---|---|
| 1 | CRITICAL | Segredos hardcoded | `app.py:13`, `services/notification_service.py:9-10` | `SECRET_KEY` e a senha do Gmail usado para notificações no código |
| 2 | CRITICAL | Senha com MD5 sem salt | `models/user.py:29`, `32` | MD5 sem salt cai em tabela pronta em segundos |
| 3 | CRITICAL | Hash da senha devolvido pela API | `models/user.py:21` (usado em `routes/user_routes.py:33`, `85`, `129`, `209`) | `to_dict()` inclui `password`, e ele aparece no cadastro, no detalhe do usuário e no login |
| 4 | CRITICAL | Sem autenticação real, e qualquer um se cadastra como admin | `routes/user_routes.py:52`, `71`, `210` | O login devolve `fake-jwt-token-<id>`, que nenhuma rota confere. `POST /users` aceita `role: "admin"` de quem não está logado |
| 5 | HIGH | Regra de negócio e serialização dentro das rotas, sem camada de controller | `routes/task_routes.py:11-63`, `routes/report_routes.py:12-101` | `get_tasks` monta o dicionário campo a campo, calcula atraso e busca usuário e categoria. Não dá para testar a regra sem HTTP |
| 6 | HIGH | `NotificationService` acoplado ao SMTP e nunca usado | `services/notification_service.py:4-25` | Cria `smtplib.SMTP` dentro do método e guarda notificações numa lista em memória. Nenhuma rota chama o serviço |
| 7 | HIGH | `debug=True` e `host="0.0.0.0"` fixos | `app.py:34` | Mesmo risco do projeto 1 |
| 8 | MEDIUM | APIs deprecated: `Query.get()` e `datetime.utcnow()` | `Query.get`: `routes/task_routes.py:42`, `51`, `67`, `117`, `122`, `158`, `188`, `195`, `227`; `routes/user_routes.py:29`, `94`, `136`, `155`; `routes/report_routes.py:105`, `192`, `213`. `utcnow`: `models/task.py:15-16`, `52`, `models/user.py:14`, `models/category.py:11` e rotas | `Query.get` é legado no SQLAlchemy 2.x (instalado: 2.1.8) e emite `LegacyAPIWarning`; `utcnow()` é deprecated desde o Python 3.12. Confirmei os dois avisos rodando com `-W always` |
| 9 | MEDIUM | N+1 em listagens e relatórios | `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:55-56`, `163` | `GET /tasks` faz duas queries por task; `/categories` conta tasks com uma query por categoria; o resumo faz 9 `COUNT` separados (`19-28`) |
| 10 | MEDIUM | Lógica de "atrasada" copiada em seis lugares, com `Task.is_overdue()` sem uso | `routes/task_routes.py:30-39`, `71-80`, `283-287`; `routes/user_routes.py:171-180`; `routes/report_routes.py:34-36`, `132-135`; método em `models/task.py:50-60` | Mudar a regra exige achar as seis cópias |
| 11 | MEDIUM | `except:` sem tipo e validação frágil | `routes/task_routes.py:62`, `137`, `204`, `236`; `routes/user_routes.py:130`, `149`; `routes/report_routes.py:186`, `207`, `221`; `routes/report_routes.py:196-197`; `routes/task_routes.py:113` | `except:` engole até `KeyboardInterrupt`. `PUT /categories/<id>` com corpo vazio dá 500, e `priority` como string dá `TypeError` |
| 12 | LOW | Imports não usados | `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `utils/helpers.py:3-7` | `os`, `sys`, `json`, `time`, `hashlib`, `math` importados sem uso |
| 13 | LOW | Constantes declaradas e ignoradas, magic numbers repetidos | `utils/helpers.py:110-116`; `routes/task_routes.py:110`, `113`; `routes/report_routes.py:129` | `VALID_STATUSES` existe, mas as rotas repetem a lista; prioridade `<= 2` como "alta" sem nome |
| 14 | LOW | `print` como log | `routes/task_routes.py:149`, `153`, `219`, `234`; `routes/user_routes.py:83`, `89`, `147` | Sem nível, e mistura sucesso com erro |

## Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o fluxo das 3 fases, formatos de saída e regras
├── references/
│   ├── project-analysis.md               # Fase 1: heurísticas de linguagem, framework, banco, domínio, rotas
│   ├── anti-patterns-catalog.md          # Fase 2: 21 anti-patterns com sinais de detecção e severidade
│   ├── report-template.md                # Fase 2: formato obrigatório do relatório
│   ├── mvc-guidelines.md                 # Fase 3: camadas, estrutura alvo por stack, config, erros
│   ├── refactoring-playbook.md           # Fase 3: 15 transformações com código antes e depois
│   └── validation.md                     # Fase 3: linha de base, boot, smoke test, re-scan, checklist
└── scripts/
    ├── free_port.py                      # acha uma porta livre
    └── http_smoke.py                     # roda requisições e grava status e formato das respostas
```

As cinco áreas pedidas no enunciado estão cobertas assim: análise de projeto em `project-analysis.md`, catálogo em `anti-patterns-catalog.md`, template em `report-template.md`, guidelines em `mvc-guidelines.md` e playbook em `refactoring-playbook.md`. A sexta referência, `validation.md`, saiu do requisito de que a Fase 3 prove que a aplicação continua funcionando.

### Decisões de design

O `SKILL.md` é curto e procedural: diz o que fazer em cada fase, o formato exato de cada saída e quando ler cada referência. O conhecimento de domínio fica nas referências, que o agente lê só no momento em que precisa. Assim a Fase 1 não carrega o playbook inteiro no contexto, e trocar o catálogo não exige mexer no fluxo.

A pausa da Fase 2 está escrita como regra dura ("não chame nenhuma ferramenta que altere arquivos até receber a resposta"), com a pergunta literal do enunciado na última linha. Fases 1 e 2 só podem rodar comandos de leitura, com uma exceção explícita: instalar dependências em `.venv/` ou `node_modules/`, que o git ignora.

A validação compara antes e depois, em vez de só subir a aplicação. Antes de editar qualquer arquivo, a Fase 3 sobe o projeto original, chama todas as rotas do inventário da Fase 1 e grava status e formato de cada resposta. Depois da refatoração, roda as mesmas requisições e lista cada diferença. Diferença que não está na lista de "mudanças intencionais" (como uma rota admin que passou a exigir token) é regressão e precisa ser corrigida antes de declarar sucesso.

Preservar o contrato externo é regra explícita: mesmas rotas, mesmos métodos, mesmo formato de resposta e mesmo comando de execução (`python app.py`, `npm start`). Quebrar isso seria "refatorar" e entregar outro sistema.

### Anti-patterns do catálogo

São 21, distribuídos em 6 CRITICAL, 5 HIGH, 6 MEDIUM e 4 LOW:

| Severidade | Anti-patterns |
|---|---|
| CRITICAL | Credenciais hardcoded, SQL injection, God Class, endpoint perigoso sem autenticação, senha em texto puro ou hash fraco, exposição de dados sensíveis |
| HIGH | Regra de negócio em rota/controller, estado global mutável, acoplamento sem injeção de dependência, escrita multi-etapa sem transação, debug e configuração insegura |
| MEDIUM | N+1, validação ausente ou duplicada, duplicação de lógica, tratamento de erro genérico, API deprecated, callback hell |
| LOW | Magic numbers, nomes pouco descritivos, `print` como log, código morto |

A seleção partiu da análise manual: todo problema da tabela acima corresponde a uma entrada. Algumas entradas foram além dos três projetos (exposição de dados sensíveis separada de credenciais, callbacks aninhados) porque são padrões que aparecem em qualquer backend legado e que o enunciado classifica explicitamente.

Cada entrada tem sinais de detecção concretos, quase sempre com o `grep` que acha o padrão, e uma seção de falsos positivos. Por exemplo, `.like(f"%{q}%")` no SQLAlchemy não é injeção, porque o ORM parametriza. Sem isso, o agente reporta coisa errada com confiança.

A detecção de APIs deprecated (AP-16) é uma tabela de pares obsoleto e moderno para Python, SQLAlchemy, Flask, Werkzeug, Node e Express, com a instrução de confirmar a versão instalada no manifesto e rodar com avisos ligados (`python -W always`, `node --trace-deprecation`). Quando não há nada, o relatório precisa dizer o que foi checado.

### Como a skill ficou agnóstica de tecnologia

1. As heurísticas de detecção são tabelas por manifesto e assinatura de código, cobrindo Python, Node, Ruby, PHP, Go, Java e C#, com frameworks de cada um.
2. A estrutura alvo do MVC tem uma versão para Flask, uma para Express e regras para as demais stacks, sempre respeitando a convenção do framework (não criar `views/` num projeto que já usa `routes/` para esse papel).
3. O playbook mostra Python e JavaScript lado a lado nas transformações em que a sintaxe muda (config, queries, error handler, hash de senha).
4. Os scripts de validação usam só a biblioteca padrão do Python e falam HTTP, então servem para qualquer stack.
5. Nenhum exemplo das referências usa nomes, rotas ou números dos três projetos. Os exemplos são de biblioteca, frete, clínica e vouchers. Na primeira versão eu tinha usado trechos reais dos projetos como exemplo e troquei, porque a skill passaria nos três projetos por memorização e não provaria nada.

### Desafios e como resolvi

Porta ocupada. No macOS a porta 5000 é do AirPlay Receiver, e os dois projetos Flask fixam essa porta. A primeira tentativa de linha de base não subia. Resolvi de dois lados: a skill ganhou `scripts/free_port.py` e a regra de nunca matar processo que ela não iniciou, e a validação usa o mecanismo do framework (`flask --app app run --port`) para subir o original sem editar arquivo.

Pausa verificável. "Pedir confirmação" num prompt é fácil de escrever e difícil de provar. Rodei as Fases 1 e 2 como um processo separado do Claude Code (`claude -p "/refactor-arch"`), que termina na pergunta, e conferi com `git status` que nenhum arquivo do projeto mudou. Só depois retomei a mesma sessão com `claude -p "y" --resume <id>` para a Fase 3. Os três relatórios em `reports/` são a saída literal dessas execuções.

Mudanças de contrato por segurança. Fechar uma rota admin ou tirar a senha da resposta muda o comportamento, e o enunciado pede que os endpoints continuem respondendo. A regra que escrevi: o caminho e o método continuam existindo, a mudança aparece numa seção própria do resumo ("Intentional Behavior Changes") e a validação trata como regressão qualquer diferença que não esteja nessa lista. Autenticação geral, que mudaria todas as rotas de escrita, a skill propôs deixar de fora e registrou como "not fixed" nos projetos 1 e 3.

Senhas já gravadas. Trocar MD5 ou texto puro por scrypt quebraria o login de quem já existe no banco. O playbook (T-06) manda conferir o formato legado e regravar com o algoritmo novo no primeiro login. A skill aplicou isso nos três projetos e testou com uma cópia do banco antigo.

Overfitting das referências. Na primeira versão, os exemplos do playbook e do template usavam trechos dos próprios projetos (o `startsWith("4")` do cartão, os campos `usr`/`eml`, a regra de atraso de task). Troquei todos por domínios que não aparecem aqui, para que os resultados mostrem a skill generalizando.

Erro meu durante a execução. Eu commitei o projeto 2 enquanto a refatoração do projeto 3 rodava no mesmo repositório, e o `git commit` levou junto uma remoção que a outra execução tinha deixado no stage. A própria skill percebeu e avisou no resumo final. Como o commit ainda não tinha sido publicado, corrigi com `--amend` e a remoção foi para o commit do projeto 3. Para quem for repetir: rode as Fases 3 uma de cada vez, ou commite só depois que todas terminarem.

## Resultados

### Resumo das auditorias

| Projeto | Stack | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total | Deprecated |
|---|---|---|---|---|---|---|---|---|
| 1. code-smells-project | Python + Flask 3.1.1, SQLite com SQL cru | 4 (~780 linhas) | 6 | 4 | 4 | 4 | 18 | nenhuma (lista do que foi checado no relatório) |
| 2. ecommerce-api-legacy | Node.js + Express 4, SQLite em memória | 3 (~180 linhas) | 5 | 4 | 5 | 4 | 18 | nenhuma (com `node --trace-deprecation`) |
| 3. task-manager-api | Python + Flask 3.0.0, Flask-SQLAlchemy | 15 (~1.158 linhas) | 4 | 4 | 6 | 4 | 18 | `Query.get()` (16 chamadas), `datetime.utcnow()` (22 chamadas) |

Relatórios completos: [reports/audit-project-1.md](reports/audit-project-1.md), [reports/audit-project-2.md](reports/audit-project-2.md), [reports/audit-project-3.md](reports/audit-project-3.md). Resumos da Fase 3: [validation/runs/](validation/runs/).

Todos os problemas da análise manual (13 no projeto 1, 13 no projeto 2 e 14 no projeto 3) aparecem nos relatórios da skill. Ela também achou coisas que eu não tinha visto: no projeto 1, quantidade negativa num item de pedido aumenta o estoque; no projeto 2, `card` enviado como número derruba o processo inteiro; no projeto 3, três dependências do `requirements.txt` nunca são importadas. Um finding do projeto 3 estava exagerado (tasks órfãs ao apagar categoria: o backref do SQLAlchemy já anulava a chave), e a própria skill corrigiu isso no resumo da Fase 3 depois de ver a linha de base.

### Antes e depois

Projeto 1, de 4 arquivos para MVC completo:

```
antes                         depois
app.py                        app.py                      # entry point: create_app + run
controllers.py                src/app.py                  # composition root
models.py                     src/config/settings.py
database.py                   src/database.py             # conexão por requisição, schema, seed com hash
                              src/models/        produto, usuario, pedido, sistema
                              src/services/      pedido, relatorio, notification
                              src/controllers/   produto, usuario, pedido, relatorio, sistema
                              src/views/         5 blueprints
                              src/middlewares/   error_handler, auth
                              src/errors.py
```

Projeto 2, de uma God Class para camadas com injeção por factory:

```
antes                         depois
src/app.js                    src/app.js                  # entry point + composition root
src/AppManager.js             src/config/index.js
src/utils.js                  src/database/      connection (Promise + transação), schema
                              src/models/        user, course, enrollment, payment, auditLog
                              src/services/      checkout, financialReport, user, paymentGateway
                              src/controllers/   checkout, report, user
                              src/routes/index.js
                              src/middlewares/   adminAuth, asyncHandler, errorHandler
                              src/validators/, src/lib/ (logger, password), src/errors.js
```

Projeto 3, que já tinha camadas parciais. A skill manteve `models/` e `routes/` e completou o que faltava:

```
antes                         depois
app.py                        app.py + app_factory.py     # create_app(settings)
models/                       models/                     # regras, validadores e constantes por entidade
routes/ (3 arquivos)          routes/ (5 arquivos)        # categorias saíram de report_routes
services/notification (morto) services/report_service.py
utils/helpers.py (morto)      utils/helpers.py (utcnow), utils/errors.py
                              controllers/       task, user, category, report
                              config/settings.py
                              middlewares/error_handler.py
```

### Validação independente

Além da validação que a própria skill faz, gravei uma linha de base dos três projetos originais antes de qualquer mudança, com o meu smoke test em [validation/smoke.py](validation/smoke.py) e as specs em `validation/spec-project-*.json`. Depois de cada refatoração, subi a aplicação pelo comando documentado, com banco limpo, e repeti as mesmas requisições. Logs de servidor e respostas estão em [validation/logs/](validation/logs/).

| Projeto | Requisições | Mesmo status | Diferenças | Todas intencionais? |
|---|---|---|---|---|
| 1 | 25 | 23 | `POST /admin/query` removida (404), `POST /admin/reset-db` exige token (403); `/health` sem `secret_key`, `debug` e `db_path` | Sim |
| 2 | 7 | 5 | relatório financeiro e `DELETE /api/users/:id` exigem `X-Admin-Token` (403). Com `ADMIN_TOKEN` configurado, os dois voltam a 200 com o mesmo formato | Sim |
| 3 | 28 | 28 | campo `password` saiu de 3 respostas de usuário | Sim |

Logs de boot depois da refatoração (trechos de `validation/logs/after-project-*.server.log`):

```
# projeto 1: PORT=5061 python -W always app.py
INFO src.database: Seed aplicado: 10 produtos, 3 usuários
INFO __main__: Servidor iniciado em http://127.0.0.1:5061

# projeto 2: PORT=3011 node --trace-deprecation src/app.js
WARN PAYMENT_GATEWAY_KEY ausente, usando gateway simulado
WARN ADMIN_TOKEN ausente, rotas administrativas respondem 403
INFO LMS API rodando na porta 3011

# projeto 3: python seed.py && PORT=5063 python -W always app.py
 * Serving Flask app 'app_factory'
 * Debug mode: off
```

Nenhum dos três logs tem traceback nem aviso de deprecation. No projeto 3, a skill contou 113 avisos de deprecation na linha de base (boot mais requisições); no meu log pós-refatoração, rodando com `-W always`, não há nenhum.

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| Linguagem detectada corretamente | ✓ Python | ✓ JavaScript (Node.js) | ✓ Python |
| Framework detectado corretamente | ✓ Flask 3.1.1 | ✓ Express ^4.18.2 | ✓ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio descrito corretamente | ✓ e-commerce | ✓ LMS com checkout | ✓ task manager |
| Número de arquivos condiz | ✓ 4 | ✓ 3 | ✓ 15 |
| Relatório segue o template | ✓ | ✓ | ✓ |
| Cada finding com arquivo e linhas exatos | ✓ | ✓ | ✓ |
| Findings ordenados por severidade | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 18 | ✓ 18 | ✓ 18 |
| APIs deprecated (se aplicável) | ✓ nenhuma, com lista checada | ✓ nenhuma, com lista checada | ✓ 2 encontradas |
| Pausa antes da Fase 3 | ✓ `git status` limpo | ✓ `git status` limpo | ✓ `git status` limpo |
| Estrutura MVC | ✓ | ✓ | ✓ |
| Config extraída, sem hardcoded | ✓ | ✓ | ✓ |
| Models abstraem dados | ✓ | ✓ | ✓ |
| Views/Routes separadas | ✓ `src/views/` | ✓ `src/routes/` | ✓ `routes/` |
| Controllers concentram o fluxo | ✓ | ✓ | ✓ |
| Error handling centralizado | ✓ | ✓ | ✓ |
| Entry point claro | ✓ `app.py` | ✓ `src/app.js` | ✓ `app.py` |
| Aplicação inicia sem erros | ✓ | ✓ | ✓ |
| Endpoints originais respondem | ✓ 23/25, 2 intencionais | ✓ 5/7, 2 intencionais (200 com token) | ✓ 28/28 |

Os critérios de aceite do enunciado foram atingidos nos três projetos: stack detectada, 18 findings em cada, pelo menos 4 CRITICAL em cada e aplicação funcionando depois da refatoração.

### O que ficou de fora

A skill não corrigiu tudo, e disse por quê. Nos projetos 1 e 3, autenticação nas rotas de negócio ficou como "not fixed", porque criar sessão ou token mudaria o contrato de todas as rotas de escrita. No projeto 1, cancelar um pedido continua sem devolver o estoque, porque antes é preciso decidir o que acontece quando um pedido sai do status "cancelado". No projeto 2, apagar um usuário agora apaga os pagamentos dele em cascata. Se o histórico financeiro precisa ser preservado, o caminho seria soft delete.

### Como a skill se comportou em stacks diferentes

A mesma skill, sem nenhuma mudança entre execuções (as três cópias são idênticas), produziu estruturas diferentes e adequadas a cada stack. No Flask desestruturado, criou `src/` com app factory e blueprints. No Express, trocou a God Class por factories com dependências injetadas e transformou os callbacks em `async/await` sobre um wrapper de Promise, com fila de transações porque o `sqlite3` usa uma conexão só. No Flask parcialmente organizado, manteve `models/` e `routes/`, porque renomear não melhora nada, e concentrou o trabalho no que faltava: controllers, config, error handler e a eliminação das cópias da regra de atraso.

A detecção de deprecated se comportou como deveria: nos dois projetos sem API obsoleta, o relatório diz o que foi checado em vez de inventar um finding; no projeto 3, achou as duas APIs e confirmou rodando com `-W always`.

As seis execuções (Fases 1 e 2 mais Fase 3, nos três projetos) levaram 23 minutos e custaram US$ 9,04 em tokens, com o modelo `claude-opus-5-5`.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) instalado e autenticado (testado com a versão 2.1.322)
- Python 3.10 ou mais novo (testado com 3.14) e Node.js 18 ou mais novo (testado com 23.1)
- `git`

### Executar a skill

A skill fica em `.claude/skills/refactor-arch/` dentro de cada projeto, então basta abrir o Claude Code na pasta do projeto e chamar `/refactor-arch`.

```bash
git clone https://github.com/camillacorreia/mba-ia-refactor-projects-skill.git
cd mba-ia-refactor-projects-skill

# Projeto 1
cd code-smells-project
claude "/refactor-arch"        # Fases 1 e 2; responda y para a Fase 3

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Este repositório já contém o resultado da refatoração. Para ver a skill trabalhando no código original, crie uma branch a partir do commit que tem a skill e os projetos ainda sem mudança, e copie a skill para os outros dois projetos:

```bash
git switch -c reexecucao 4cc7865
cp -R code-smells-project/.claude ecommerce-api-legacy/
cp -R code-smells-project/.claude task-manager-api/
```

Execução não interativa, como foi feita nesta entrega:

```bash
cd code-smells-project
claude -p "/refactor-arch" --output-format json > fase12.json     # para na pergunta de confirmação
claude -p "y" --resume <session_id do fase12.json> --output-format json > fase3.json
```

### Rodar as aplicações refatoradas

```bash
# Projeto 1
cd code-smells-project
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PORT=5001 .venv/bin/python app.py                 # http://127.0.0.1:5001

# Projeto 2
cd ecommerce-api-legacy
npm install
ADMIN_TOKEN=token-local-smoke npm start          # http://127.0.0.1:3000, rotas admin com header X-Admin-Token

# Projeto 3
cd task-manager-api
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
PORT=5003 .venv/bin/python app.py                 # http://127.0.0.1:5003
```

No macOS, use uma `PORT` diferente de 5000, que é ocupada pelo AirPlay Receiver. Todas as variáveis de configuração estão no `.env.example` de cada projeto, e as aplicações sobem sem nenhuma delas definida.

### Validar que a refatoração funcionou

Com a aplicação rodando, repita as requisições da linha de base e compare com o resultado gravado antes da refatoração:

```bash
python3 validation/smoke.py validation/spec-project-1.json http://127.0.0.1:5001 /tmp/after-1.json
python3 validation/smoke.py validation/spec-project-3.json http://127.0.0.1:5003 /tmp/after-3.json
python3 validation/smoke.py validation/spec-project-2-admin.json http://127.0.0.1:3000 /tmp/after-2.json
```

Cada linha impressa mostra status, método e rota. Compare com `validation/logs/before-project-*.json`: as únicas diferenças esperadas são as listadas na tabela de validação acima.
