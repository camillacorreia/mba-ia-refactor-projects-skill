# Fase 3: ecommerce-api-legacy (projeto 2)

Saída da Fase 3 da skill `/refactor-arch` depois da resposta `y`, retomando a sessão das Fases 1 e 2 com `claude -p "y" --resume <sessão>`. 4.7 min, 40 turnos, US$ 1.93.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api.http
├── package.json
└── src/
    ├── app.js                      # entry point + composition root (createApp)
    ├── errors.js                   # AppError, ValidationError, PaymentDeclinedError, ForbiddenError, NotFoundError
    ├── config/index.js
    ├── database/
    │   ├── connection.js           # get/all/run com Promise + transaction() em fila
    │   └── schema.js               # CREATE TABLE com FKs + seed
    ├── models/                     # user, course, enrollment, payment, auditLog
    ├── services/                   # checkout, financialReport, user, paymentGateway
    ├── validators/checkout.validator.js
    ├── controllers/                # checkout, report, user
    ├── routes/index.js
    ├── middlewares/                # adminAuth, asyncHandler, errorHandler
    └── lib/                        # logger, password

## Changes by Finding
[CRITICAL] Credenciais hardcoded -> config/index.js lê PORT, DB_PATH, PAYMENT_GATEWAY_KEY, ADMIN_TOKEN, LOG_LEVEL do ambiente; pk_live, dbPass, dbUser e smtpUser removidos
[CRITICAL] Cartão e chave no log -> gateway loga só card=****4444; a chave nunca vai para log
[CRITICAL] Rotas admin sem auth -> middleware adminAuth (X-Admin-Token comparado com timingSafeEqual); sem ADMIN_TOKEN responde 403
[CRITICAL] Hash caseiro de senha -> crypto.scrypt com salt (scrypt$salt$hash); seed também com hash; pwd ausente vira senha aleatória em vez de "123456"
[CRITICAL] God Class AppManager -> quebrada em config/database/models/services/controllers/routes; AppManager.js removido
[HIGH] Checkout sem transação -> pagamento decidido antes de qualquer escrita; user + enrollment + payment + audit numa transação com ROLLBACK
[HIGH] Delete deixa órfãos -> FKs com ON DELETE CASCADE + PRAGMA foreign_keys = ON, dentro de transação
[HIGH] Infra instanciada na classe -> openDatabase no composition root, tudo injetado por factory
[HIGH] Cache global mutável -> globalCache, logAndCache e totalRevenue removidos (não tinham leitor)
[MEDIUM] N+1 no relatório -> uma consulta com LEFT JOIN, agregação em memória
[MEDIUM] Erros ignorados -> asyncHandler + errorHandler central; 500 "Erro interno" com stack só no log
[MEDIUM] Callback hell -> async/await sobre helpers com Promise; contadores *Pending removidos
[MEDIUM] Validação mínima -> checkout.validator (strings não vazias, c_id inteiro, pwd string opcional); :id do DELETE validado
[MEDIUM] Porta fixa -> PORT via env, default 3000
[LOW] Código morto -> totalRevenue, dbUser, dbPass, smtpUser, globalCache removidos; utils.js removido
[LOW] Magic strings -> PAYMENT_STATUS, APPROVED_CARD_PREFIX, VISIBLE_CARD_DIGITS, UNKNOWN_STUDENT
[LOW] Nomes ruins -> userName/email/password/courseId/cardNumber internamente; campos usr/eml/pwd/c_id/card mantidos na API; self = this removido
[LOW] console.log -> lib/logger.js com nível (LOG_LEVEL)

## Intentional Behavior Changes
- GET /api/admin/financial-report e DELETE /api/users/:id: 403 "Acesso negado" sem X-Admin-Token válido (antes 200 para qualquer um)
- DELETE /api/users/:id: corpo "Usuário deletado" (a mensagem antiga dizia que os dados ficavam sujos, o que deixou de ser verdade); id inexistente agora 404 "Usuário não encontrado", id não numérico 400
- DELETE apaga matrículas e pagamentos do usuário em cascata: o relatório deixa de mostrar "Unknown" e a receita daquele aluno sai do total (antes ficava órfã)
- DELETE grava uma linha em audit_logs
- Checkout recusado não cria mais o usuário (antes criava antes de decidir o pagamento)
- Checkout com card não string ou c_id não inteiro: 400 "Bad Request" (antes card numérico derrubava o processo inteiro, c_id lixo dava 404)
- JSON malformado: 400 "Bad Request" em texto (antes página HTML de erro do Express)
- Erros de banco: 500 "Erro interno" único (antes "Erro DB", "Erro Matrícula" etc.)
- Relatório ordenado por curso e matrícula (antes a ordem dependia de qual callback terminava primeiro)

## Validation
  ✓ Application boots without errors (PORT=3000 node --trace-deprecation src/app.js, sem nenhuma outra variável; nenhum aviso de deprecation)
  ✓ All endpoints respond as before (8/8 requisições da spec: 5 de checkout idênticas em status, formato e corpo; 3 admin mudam para 403 sem token, intencional. Com ADMIN_TOKEN, relatório e delete devolvem os mesmos dados da linha de base)
  ✓ Anti-pattern re-scan: 0 remaining (hits restantes são falsos positivos: base64url em lib/password.js:18 gera senha aleatória, console.* só dentro do logger e no erro fatal de boot em app.js:70, loops em schema.js:37 e financialReport.service.js:13 não fazem consulta)

## How to Run
npm install
npm start                               # porta 3000, SQLite em memória com seed
ADMIN_TOKEN=um-token-local npm start    # habilita rotas admin (header X-Admin-Token)

## Validation Checklist
### Fase 1: Análise
  ✓ Linguagem detectada corretamente: JavaScript/Node, package.json sem typescript
  ✓ Framework detectado corretamente: Express ^4.18.2 (4.22.1 instalado)
  ✓ Domínio descrito corretamente: LMS com checkout (users, courses, enrollments, payments, audit_logs)
  ✓ Número de arquivos condiz: 3 arquivos, 180 linhas (wc -l)
### Fase 2: Auditoria
  ✓ Relatório segue o template: blocos ###, Summary 5/4/5/4 = Total 18
  ✓ Cada finding tem arquivo e linhas exatos: conferidos com cat -n e grep -n
  ✓ Findings ordenados CRITICAL → LOW
  ✓ Mínimo de 5 findings: 18
  ✓ Detecção de deprecated incluída: nenhuma encontrada, com lista checada e boot com --trace-deprecation
  ✓ Skill pausou e pediu confirmação antes da Fase 3
### Fase 3: Refatoração
  ✓ Estrutura MVC: models/, controllers/, routes/ (view), services/, middlewares/
  ✓ Config extraída: config/index.js, re-scan AP-01 sem ocorrências
  ✓ Models criados: 5 models, um por tabela
  ✓ Routes separadas: routes/index.js só mapeia rota → controller
  ✓ Controllers concentram o fluxo: 3 controllers, maior ação com 4 linhas
  ✓ Error handling centralizado: middlewares/errorHandler.js + asyncHandler
  ✓ Entry point claro: src/app.js, mesmo npm start
  ✓ Aplicação inicia sem erros: boot limpo sem variáveis
  ✓ Endpoints originais respondem: 5/5 iguais, 3 com 403 intencional, iguais à linha de base com token
================================
```

A refatoração está aplicada no working tree e nada foi commitado. `AppManager.js` e `utils.js` foram apagados, mas não estão staged. Os artefatos da validação ficaram fora do projeto, em `/tmp/refactor-arch-ecommerce-api-legacy/`.

Alguns pontos merecem atenção:

- **Crash na linha de base:** o Phase 2 dizia que `card` numérico gerava 500. Na verdade derrubava o processo inteiro. Agora responde 400.
- **Auth diferente do anunciado:** no fim do Phase 2 falei em `Authorization` com `ADMIN_API_TOKEN`. Acabei usando `X-Admin-Token` com `ADMIN_TOKEN`, que é o que o playbook (T-13) define.
- **Testes além do smoke:** o smoke não enxerga efeito no banco, então rodei um script à parte. Ele confirmou quatro coisas: checkout recusado não cria usuário, 20 checkouts simultâneos dão 200 sem colidir na transação, falha no INSERT de payments desfaz usuário e matrícula, e o delete não deixa órfãos.
- **Leitura no meio de transação:** o banco usa uma conexão só. As escritas entram numa fila, mas uma leitura do relatório pode enxergar um checkout ainda não commitado. Com SQLite em memória isso é aceitável. Se `DB_PATH` passar a apontar para arquivo com carga real, vale abrir uma conexão por transação.
- **Cascata no delete:** apagar um usuário agora apaga os pagamentos dele, e com eles o histórico financeiro. Se isso precisa ser preservado, o caminho é soft delete. Não fiz porque muda o modelo de dados além do escopo do finding.
