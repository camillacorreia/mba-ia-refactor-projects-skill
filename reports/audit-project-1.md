# Auditoria: code-smells-project (projeto 1)

Saída das Fases 1 e 2 da skill `/refactor-arch`, executada com `claude -p "/refactor-arch"` (Claude Code 2.1.322, modelo claude-opus-5-5) dentro de `code-smells-project/`, sem edição. Sessão 66c27ac8-465a-4969-a429-07e63db3325e, 105 s.

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; ambiente local 3.14.6)
Framework:     Flask 3.1.1 (requirements.txt:1)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Database:      SQLite em arquivo (`loja.db`) com SQL cru via `sqlite3`, conexão global única, schema e seed criados no primeiro `get_db()`
Domain:        API de e-commerce (produtos, usuários, pedidos, itens de pedido, relatório de vendas), com fluxo principal de checkout: cria pedido, baixa estoque, muda status
Architecture:  Separação nominal: existem `models.py` e `controllers.py`, mas `models.py` mistura SQL concatenado, regra de negócio (desconto, estoque) e serialização de 3 domínios; `controllers.py` valida, decide e "notifica"; `app.py` tem rotas admin com SQL direto
Source files:  4 files analyzed (~780 lines)
Entry point:   app.py (`python app.py`, porta 5000, `0.0.0.0`, debug=True)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes
================================

| Método | Caminho | Handler | Local |
|---|---|---|---|
| GET | /produtos | listar_produtos | app.py:11 |
| GET | /produtos/busca | buscar_produtos | app.py:12 |
| GET | /produtos/<int:id> | buscar_produto | app.py:13 |
| POST | /produtos | criar_produto | app.py:14 |
| PUT | /produtos/<int:id> | atualizar_produto | app.py:15 |
| DELETE | /produtos/<int:id> | deletar_produto | app.py:16 |
| GET | /usuarios | listar_usuarios | app.py:18 |
| GET | /usuarios/<int:id> | buscar_usuario | app.py:19 |
| POST | /usuarios | criar_usuario | app.py:20 |
| POST | /login | login | app.py:21 |
| POST | /pedidos | criar_pedido | app.py:23 |
| GET | /pedidos | listar_todos_pedidos | app.py:24 |
| GET | /pedidos/usuario/<int:usuario_id> | listar_pedidos_usuario | app.py:25 |
| PUT | /pedidos/<int:pedido_id>/status | atualizar_status_pedido | app.py:26 |
| GET | /relatorios/vendas | relatorio_vendas | app.py:28 |
| GET | /health | health_check | app.py:30 |
| GET | / | index | app.py:32 |
| POST | /admin/reset-db | reset_database | app.py:47 |
| POST | /admin/query | executar_query | app.py:59 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite, SQL cru)
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 4 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] SQL injection em todas as queries com parâmetro
ID: AP-02
File: models.py:109-111
Locations: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-297
Description: login_usuario monta "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"; criar_produto, atualizar_produto, criar_usuario e atualizar_status_pedido concatenam strings do JSON; buscar_produtos faz query += " AND (nome LIKE '%" + termo + "%' ...". Nenhuma query usa placeholder.
Impact: POST /login com email "admin@loja.com' --" e qualquer senha devolve o usuário admin. GET /produtos/busca?q=' UNION SELECT ... lê a tabela usuarios inteira, senhas incluídas. Nome de produto com aspas simples ("Monitor 27''") quebra o INSERT com 500.
Recommendation: Reescrever todas as queries com placeholders "?" e tupla de parâmetros, inclusive o WHERE dinâmico da busca (T-02), dentro dos novos repositórios por entidade.

### [CRITICAL] Endpoints administrativos e de dados sem nenhuma autenticação
ID: AP-04
File: app.py:59-78
Locations: app.py:47-57, app.py:28, app.py:18-19
Description: POST /admin/query executa cursor.execute(query) com o SQL que vier em dados["sql"] e faz commit; POST /admin/reset-db roda DELETE em itens_pedido, pedidos, produtos e usuarios. Nenhuma rota do projeto tem decorator ou checagem de identidade, inclusive /relatorios/vendas (faturamento) e /usuarios.
Impact: Qualquer pessoa que alcance a porta 5000 apaga o banco com um POST vazio ou roda "DROP TABLE usuarios"; o relatório financeiro e a lista de clientes ficam públicos.
Recommendation: Remover /admin/query (SQL arbitrário não tem uso legítimo numa API) e proteger /admin/reset-db com token administrativo vindo de variável de ambiente, desligado por padrão (T-13).

### [CRITICAL] SECRET_KEY hardcoded e devolvida no /health
ID: AP-01
File: app.py:7
Locations: controllers.py:285-289
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"; health_check devolve "secret_key": "minha-chave-super-secreta-123", "debug": True, "db_path": "loja.db" e "ambiente": "producao" (também AP-06).
Impact: A chave que assina sessões do Flask está no repositório e em qualquer GET /health, então qualquer cookie de sessão pode ser forjado. O /health ainda revela caminho do banco e que o debugger está ligado.
Recommendation: Ler SECRET_KEY, DEBUG, DB_PATH e PORT de variáveis de ambiente num módulo config, e tirar secret_key, debug e db_path da resposta do /health (T-01).

### [CRITICAL] Senhas gravadas e comparadas em texto puro
ID: AP-05
File: models.py:126-129
Locations: models.py:109-111, database.py:75-83
Description: criar_usuario insere a senha recebida direto na coluna senha; login_usuario compara "AND senha = '" + senha + "'" no SQL; o seed grava "admin123", "123456" e "senha123".
Impact: Qualquer leitura do banco (via /admin/query, SQL injection ou cópia de loja.db) entrega a senha real de todos os usuários, que costuma ser reutilizada em outros serviços.
Recommendation: Gravar hash com werkzeug.security.generate_password_hash e conferir com check_password_hash no login, fazendo o seed também com hash e migrando senhas legadas no boot (T-06).

### [CRITICAL] Senha devolvida nas respostas de usuário
ID: AP-06
File: models.py:83
Locations: models.py:99
Description: get_todos_usuarios e get_usuario_por_id serializam "senha": row["senha"], e GET /usuarios e GET /usuarios/<id> devolvem esse dicionário. Os prints de controllers.py:161, 179 e 182 também logam o email de cada cadastro e tentativa de login.
Impact: GET /usuarios sem autenticação lista email e senha em texto puro de todos os clientes e do admin.
Recommendation: Serializador único de usuário que nunca inclui senha (T-12); log sem dado pessoal.

### [CRITICAL] models.py como God File de três domínios
ID: AP-03
File: models.py:1-314
Locations: database.py:7-86
Description: models.py (314 linhas) concentra SQL, serialização manual e regra de negócio de produtos, usuários, pedidos e relatório: checagem de estoque e cálculo de total em criar_pedido (models.py:139-146), faixas de desconto em relatorio_vendas (models.py:256-262). database.py mistura conexão, DDL e seed na mesma função get_db.
Impact: Nenhuma regra (desconto, estoque, autenticação) pode ser testada sem um SQLite real; qualquer mudança em pedidos mexe no mesmo arquivo que login.
Recommendation: Separar em models/ por entidade (repositório com SQL parametrizado), services/ com as regras de pedido, relatório e autenticação, e db/ com conexão, schema e seed em funções distintas (T-03).

### [HIGH] Regra de negócio e efeitos colaterais nos controllers
ID: AP-07
File: controllers.py:188-220
Locations: controllers.py:24-62, controllers.py:237-255, controllers.py:264-290, app.py:47-78
Description: criar_pedido valida, chama o model e dispara "ENVIANDO EMAIL/SMS/PUSH" via print; criar_produto tem 38 linhas de validação de domínio (preço, estoque, tamanho do nome, categorias); atualizar_status_pedido decide notificações por status; health_check e as rotas admin chamam get_db() e cursor.execute direto, pulando o model.
Impact: A mesma regra de produto precisa ser reescrita em cada handler (e já divergiu, ver AP-13); notificação não pode ser trocada por um envio real sem editar o controller.
Recommendation: Controllers só leem a requisição e montam a resposta; validação vai para validators/, regra de pedido e notificação para services/ (T-04).

### [HIGH] Criação de pedido sem transação e exclusão que deixa órfãos
ID: AP-10
File: models.py:133-169
Locations: models.py:65-70, models.py:275-283, controllers.py:249-250, database.py:36-53
Description: criar_pedido checa estoque num laço e só depois insere pedido, itens e faz "UPDATE produtos SET estoque = estoque - N", com um commit no fim e sem rollback; como a conexão é global, uma exceção no meio deixa os INSERTs pendentes e o próximo commit de qualquer request os grava. deletar_produto apaga o produto e mantém itens_pedido apontando para ele. O cancelamento só imprime "Devolver estoque" sem devolver. O schema não declara FOREIGN KEY.
Impact: Dois pedidos simultâneos passam pela checagem e deixam estoque negativo; pedido pela metade aparece no banco após erro; histórico de pedidos mostra "Desconhecido" depois de excluir produto.
Recommendation: Envolver criar_pedido em transação única com rollback, baixar estoque com "WHERE estoque >= ?" checando rowcount, adicionar FOREIGN KEY e bloquear exclusão de produto com pedidos (T-09).

### [HIGH] Conexão SQLite global e compartilhada entre threads
ID: AP-08
File: database.py:4-11
Locations: controllers.py:3, app.py:4
Description: db_connection = None mutado com "global db_connection" e aberto com check_same_thread=False; todas as funções chamam get_db() por conta própria, controllers importam database, e não há app factory (também AP-09).
Impact: O servidor de dev do Flask é multithread, então requests concorrentes compartilham o mesmo cursor e a mesma transação (é isso que torna o AP-10 contaminante); testes não conseguem usar um banco isolado.
Recommendation: create_app() como composition root, conexão por request em flask.g com teardown, caminho do banco vindo da config (T-05).

### [HIGH] Debug ligado, bind em 0.0.0.0 e CORS aberto fixos no código
ID: AP-11
File: app.py:88
Locations: app.py:8, app.py:9
Description: app.run(host="0.0.0.0", port=5000, debug=True), app.config["DEBUG"] = True e CORS(app) sem lista de origens.
Impact: O debugger do Werkzeug exposto na rede permite execução de código remoto a partir de qualquer traceback; qualquer site pode chamar a API pelo navegador da vítima.
Recommendation: DEBUG, HOST, PORT e CORS_ORIGINS vindos de variáveis de ambiente com padrão seguro (debug desligado) (T-01).

### [MEDIUM] Validação ausente e inconsistente entre create e update
ID: AP-13
File: controllers.py:64-92
Locations: controllers.py:24-54, controllers.py:169-170, controllers.py:239-240, app.py:61-62, controllers.py:195-201, models.py:144
Description: atualizar_produto não aplica as regras de nome (2..200) nem a lista de categorias que criar_produto aplica; login, atualizar_status_pedido e /admin/query chamam dados.get sem checar se get_json() devolveu None; preco/estoque não têm checagem de tipo; quantidade dos itens não é validada.
Impact: PUT /produtos/1 com categoria "xyz" é aceito; POST /login sem corpo dá 500 em vez de 400; preco "abc" vira 500; item com quantidade -5 passa na checagem de estoque e aumenta o estoque.
Recommendation: Um validador de produto usado por create e update, validador de pedido (quantidade inteira > 0), checagem de corpo JSON centralizada (T-04, T-14).

### [MEDIUM] Consultas N+1 na listagem de pedidos e no relatório
ID: AP-12
File: models.py:187-199
Locations: models.py:219-231, models.py:239-254, models.py:154-156
Description: Para cada pedido roda "SELECT * FROM itens_pedido WHERE pedido_id = ..." e, para cada item, "SELECT nome FROM produtos WHERE id = ..."; relatorio_vendas faz 5 queries separadas (COUNT, SUM e 3 COUNT por status); criar_pedido busca o preço de cada produto duas vezes.
Impact: 100 pedidos com 3 itens viram 401 queries por GET /pedidos.
Recommendation: Um SELECT de itens com JOIN em produtos filtrado por IN dos pedidos, agrupado em memória; relatório com uma query de agregação com SUM(CASE ...) (T-07).

### [MEDIUM] try/except genérico repetido que devolve str(e) ao cliente
ID: AP-15
File: controllers.py:10-12
Locations: controllers.py:21, controllers.py:60, controllers.py:95, controllers.py:108, controllers.py:125, controllers.py:133, controllers.py:143, controllers.py:164, controllers.py:185, controllers.py:218, controllers.py:226, controllers.py:234, controllers.py:254, controllers.py:261, controllers.py:291, app.py:77
Description: 17 blocos "except Exception as e: return jsonify({"erro": str(e)}), 500", um por handler, sem error handler global.
Impact: Mensagens internas do sqlite (nomes de tabela, trechos de SQL) vazam para o cliente, o que facilita explorar o AP-02; erro de entrada vira 500.
Recommendation: Exceções de domínio (ValidationError, NotFound) e um errorhandler registrado no create_app que loga o traceback e devolve mensagem genérica no 500 (T-08).

### [MEDIUM] Serialização e blocos de consulta duplicados
ID: AP-14
File: models.py:12-21
Locations: models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:178-200, models.py:211-232, controllers.py:30-46, controllers.py:74-90
Description: O dicionário de produto com 8 campos aparece 3 vezes, o de usuário 2 vezes, e o bloco inteiro de montar pedido com itens (23 linhas) é idêntico em get_pedidos_usuario e get_todos_pedidos; a validação de produto está copiada entre create e update.
Impact: O vazamento de senha precisou ser corrigido em dois lugares; a cópia da validação já divergiu (AP-13).
Recommendation: Funções de serialização únicas por entidade e uma rotina de listagem de pedidos com filtro opcional (T-12, T-04).

### [LOW] Magic numbers e listas de valores soltas
ID: AP-18
File: models.py:256-262
Locations: controllers.py:47-52, controllers.py:242, app.py:36, controllers.py:285-286, app.py:88
Description: Faixas de desconto 10000/5000/1000 com 0.1/0.05/0.02; limites de nome 2 e 200; lista de categorias e lista de status literais; versão "1.0.0" repetida em dois arquivos; porta 5000 fixa.
Impact: Mudar uma faixa de desconto ou adicionar status exige caçar literais em arquivos diferentes.
Recommendation: Constantes nomeadas num módulo de domínio (CATEGORIAS_VALIDAS, STATUS_PEDIDO, FAIXAS_DESCONTO, API_VERSION) (T-14).

### [LOW] print no lugar de logging, inclusive simulando notificações
ID: AP-20
File: controllers.py:208-210
Locations: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:219, controllers.py:248, controllers.py:250
Description: 19 chamadas de print, entre elas "ENVIANDO EMAIL: Pedido ...", "ENVIANDO SMS" e "ENVIANDO PUSH" no lugar de um serviço de notificação.
Impact: Sem nível nem contexto, não dá para filtrar erro de evento em produção.
Recommendation: logging com logger por módulo e um NotificationService que hoje só loga (T-15).

### [LOW] Imports mortos
ID: AP-21
File: models.py:2
Locations: database.py:2
Description: "import sqlite3" em models.py e "import os" em database.py não são usados (grep de "sqlite3." e "os." no arquivo retorna 0).
Impact: Ruído e falsa impressão de dependência.
Recommendation: Remover.

### [LOW] Nomes que sombreiam builtins e cursores numerados
ID: AP-19
File: controllers.py:56
Locations: controllers.py:160, models.py:24, models.py:89, models.py:187-191, models.py:219-223
Description: "id = models.criar_produto(...)" sombreia o builtin id; variáveis cursor2 e cursor3 dentro dos laços.
Impact: Leitura mais difícil e risco de bug ao usar id() no mesmo escopo.
Recommendation: Renomear internamente (produto_id, usuario_id), mantendo o nome do parâmetro de rota "id" que o Flask injeta (T-14).

## Deprecated APIs
No deprecated API usage found. Checked: datetime.utcnow/utcfromtimestamp, @app.before_first_request, app.json_encoder/JSONEncoder, werkzeug safe_str_cmp, Model.query.get, imp, distutils, asyncio.get_event_loop (Flask 3.1.1, Werkzeug 3.1.9, Python 3.14.6).

================================
Total: 18 findings
================================
```

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
