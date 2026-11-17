# Auditoria: code-smells-project (projeto 1)

Saída das Fases 1 e 2 da skill `/refactor-arch`, executada com `claude -p "/refactor-arch"` (Claude Code 2.1.326, modelo claude-opus-5-5) dentro de `code-smells-project/`, sem edição. Sessão 01a8853e-68aa-4ac7-9f95-e4060d8eba74, 108 s. Esta é a segunda execução, feita depois que a skill passou a exigir a correção do AP-04 com token administrativo; a primeira está no histórico do git (commit 694c5db).

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (versão não declarada; .venv local usa 3.14.6)
Framework:     Flask 3.1.1 (requirements.txt)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Database:      SQLite em arquivo (`loja.db`) com SQL cru via `sqlite3`, conexão global única, schema e seed criados no primeiro `get_db()`
Domain:        API de e-commerce (produtos, usuários, pedidos, itens de pedido), com fluxo principal de checkout (`POST /pedidos` valida estoque, grava pedido e itens, baixa estoque) e relatório de vendas
Architecture:  Separação nominal: existem `models.py` e `controllers.py`, mas `models.py` mistura SQL de 4 entidades, regra de desconto e serialização; `controllers.py` valida, notifica e faz SQL direto (`health_check`); `app.py` tem rotas admin com SQL inline
Source files:  4 files analyzed (~780 lines)
Entry point:   app.py (`python app.py`, porta 5000 fixa, host 0.0.0.0, debug=True)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Endpoints:     19 routes
================================

| # | Método | Caminho | Handler | Arquivo:linha |
|---|---|---|---|---|
| 1 | GET | /produtos | controllers.listar_produtos | app.py:11 |
| 2 | GET | /produtos/busca | controllers.buscar_produtos | app.py:12 |
| 3 | GET | /produtos/<int:id> | controllers.buscar_produto | app.py:13 |
| 4 | POST | /produtos | controllers.criar_produto | app.py:14 |
| 5 | PUT | /produtos/<int:id> | controllers.atualizar_produto | app.py:15 |
| 6 | DELETE | /produtos/<int:id> | controllers.deletar_produto | app.py:16 |
| 7 | GET | /usuarios | controllers.listar_usuarios | app.py:18 |
| 8 | GET | /usuarios/<int:id> | controllers.buscar_usuario | app.py:19 |
| 9 | POST | /usuarios | controllers.criar_usuario | app.py:20 |
| 10 | POST | /login | controllers.login | app.py:21 |
| 11 | POST | /pedidos | controllers.criar_pedido | app.py:23 |
| 12 | GET | /pedidos | controllers.listar_todos_pedidos | app.py:24 |
| 13 | GET | /pedidos/usuario/<int:usuario_id> | controllers.listar_pedidos_usuario | app.py:25 |
| 14 | PUT | /pedidos/<int:pedido_id>/status | controllers.atualizar_status_pedido | app.py:26 |
| 15 | GET | /relatorios/vendas | controllers.relatorio_vendas | app.py:28 |
| 16 | GET | /health | controllers.health_check | app.py:30 |
| 17 | GET | / | index | app.py:32-45 |
| 18 | POST | /admin/reset-db | reset_database | app.py:47-57 |
| 19 | POST | /admin/query | executar_query | app.py:59-78 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite, SQL cru)
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Endpoints administrativos e de dados de terceiros sem autenticação
ID: AP-04
File: app.py:59-78
Locations: app.py:47-57, app.py:28, app.py:18, app.py:19, app.py:24, app.py:25, app.py:26
Description: POST /admin/query faz cursor.execute(query) com o "sql" recebido no corpo e commita; POST /admin/reset-db apaga as 4 tabelas; GET /relatorios/vendas expõe faturamento; GET /usuarios e GET /usuarios/<id> listam cadastros de terceiros; GET /pedidos e GET /pedidos/usuario/<id> expõem pedidos de todos os clientes; PUT /pedidos/<id>/status aprova ou cancela qualquer pedido. Nenhuma tem decorator ou checagem de identidade/papel. O login (controllers.py:167-186) não emite credencial nenhuma, então não existe mecanismo de auth hoje.
Impact: Qualquer pessoa na rede roda "DROP TABLE usuarios" via /admin/query, zera o banco com um POST ou lê todos os clientes e o faturamento.
Recommendation: Token administrativo lido do ambiente (T-13) exigido nessas rotas via decorator; sem token elas passam a responder 401/403 (mudança intencional).

### [CRITICAL] SQL injection por concatenação em todo o models.py
ID: AP-02
File: models.py:109-111
Locations: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:126-129, models.py:140, models.py:148-151, models.py:155, models.py:157-161, models.py:163-166, models.py:174, models.py:188, models.py:192, models.py:220, models.py:224, models.py:279-281, models.py:289-299
Description: login_usuario monta "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"; buscar_produtos faz query += " AND (nome LIKE '%" + termo + "%' ..."; criar_produto, criar_usuario, atualizar_status_pedido e criar_pedido concatenam campos do corpo (incluindo item["produto_id"] e item["quantidade"], que não são tipados).
Impact: POST /login com email "admin@loja.com' --" autentica como admin sem senha; GET /produtos/busca?q=' UNION SELECT ... lê a tabela usuarios com senhas.
Recommendation: Placeholders "?" com tupla de parâmetros em todas as queries, já dentro dos novos models por entidade (T-02).

### [CRITICAL] SECRET_KEY hardcoded e devolvida no /health
ID: AP-01
File: app.py:7
Locations: controllers.py:289, controllers.py:286-288
Description: app.config["SECRET_KEY"] = "minha-chave-super-secreta-123" no código e o mesmo literal devolvido em GET /health como "secret_key", junto com "db_path": "loja.db" e "debug": True (também AP-06).
Impact: A chave que assina sessões está no git e em uma resposta pública; quem chama /health pode forjar cookies de sessão do Flask.
Recommendation: Ler SECRET_KEY, DEBUG, DB_PATH e porta de variáveis de ambiente num módulo de config (T-01) e remover secret_key, db_path e debug da resposta do /health.

### [CRITICAL] Senhas devolvidas pela API
ID: AP-06
File: models.py:83
Locations: models.py:99, controllers.py:132, controllers.py:140, controllers.py:161, controllers.py:179, controllers.py:182
Description: get_todos_usuarios e get_usuario_por_id serializam "senha": row["senha"], e GET /usuarios e GET /usuarios/<id> devolvem esse dict. Os logs imprimem o email de cada tentativa de login.
Impact: Um GET /usuarios sem autenticação entrega email e senha em texto puro de todos os clientes, incluindo "admin123" do admin.
Recommendation: Serialização única de usuário sem o campo senha (T-12); logs sem dado pessoal (T-15).

### [CRITICAL] Senha armazenada e comparada em texto puro
ID: AP-05
File: models.py:126-129
Locations: models.py:109-111, database.py:75-83
Description: criar_usuario grava senha como veio do corpo; login_usuario compara "AND senha = '" + senha + "'" no SQL; o seed insere "admin123", "123456", "senha123" sem hash.
Impact: Qualquer vazamento do loja.db (ou o próprio /admin/query) expõe todas as senhas reutilizáveis.
Recommendation: Hash com werkzeug.security (generate_password_hash / check_password_hash) no cadastro, no seed e no login (T-06), com migração das senhas legadas em texto puro no boot.

### [CRITICAL] models.py como God File de quatro domínios
ID: AP-03
File: models.py:1-314
Locations: database.py:7-86, app.py:47-78, controllers.py:264-274
Description: models.py (314 linhas) concentra SQL de produtos, usuários, pedidos e relatório, regra de negócio (faixas de desconto em models.py:256-262, checagem de estoque em models.py:139-146) e a montagem dos dicionários de resposta. database.py junta conexão, DDL e seed na mesma função; app.py e controllers.health_check executam SQL direto.
Impact: Qualquer mudança em pedido mexe no mesmo arquivo que login e catálogo; impossível testar a regra de desconto sem banco.
Recommendation: Separar em models por entidade, services para checkout/relatório/notificação, controllers finos, rotas em blueprints e um database.py só com conexão e schema (T-03).

### [HIGH] Checkout sem transação e exclusão que deixa itens órfãos
ID: AP-10
File: models.py:133-169
Locations: models.py:65-70, database.py:36-53, controllers.py:249-250
Description: criar_pedido checa estoque num laço (139-146), depois insere pedido, itens e faz "estoque = estoque - N" sem transação explícita nem guarda de estoque no UPDATE; se uma inserção falhar no meio, o que já foi executado fica pendente na conexão global compartilhada e é commitado pela próxima requisição. deletar_produto apaga o produto e mantém itens_pedido apontando para ele; o schema não tem FOREIGN KEY. Cancelar pedido só imprime "Devolver estoque".
Impact: Dois pedidos simultâneos do último item deixam estoque negativo; uma falha parcial grava pedido sem itens; pedidos antigos passam a mostrar "Desconhecido".
Recommendation: Transação com rollback cobrindo pedido, itens e baixa condicional (WHERE estoque >= ?), FOREIGN KEY com PRAGMA foreign_keys e tratamento de produto com histórico na exclusão (T-09).

### [HIGH] Debug ligado, host 0.0.0.0 e CORS aberto fixos no código
ID: AP-11
File: app.py:88
Locations: app.py:8, app.py:9, controllers.py:286-288
Description: app.run(host="0.0.0.0", port=5000, debug=True) e app.config["DEBUG"] = True; CORS(app) sem origens; /health anuncia "ambiente": "producao" com "debug": True.
Impact: O debugger do Werkzeug fica acessível na rede (execução de código protegida só pelo PIN) e qualquer origem lê a API pelo navegador.
Recommendation: DEBUG, HOST, PORT e CORS_ORIGINS vindos do ambiente com padrão seguro (T-01).

### [HIGH] Conexão SQLite global e mutável compartilhada entre threads
ID: AP-08
File: database.py:4-10
Description: db_connection = None no módulo, "global db_connection" em get_db e sqlite3.connect(db_path, check_same_thread=False); todas as requisições usam o mesmo objeto de conexão.
Impact: Requisições concorrentes compartilham a mesma transação implícita: o commit de uma grava a escrita pela metade da outra, e não há como isolar o banco em teste.
Recommendation: Conexão por requisição em flask.g com teardown, aberta a partir do caminho em app.config (T-05).

### [HIGH] Infraestrutura acoplada sem composition root
ID: AP-09
File: app.py:6
Locations: controllers.py:3, models.py:1, app.py:4
Description: O app é criado no import de app.py, sem create_app; cada função de models.py chama get_db() direto e controllers.py importa database para fazer SQL no health_check.
Impact: Não dá pra subir o app com outro banco (teste, tmp) nem trocar a conexão sem editar código.
Recommendation: create_app(config) registrando blueprints, error handlers e banco; models recebem a conexão do contexto da requisição (T-05, T-03).

### [HIGH] Regra de negócio e notificações nos controllers e nas rotas
ID: AP-07
File: controllers.py:188-220
Locations: controllers.py:24-62, controllers.py:237-255, controllers.py:264-290, app.py:47-78, models.py:256-262
Description: criar_pedido decide e dispara "ENVIANDO EMAIL/SMS/PUSH"; criar_produto tem 38 linhas de validação de domínio e lista de categorias; atualizar_status_pedido decide notificação por status; health_check e as rotas admin executam SQL; a regra de desconto por faixa de faturamento está no "model".
Impact: Regras de checkout e de status ficam espalhadas entre controller e SQL, sem como reaproveitar ou testar isoladamente.
Recommendation: Services de pedido, relatório e notificação; validação no model/schema; controllers só traduzem HTTP (T-04).

### [MEDIUM] Consultas N+1 na listagem de pedidos e no relatório
ID: AP-12
File: models.py:171-201
Locations: models.py:203-233, models.py:239-254, models.py:155
Description: Para cada pedido roda "SELECT * FROM itens_pedido WHERE pedido_id = ..." e para cada item "SELECT nome FROM produtos WHERE id = ..." (1 + P + I queries); o relatório faz 5 queries separadas (COUNT, SUM e três COUNT por status); criar_pedido relê o preço que já leu no primeiro laço.
Impact: Com 1.000 pedidos de 3 itens, GET /pedidos faz ~4.000 queries.
Recommendation: Um SELECT com JOIN itens_pedido/produtos agrupado em Python e um único SELECT com SUM(CASE ...) no relatório (T-07).

### [MEDIUM] Validação ausente e inconsistente entre criação e atualização
ID: AP-13
File: controllers.py:64-96
Locations: controllers.py:24-62, controllers.py:146-165, controllers.py:167-171, controllers.py:188-201, controllers.py:237-243
Description: atualizar_produto não aplica os limites de nome nem a lista de categorias que criar_produto aplica; preco/estoque não são checados por tipo ("abc" < 0 vira TypeError 500); login e atualizar_status chamam dados.get sem checar None; criar_pedido não valida produto_id nem quantidade (quantidade negativa passa no estoque e aumenta o estoque).
Impact: Um PUT grava categoria "xpto"; um pedido com quantidade -5 gera total negativo e infla o estoque; corpo vazio no login vira 500.
Recommendation: Validadores únicos por entidade usados no create e no update, com tipos e faixas (T-04, T-14).

### [MEDIUM] Serialização e consultas duplicadas
ID: AP-14
File: models.py:171-201
Locations: models.py:203-233, models.py:12-21, models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, controllers.py:28-46, controllers.py:72-90
Description: get_pedidos_usuario e get_todos_pedidos são idênticas exceto pelo WHERE; o dicionário de produto é montado três vezes e o de usuário duas; o bloco de validação de produto aparece no create e no update.
Impact: Uma correção (ex.: remover senha) precisa ser lembrada em vários lugares; foi exatamente o que vazou a senha em duas funções.
Recommendation: Funções de serialização por entidade e uma consulta de pedidos parametrizada (T-12, T-04).

### [MEDIUM] Tratamento de erro repetido que devolve str(e) ao cliente
ID: AP-15
File: controllers.py:10-12
Locations: 17 blocos "except Exception as e" em controllers.py (linhas 10, 21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291) e app.py:77-78
Description: Cada handler tem seu try/except devolvendo {"erro": str(e)} com 500; não há error handler global.
Impact: Mensagens internas do sqlite (nomes de tabela, trechos de SQL) chegam ao cliente e ajudam a explorar a injeção.
Recommendation: Exceções de domínio (validação 400, não encontrado 404) e error handlers centralizados que logam o detalhe e devolvem mensagem genérica no 500 (T-08).

### [LOW] print como log e simulação de notificação
ID: AP-20
File: controllers.py:208-210
Locations: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:219, controllers.py:248, controllers.py:250
Description: 19 prints, incluindo "ENVIANDO EMAIL: Pedido ..." como se fosse integração e emails de login em texto.
Impact: Sem nível nem contexto, impossível filtrar em produção; dado pessoal vai para stdout.
Recommendation: logging com logger por módulo e NotificationService isolando os envios simulados (T-15).

### [LOW] Magic numbers e listas de domínio soltas
ID: AP-18
File: models.py:256-262
Locations: controllers.py:52, controllers.py:242, controllers.py:47-50, models.py:247-253, app.py:36, controllers.py:285
Description: Faixas 10000/5000/1000 com 0.1/0.05/0.02; lista de categorias e lista de status inline; limites 2 e 200 do nome; "1.0.0" repetido.
Impact: Mudar a política de desconto ou adicionar um status exige caçar literais em arquivos diferentes.
Recommendation: Constantes nomeadas num módulo de domínio (T-14).

### [LOW] Imports mortos
ID: AP-21
File: models.py:2
Locations: database.py:2
Description: "import sqlite3" em models.py e "import os" em database.py nunca são usados.
Impact: Ruído e falsa impressão de dependência.
Recommendation: Remover.

### [LOW] Nomes pouco descritivos e sombra de builtin
ID: AP-19
File: models.py:187-193
Locations: models.py:219-225, controllers.py:56, controllers.py:160, models.py:24, models.py:54, models.py:65, models.py:89
Description: cursor2/cursor3 e prod nos laços; parâmetro e variável "id" sombreando o builtin.
Impact: Leitura mais difícil dos laços aninhados.
Recommendation: Renomear internamente (produto_id, pedido_id), mantendo os nomes de rota e de campo da API (T-14).

## Deprecated APIs
No deprecated API usage found. Checked: python -W always no import do app (Flask 3.1.1, Werkzeug 3.1.9, Python 3.14.6), datetime.utcnow/utcfromtimestamp, before_first_request, json_encoder, safe_str_cmp, imp/distutils.

================================
Total: 19 findings
================================
```

Observação: as rotas de catálogo (`/produtos` CRUD) e o checkout (`POST /pedidos`) também não têm autenticação, mas são rotas de negócio comuns e ficam fora do AP-04 para não mudar o contrato.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
