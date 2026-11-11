# Fase 3: code-smells-project (projeto 1)

Saída da Fase 3 da skill `/refactor-arch` depois da resposta `y`, retomando a sessão das Fases 1 e 2 com `claude -p "y" --resume <sessão>`. 6.0 min, 27 turnos, US$ 2.44.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                         # entry point: create_app() + app.run com config
├── .env.example
├── README.md
├── requirements.txt               # sem dependência nova
└── src/
    ├── app.py                     # composition root
    ├── errors.py                  # ValidationError, NotFound, Conflict, Forbidden...
    ├── database.py                # conexão por request (flask.g), schema, seed com hash
    ├── config/settings.py
    ├── models/        produto_model, usuario_model, pedido_model, sistema_model
    ├── services/      pedido_service, relatorio_service, notification_service
    ├── controllers/   produto, usuario, pedido, relatorio, sistema
    ├── views/         produto_routes, usuario_routes, pedido_routes, relatorio_routes, sistema_routes
    └── middlewares/   error_handler, auth

## Changes by Finding
[CRITICAL] SQL injection -> todas as queries com placeholder "?"; WHERE dinâmico da busca monta condições e parâmetros em paralelo
[CRITICAL] Endpoints admin sem autenticação -> /admin/query removida; /admin/reset-db exige X-Admin-Token igual a ADMIN_TOKEN (vazio = 403). Auth geral das rotas de negócio: not fixed, o projeto não tem modelo de sessão/token e criar um mudaria o contrato de todas as rotas
[CRITICAL] SECRET_KEY hardcoded e exposta no /health -> lida de SECRET_KEY (aleatória por boot se ausente, obrigatória com APP_ENV=producao); /health sem secret_key, debug e db_path
[CRITICAL] Senhas em texto puro -> generate_password_hash (scrypt) no cadastro e no seed; login confere hash e migra senha legada em texto puro no primeiro login
[CRITICAL] Senha devolvida nas respostas -> serializador único usuario_model.to_dict sem senha; logs sem email
[CRITICAL] models.py God File -> um model por entidade, services para pedido/relatório/notificação, database.py só conexão/schema/seed
[HIGH] Regra de negócio nos controllers -> validação nos models, notificação e transição de status no PedidoService, controllers só orquestram
[HIGH] Pedido sem transação / exclusão com órfãos -> criar pedido numa transação única (with db) com baixa condicional "estoque >= ?"; DELETE de produto com pedidos responde 409; FOREIGN KEY em itens_pedido (só em bancos novos). Devolução de estoque no cancelamento: not fixed, exige definir regra para sair de "cancelado" e isso é decisão de produto
[HIGH] Conexão global -> conexão por request em flask.g com teardown; create_app como composition root; NotificationService injetado no PedidoService
[HIGH] Debug, 0.0.0.0 e CORS fixos -> DEBUG=false, HOST=127.0.0.1, CORS_ORIGINS (default "*", comportamento original) via ambiente
[MEDIUM] Validação inconsistente -> mesmo validar() em create e update, checagem de tipo, quantidade inteira > 0, corpo ausente vira 400
[MEDIUM] N+1 -> itens de todos os pedidos num JOIN com IN; relatório numa query de agregação; produtos do pedido num SELECT IN
[MEDIUM] try/except com str(e) -> 17 blocos removidos; error handler central devolve {"erro": ...} e 500 genérico com traceback só no log
[MEDIUM] Serialização duplicada -> to_dict único por entidade e _montar único para as duas listagens de pedido
[LOW] Magic numbers -> CATEGORIAS_VALIDAS, NOME_MIN/MAX_CHARS, STATUS_*, FAIXAS_DESCONTO, API_VERSION
[LOW] print -> logging por módulo; "ENVIANDO EMAIL/SMS/PUSH" virou NotificationService
[LOW] Imports mortos -> removidos junto com os arquivos antigos
[LOW] Nomes -> produto_id/usuario_id internos; cursor2/cursor3 sumiram; parâmetro de rota "id" mantido

## Intentional Behavior Changes
- GET /usuarios e /usuarios/<id>: campo "senha" removido (vazava senha)
- GET /health: sem "secret_key", "debug" e "db_path"; "ambiente" vem de APP_ENV (default "desenvolvimento", antes era "producao" fixo)
- POST /admin/query: 404, rota removida (SQL arbitrário)
- POST /admin/reset-db: 403 sem X-Admin-Token válido
- POST /login com "admin@loja.com' --": 401 (antes autenticava como admin)
- GET /produtos/busca com payload de injeção: 200 com lista vazia (antes 500 com erro do sqlite)
- DELETE /produtos/<id> com pedidos: 409 (antes apagava e deixava itens órfãos)
- PUT /produtos/<id> agora aplica as mesmas regras do POST (nome 2..200, categoria válida); estoque precisa ser inteiro
- POST /pedidos: quantidade <= 0 ou não inteira dá 400 (antes quantidade negativa aumentava estoque); item repetido que estoura o estoque dá 400 sem gravar nada
- PUT /pedidos/<id>/status: pedido inexistente dá 404 (antes 200); corpo ausente dá 400 (antes 500)
- Erros 500 devolvem {"erro": "Erro interno"} sem a mensagem da exceção; 404/405 do Flask passam a ser JSON
- Servidor escuta em 127.0.0.1 com debug desligado por padrão

## Validation
  ✓ Application boots without errors (PORT=<livre> .venv/bin/python -W always app.py; zero traceback, zero deprecation)
  ✓ All endpoints respond as before (18/18 routes mantidas + /admin/query removida; 39 requisições, 33 idênticas em status e corpo, 6 DIFFs todos listados acima)
  ✓ Anti-pattern re-scan: 0 reais remaining (falsos positivos: f-string em sistema_model.py:18 com nomes de tabela fixos, join de condições com placeholders em produto_model.py:89, "senha" no validador que vai para o hash, um except no /health para manter o formato {"status":"erro"}, UPDATE por item em criar pedido porque a baixa condicional precisa ser por linha)

## How to Run
pip install -r requirements.txt
python app.py                      # http://127.0.0.1:5000
# opcional: cp .env.example .env e exportar as variáveis (ADMIN_TOKEN, SECRET_KEY, PORT...)

## Validation Checklist
### Fase 1: Análise
✓ Linguagem detectada corretamente (Python, .py e requirements.txt)
✓ Framework detectado corretamente (Flask 3.1.1, add_url_rule em app.py)
✓ Domínio descrito corretamente (e-commerce: produtos, usuários, pedidos, relatório)
✓ Número de arquivos condiz (4 .py, 780 linhas)
### Fase 2: Auditoria
✓ Relatório segue o template (blocos, Summary, Deprecated APIs, Total)
✓ Cada finding tem arquivo e linhas exatos (conferidos com cat -n/grep -n)
✓ Findings ordenados CRITICAL → LOW (6/4/4/4)
✓ Mínimo de 5 findings (18)
✓ Detecção de APIs deprecated incluída (nenhuma, lista do que foi checado)
✓ Skill pausou e pediu confirmação antes da Fase 3
### Fase 3: Refatoração
✓ Estrutura MVC (models/, controllers/, views/, services/, middlewares/)
✓ Configuração extraída (src/config/settings.py, re-scan AP-01/AP-11 zerado)
✓ Models abstraem dados (todo SQL está em src/models e src/database.py)
✓ Views/Routes separadas (5 blueprints em src/views)
✓ Controllers concentram o fluxo (nenhum SQL nem print em controllers)
✓ Error handling centralizado (src/middlewares/error_handler.py, testado com exceção forçada)
✓ Entry point claro (app.py raiz → create_app)
✓ Aplicação inicia sem erros (boot com -W always limpo)
✓ Endpoints originais respondem corretamente (39 requisições comparadas com a linha de base)
================================
```

A refatoração está pronta e validada. As 39 requisições da linha de base foram repetidas contra a app nova: 33 dão status e corpo idênticos, inclusive pedidos, itens, totais e o relatório de vendas. As outras 6 são as correções de segurança listadas em Intentional Behavior Changes. Também testei à parte, com um banco de teste:

- **Migração de senha:** um banco antigo com senha em texto puro aceita o login e regrava a senha com hash.
- **Pedido que falha no meio:** não grava nada nem baixa estoque (rollback).
- **Rota de reset:** só funciona com o token certo.
- **Erro inesperado:** um 500 não mostra mais a mensagem interna para o cliente.

Duas coisas ficaram de fora porque dependem de decisão sua:

- **Autenticação nas rotas de negócio:** /usuarios e /relatorios/vendas continuam abertas, como antes. Fechar exige criar sessão ou token, o que muda o contrato de todas as rotas.
- **Estoque no cancelamento:** cancelar um pedido continua sem devolver o estoque, porque antes é preciso definir o que acontece quando um pedido sai do status "cancelado".

Não fiz commit. Os arquivos antigos (`controllers.py`, `models.py`, `database.py`) foram apagados mas não estão staged, então `git status` mostra tudo como mudança local. Os logs e as saídas da validação estão em `$TMPDIR/refactor-arch-code-smells-project/`.
