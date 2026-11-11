# Auditoria: ecommerce-api-legacy (projeto 2)

Saída das Fases 1 e 2 da skill `/refactor-arch`, executada com `claude -p "/refactor-arch"` (Claude Code 2.1.322, modelo claude-opus-5-5) dentro de `ecommerce-api-legacy/`, sem edição. Sessão f50893ea-137d-4bcb-8e07-ee97df23944e, 105 s.

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js), versão não declarada (sem `engines`/`.nvmrc`; local: v23.1.0)
Framework:     Express ^4.18.2 (instalado 4.22.1)
Dependencies:  express, sqlite3
Database:      SQLite em memória (`new sqlite3.Database(':memory:')`), SQL cru com placeholders, schema e seed criados no boot
Domain:        LMS com fluxo de checkout (usuários, cursos, matrículas, pagamentos, log de auditoria)
Architecture:  Monolítica sem camadas, `AppManager` cria o banco, faz seed, registra rotas, decide pagamento e formata resposta na mesma classe
Source files:  3 files analyzed (~180 lines)
Entry point:   src/app.js (`npm start` → `node src/app.js`, porta 3000 fixa)
DB tables:     users, courses, enrollments, payments, audit_logs
Endpoints:     3 routes
================================

| Método | Caminho | Handler | Arquivo:linha |
|---|---|---|---|
| POST | /api/checkout | arrow inline (checkout) | src/AppManager.js:28 |
| GET | /api/admin/financial-report | arrow inline (relatório) | src/AppManager.js:80 |
| DELETE | /api/users/:id | arrow inline (exclusão) | src/AppManager.js:131 |

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4 (SQLite em memória)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Credenciais de produção hardcoded no código
ID: AP-01
File: src/utils.js:1-7
Locations: src/utils.js:3, src/utils.js:4, src/AppManager.js:45
Description: O objeto config fixa dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", dbUser: "admin_master" e smtpUser no código versionado. A chave do gateway ainda é usada em AppManager.js:45.
Impact: Qualquer pessoa com acesso ao repositório tem a chave live do gateway e a senha do banco; trocar o segredo exige commit e deploy, e o segredo fica no histórico do git para sempre.
Recommendation: Mover toda a configuração para variáveis de ambiente lidas num módulo src/config (T-01), com .env.example sem valores reais; remover os campos que nunca são lidos (ver AP-21).

### [CRITICAL] Número de cartão e chave do gateway impressos no log
ID: AP-06
File: src/AppManager.js:45
Description: console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) imprime o PAN completo vindo de req.body.card e a chave pk_live a cada checkout. Também é AP-20 (console.log no lugar de logger).
Impact: Todo agregador de log passa a guardar cartões em claro (violação de PCI-DSS) e a chave do gateway; quem lê logs consegue cobrar no nome da empresa.
Recommendation: Remover o log do cartão e da chave; se precisar rastrear, logar só os 4 últimos dígitos mascarados (T-12/T-01), dentro de um serviço de pagamento.

### [CRITICAL] Relatório financeiro e exclusão de usuário sem autenticação
ID: AP-04
File: src/AppManager.js:80
Locations: src/AppManager.js:131-137
Description: GET /api/admin/financial-report devolve receita por curso e nome de cada aluno; DELETE /api/users/:id apaga qualquer usuário. Nenhuma rota tem middleware de auth e o projeto inteiro não tem nenhum mecanismo de autenticação.
Impact: Qualquer cliente anônimo lê o faturamento e a lista de alunos pagantes, e consegue apagar usuários em sequência (DELETE /api/users/1, /2, ...).
Recommendation: Middleware de autorização admin por token vindo de env (ADMIN_API_TOKEN) aplicado às duas rotas (T-13).

### [CRITICAL] Senha com "hash" caseiro reversível e seed em texto puro
ID: AP-05
File: src/utils.js:17-23
Locations: src/AppManager.js:68, src/AppManager.js:18
Description: badCrypto repete Buffer.from(pwd).toString('base64').substring(0, 2) 10000 vezes e corta em 10 caracteres, ou seja, grava os 2 primeiros caracteres do base64 da senha repetidos. Sem pwd, a senha vira "123456" (linha 68). O seed grava pass '123' em claro (linha 18).
Impact: O "hash" depende só dos 2 primeiros caracteres da senha: qualquer senha que comece igual gera o mesmo valor, e o prefixo é recuperável decodificando base64. Vazamento do banco expõe as senhas na prática.
Recommendation: Trocar por crypto.scrypt com salt aleatório (T-06), num módulo de senha; seed também passa a gravar hash.

### [CRITICAL] God Class AppManager concentra banco, seed, rotas, pagamento e resposta
ID: AP-03
File: src/AppManager.js:4-139
Locations: src/AppManager.js:10-23, src/AppManager.js:25-137, src/AppManager.js:43-64
Description: A mesma classe cria a conexão (linha 7), o schema e o seed (10-23), registra as três rotas (25-137), decide a aprovação do pagamento por prefixo do cartão (46), cria usuário, matrícula, pagamento e auditoria, e monta as respostas HTTP. O handler de checkout tem 50 linhas e 6 níveis de aninhamento, com regra de negócio direto na rota (AP-07 incluído aqui).
Impact: Nenhuma regra pode ser testada sem subir Express e SQLite; qualquer mudança em pagamento mexe no mesmo arquivo das rotas e do schema.
Recommendation: Separar em config, database (conexão + schema + seed), models/repositories por tabela, services (checkout, relatório, usuários, pagamento), controllers e routes (T-03, T-04).

### [HIGH] Checkout grava em quatro tabelas sem transação
ID: AP-10
File: src/AppManager.js:50-61
Locations: src/AppManager.js:69-71, src/AppManager.js:46-48
Description: O usuário é criado (69) antes da decisão de pagamento (46-48); depois enrollments, payments e audit_logs são inseridos em callbacks separados, cada um com return no erro sem rollback. Um pagamento DENIED deixa o usuário novo criado.
Impact: Falha no INSERT de payments deixa matrícula sem pagamento (aluno com acesso de graça); pagamento recusado cria conta mesmo assim.
Recommendation: Envolver criação de usuário, matrícula, pagamento e auditoria em BEGIN/COMMIT/ROLLBACK num único método de serviço, decidindo o pagamento antes de qualquer escrita (T-09).

### [HIGH] Exclusão de usuário deixa matrículas e pagamentos órfãos
ID: AP-10
File: src/AppManager.js:133-135
Description: "DELETE FROM users WHERE id = ?" sem tratar enrollments e payments; a própria resposta admite: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." O schema (12-15) não tem FOREIGN KEY.
Impact: O relatório financeiro passa a mostrar alunos "Unknown" com valores pagos; receita fica atribuída a usuários inexistentes.
Recommendation: Apagar payments → enrollments → users numa transação e declarar FOREIGN KEY com PRAGMA foreign_keys = ON (T-09). A mensagem de resposta é mantida (contrato), ver plano.

### [HIGH] Infraestrutura instanciada dentro da classe, sem composition root
ID: AP-09
File: src/AppManager.js:7
Locations: src/app.js:8-10, src/AppManager.js:2
Description: O construtor faz new sqlite3.Database(':memory:') e o módulo importa config e helpers direto de ./utils; app.js só chama new AppManager(), initDb() e setupRoutes(app).
Impact: Impossível injetar um banco de teste ou um gateway de pagamento falso; o caminho do banco não é configurável.
Recommendation: Criar o banco a partir da config num createApp/composition root e injetar nos repositórios e serviços (T-05, T-03).

### [HIGH] Cache global mutável que cresce sem limite
ID: AP-08
File: src/utils.js:9-15
Locations: src/utils.js:10, src/AppManager.js:59
Description: let globalCache = {} é mutado por logAndCache(`last_checkout_${userId}`, course.title) a cada checkout e nunca lido; let totalRevenue = 0 também é estado de módulo exportado.
Impact: Memória cresce com cada usuário que compra, compartilhada entre requisições e sem uso; em múltiplas instâncias cada processo tem um cache diferente.
Recommendation: Remover o cache (não tem leitor) e o contador (T-05, AP-21).

### [MEDIUM] Relatório financeiro com N+1 (1 + C + 2E consultas)
ID: AP-12
File: src/AppManager.js:83-106
Locations: src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106
Description: Busca todos os cursos, depois enrollments por curso dentro do forEach (92) e, para cada matrícula, users (104) e payments (106) separadamente.
Impact: Com 50 cursos e 10.000 matrículas são ~20.051 consultas por chamada ao relatório.
Recommendation: Uma consulta com LEFT JOIN courses/enrollments/users/payments e agregação em memória (T-07).

### [MEDIUM] Erros de banco ignorados ou mascarados
ID: AP-15
File: src/AppManager.js:92-93
Locations: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133-135
Description: Em 92 o err é ignorado e enrollments.length explode com TypeError se a consulta falhar (derruba o processo, já que está num callback); 104/106/57 ignoram err; 38 responde 404 "Curso não encontrado" também para erro de banco; 133 responde sucesso mesmo com erro ou id inexistente. Não há error handler global.
Impact: Uma falha de SQLite no relatório mata o servidor inteiro; falhas reais aparecem como 404 ou sucesso.
Recommendation: Promisificar o acesso a banco, propagar erros com next(err) para um error handler central que devolve 500 (T-08).

### [MEDIUM] Callback hell com contadores manuais de pendência
ID: AP-17
File: src/AppManager.js:37-77
Locations: src/AppManager.js:83-128, src/AppManager.js:86, src/AppManager.js:93, src/AppManager.js:117-121
Description: Checkout aninha 6 níveis de callback (db.get → db.get → run → run → run) e mistura arrow com function() + const self = this para manter o lastID; o relatório controla término com coursesPending-- e enrPending--.
Impact: A ordem dos cursos no relatório depende de qual callback termina primeiro (no boot de hoje veio Docker antes de Clean Architecture); qualquer novo passo no checkout aumenta o aninhamento.
Recommendation: Wrapper de promessas sobre sqlite3 (get/all/run) e serviços async/await (T-10).

### [MEDIUM] Validação de entrada mínima no checkout e no delete
ID: AP-13
File: src/AppManager.js:35
Locations: src/AppManager.js:68, src/AppManager.js:132
Description: Só checa presença de usr, eml, c_id e card; pwd ausente vira "123456" silenciosamente (68); card não é checado como string (cc.startsWith quebra com número, gerando 500 HTML); eml não tem formato; :id do DELETE não é validado.
Impact: card: 4111 (número JSON) derruba a rota com TypeError; usuários criados com senha padrão conhecida.
Recommendation: Validador do payload de checkout num módulo próprio, mantendo 400 "Bad Request" para entrada inválida (T-04, T-14).

### [MEDIUM] Porta fixa no código
ID: AP-11
File: src/utils.js:6
Locations: src/app.js:12
Description: port: 3000 fixo em config. Severidade ajustada de HIGH para MEDIUM: não há debug mode nem CORS aberto, o único sinal é a porta.
Impact: Não dá para subir duas instâncias nem configurar a porta no deploy sem editar código.
Recommendation: PORT via env com default 3000 (T-01).

### [LOW] Código e configuração mortos
ID: AP-21
File: src/AppManager.js:2
Locations: src/utils.js:2, src/utils.js:3, src/utils.js:5, src/utils.js:10, src/utils.js:25
Description: totalRevenue é importado e nunca usado; dbUser, dbPass e smtpUser nunca são lidos (banco é :memory:, não há SMTP); globalCache é exportado sem leitor.
Impact: Dá a impressão de que existe integração com banco remoto e e-mail que não existe; segredo mantido sem necessidade.
Recommendation: Remover.

### [LOW] Regra de pagamento e status como strings soltas
ID: AP-18
File: src/AppManager.js:46
Locations: src/AppManager.js:48, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:19
Description: Aprovação decidida por cc.startsWith("4"); status "PAID"/"DENIED" repetidos em 46, 48 e 108; senha padrão "123456"; 10000 iterações sem nome.
Impact: Mudar a regra do gateway simulado ou o nome de um status exige caçar strings em vários pontos.
Recommendation: Constantes PAYMENT_STATUS e APPROVED_CARD_PREFIX no módulo de pagamento (T-14).

### [LOW] Nomes pouco descritivos
ID: AP-19
File: src/AppManager.js:29-33
Locations: src/AppManager.js:26, src/utils.js:17, src/AppManager.js:4
Description: let u, e, p, cid, cc; const self = this; função badCrypto; classe AppManager e módulo utils com regra de negócio.
Impact: Leitura do checkout exige mapear mentalmente cada letra para o campo da API.
Recommendation: Renomear internamente (userName, email, password, courseId, cardNumber) mantendo os campos externos usr/eml/pwd/c_id/card (T-14).

### [LOW] console.log no lugar de logger
ID: AP-20
File: src/utils.js:13
Locations: src/app.js:13, src/AppManager.js:45
Description: "[LOG] Salvando no cache" e o aviso de boot usam console.log sem nível.
Impact: Sem nível, não dá para silenciar em teste nem filtrar em produção.
Recommendation: Logger mínimo com nível configurável (T-15).

## Deprecated APIs
No deprecated API usage found. Checked: new Buffer, url.parse, crypto.createCipher, fs.exists, body-parser, req.param, res.send(status)/res.json(status, body), app.del; boot com node --trace-deprecation sem avisos.

================================
Total: 18 findings
================================
```

Uma observação antes de seguir: proteger o relatório e o DELETE com token admin (AP-04) muda o contrato, porque chamadas sem `Authorization` passam a receber 401. Vou tratar isso como mudança intencional de segurança e documentar.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
