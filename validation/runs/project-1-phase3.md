# Fase 3: code-smells-project (projeto 1)

Saída da Fase 3 da skill `/refactor-arch` depois da resposta `y`, retomando a sessão das Fases 1 e 2 com `claude -p "y" --resume <sessão>`. 5.7 min, 25 turnos. Segunda execução, com o AP-04 corrigido.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
code-smells-project/
├── app.py                       # entry point: create_app(Settings()) + app.run
├── .env.example
├── README.md
├── requirements.txt             # sem mudança (itsdangerous e werkzeug já vêm com o Flask)
└── src/
    ├── app.py                   # create_app: config, CORS, banco, PedidoService, blueprints, error handlers
    ├── errors.py                # ValidationError, UnauthorizedError, ForbiddenError, NotFoundError, ConflictError
    ├── database.py              # conexão por requisição em flask.g, schema com FKs, seed, migração de senhas
    ├── config/settings.py
    ├── models/                  # produto_model, usuario_model, pedido_model, sistema_model
    ├── services/                # pedido_service, relatorio_service, notification_service, auth_service
    ├── controllers/             # produto, usuario, pedido, relatorio, sistema
    ├── views/                   # um Blueprint por recurso
    └── middlewares/             # auth.py (require_admin, require_admin_or_self), error_handler.py
```

## Changes by Finding
- [CRITICAL] Endpoints sem autenticação (AP-04) -> `require_admin` (header `X-Admin-Token` comparado com `hmac.compare_digest`, ou Bearer de usuário admin) em `/usuarios`, `/pedidos`, `PUT /pedidos/<id>/status`, `/relatorios/vendas` e `/admin/reset-db`. `/usuarios/<id>` e `/pedidos/usuario/<id>` aceitam admin ou o Bearer do próprio usuário. `POST /admin/query` removida. O login agora emite um token assinado com `itsdangerous` que expira em 1h.
- [CRITICAL] SQL injection (AP-02) -> todas as queries usam placeholders `?`, e a busca monta as condições junto com a lista de parâmetros.
- [CRITICAL] SECRET_KEY hardcoded (AP-01) -> lida de `SECRET_KEY`; sem ela, gera uma chave aleatória e loga um aviso. O `/health` não devolve mais `secret_key`, `db_path` nem `debug`.
- [CRITICAL] Senhas na resposta (AP-06) -> `usuario_model.to_dict` sem `senha`; logs sem email.
- [CRITICAL] Senha em texto puro (AP-05) -> `generate_password_hash`/`check_password_hash` no cadastro, no seed e no login. Bancos antigos são migrados para scrypt no boot (testado com um `loja.db` criado pelo código original: 3 senhas migradas e o login continuou funcionando).
- [CRITICAL] God File models.py (AP-03) -> dividido em models por entidade, services, controllers, views e middlewares.
- [HIGH] Checkout sem transação e itens órfãos (AP-10) -> `pedido_model.criar` roda num `with db:` com baixa condicional `WHERE estoque >= ?` e rollback. O schema ganhou FKs com `PRAGMA foreign_keys = ON`. Excluir produto que tem pedidos retorna 409. Cancelar pedido continua só notificando "devolver estoque": não mudei essa regra de negócio.
- [HIGH] Debug/0.0.0.0/CORS fixos (AP-11) -> `DEBUG=false` e `HOST=127.0.0.1` por padrão, `CORS_ORIGINS` configurável (default `*`, como no original).
- [HIGH] Conexão global (AP-08) -> conexão por requisição em `flask.g` com teardown; acabou o `global`.
- [HIGH] Sem composition root (AP-09) -> `create_app(settings)`. Os models recebem a conexão como parâmetro e o `NotificationService` é injetado no `PedidoService`.
- [HIGH] Regra de negócio no controller (AP-07) -> validação foi para os models, checkout e status para o `PedidoService`, desconto para o `relatorio_service`. Os controllers ficaram com até ~15 linhas.
- [MEDIUM] N+1 (AP-12) -> pedidos com uma query mais um JOIN de itens/produtos; relatório com uma query `SUM(CASE ...)`; health com uma query de subcontagens.
- [MEDIUM] Validação inconsistente (AP-13) -> `produto_model.validar` é usado no create e no update, com checagem de tipo. Pedido exige `produto_id` inteiro e `quantidade` inteira positiva. Corpo ausente agora dá 400.
- [MEDIUM] Duplicação (AP-14) -> um `to_dict` por entidade e uma única `pedido_model.listar(usuario_id=None)`.
- [MEDIUM] Erro genérico (AP-15) -> error handler central. Erros de domínio mantêm o formato `{"erro"}` (com `"sucesso": false` onde o original tinha), e o 500 responde "Erro interno" com o detalhe só no log.
- [LOW] print como log (AP-20) -> `logging`, e as notificações viraram métodos do `NotificationService`.
- [LOW] Magic numbers (AP-18) -> `CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `NOME_MIN/MAX_CARACTERES`, `API_VERSION`.
- [LOW] Imports mortos (AP-21) -> removidos junto com os arquivos antigos.
- [LOW] Nomes ruins (AP-19) -> `cursor2/cursor3/prod` sumiram. O parâmetro `id` ficou só nas rotas, porque é o nome da variável na URL.

## Intentional Behavior Changes
- As rotas protegidas respondem 403 sem credencial e o mesmo de antes com `X-Admin-Token` (7 rotas, com o status e o formato da linha de base).
- `POST /admin/query` foi removida e responde 404.
- `POST /login` com `"admin@loja.com' --"` passou de 200 (bypass por SQLi) para 401.
- `POST /login` ganhou o campo `token` no topo da resposta.
- `GET /usuarios` e `GET /usuarios/<id>` não devolvem mais `senha`.
- `GET /health` perdeu `secret_key`, `db_path` e `debug`, e `ambiente` vem de `APP_ENV` (default `desenvolvimento`).
- Entrada inválida que antes dava 500 agora dá 400: `preco_min=abc`, preço não numérico, `quantidade` ausente ou negativa, corpo vazio no login e no status.
- `PUT /produtos/<id>` passou a aplicar as mesmas regras de nome e categoria do POST.
- `POST /pedidos` com `usuario_id` inexistente responde 400 em vez de criar um pedido órfão.
- `DELETE /produtos/<id>` de produto com pedidos responde 409.
- O servidor sobe em `127.0.0.1` com debug desligado por padrão.

## Validation
  ✓ Application boots without errors (`PORT=<p> ADMIN_TOKEN=... python -W always app.py`, sem traceback e sem aviso de deprecation)
  ✓ All endpoints respond as before (18/19 rotas presentes e 34/45 requisições com status idêntico; as 11 diferenças são exatamente as mudanças intencionais acima: 7× 403 sem token, 2× `/admin/query` 404, login SQLi 401, `preco_min=abc` 400)
  ✓ Anti-pattern re-scan: 0 remaining (dois `execute(f...)` só interpolam constantes internas, sempre com parâmetros; o único `except Exception` está no health check, que precisa responder `{"status":"erro"}`; as senhas do seed fictício continuam no código, mas são gravadas com hash)

## How to Run
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python app.py                       # http://127.0.0.1:5000
ADMIN_TOKEN=troque-isto .venv/bin/python app.py
curl -H "X-Admin-Token: troque-isto" http://127.0.0.1:5000/relatorios/vendas
```

## Validation Checklist
Fase 1: Análise
- ✓ Linguagem detectada corretamente: Python, pelo requirements.txt e pelos 4 `.py`
- ✓ Framework detectado corretamente: Flask 3.1.1, confirmado no import
- ✓ Domínio da aplicação descrito corretamente: e-commerce com produtos, usuários, pedidos e itens
- ✓ Número de arquivos analisados condiz com a realidade: 4 arquivos, 780 linhas

Fase 2: Auditoria
- ✓ Relatório segue o template definido nos arquivos de referência
- ✓ Cada finding tem arquivo e linhas exatos, conferidos com `cat -n` e `grep -n`
- ✓ Findings ordenados por severidade (6 CRITICAL, 5 HIGH, 4 MEDIUM, 4 LOW)
- ✓ Mínimo de 5 findings identificados: 19
- ✓ Detecção de APIs deprecated incluída: nenhuma, verificado com `-W always`
- ✓ Skill pausou e pediu confirmação antes da Fase 3

Fase 3: Refatoração
- ✓ Estrutura de diretórios segue padrão MVC: `src/{models,views,controllers,services,middlewares,config}`
- ✓ Configuração extraída para módulo de config: `src/config/settings.py`, sem segredo literal
- ✓ Models criados para abstrair dados: 4 models com SQL parametrizado
- ✓ Views/Routes separadas para roteamento: 5 blueprints
- ✓ Controllers concentram o fluxo da aplicação
- ✓ Error handling centralizado: `middlewares/error_handler.py`
- ✓ Entry point claro: `app.py` com `create_app`
- ✓ Aplicação inicia sem erros
- ✓ Endpoints originais respondem corretamente: 34/45 iguais, e as 11 diferenças são todas intencionais
================================

Algumas coisas que você precisa saber:

- **Index do git:** o `git rm --cached` que usei para apagar `controllers.py`, `models.py` e `database.py` também alterou o index que você tinha staged (essas três entradas "A" saíram). Os arquivos novos em `src/` e o `.env.example` estão untracked, e as deleções de `src/` que você tinha staged continuam lá. Não commitei nada.
- **SECRET_KEY no shell:** seu shell já tem `SECRET_KEY` exportada. Para conferir o aviso de chave aleatória, rodei o boot final com `env -u SECRET_KEY`.
- **Arquivos temporários:** o smoke e os bancos de teste ficaram em `$TMPDIR/refactor-arch-code-smells-project`. Nenhum `loja.db` foi criado no projeto.
