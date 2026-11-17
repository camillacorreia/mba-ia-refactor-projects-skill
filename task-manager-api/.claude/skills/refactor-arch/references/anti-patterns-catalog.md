# Catálogo de anti-patterns (Fase 2)

Cada entrada tem: severidade padrão, o que é, sinais de detecção (com `grep` quando dá), falsos positivos e a transformação do playbook que resolve.

## Escala de severidade

| Severidade | Critério |
|---|---|
| CRITICAL | Falha grave de arquitetura ou segurança: impede o funcionamento correto, expõe dado sensível (credencial hardcoded, SQL injection, senha recuperável) ou viola completamente a separação de responsabilidades (God Class com banco, regra de negócio e roteamento juntos) |
| HIGH | Violação forte de MVC ou SOLID que dificulta muito manutenção e teste: regra de negócio pesada em controller/rota, acoplamento sem injeção de dependência, estado global mutável, escrita multi-etapa sem transação |
| MEDIUM | Padronização, duplicação, performance moderada: N+1, validação ausente, tratamento de erro inadequado, API deprecated, callbacks aninhados |
| LOW | Legibilidade: nomes ruins, magic numbers, `print` como log, import ou código morto |

## Índice

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP-01 | Credenciais e segredos hardcoded | CRITICAL |
| AP-02 | SQL injection por concatenação | CRITICAL |
| AP-03 | God Class / God File | CRITICAL |
| AP-04 | Endpoint perigoso sem autenticação | CRITICAL |
| AP-05 | Senha em texto puro ou hash fraco | CRITICAL |
| AP-06 | Exposição de dados sensíveis em resposta ou log | CRITICAL |
| AP-07 | Regra de negócio em rota/controller (fat controller) | HIGH |
| AP-08 | Estado global mutável | HIGH |
| AP-09 | Acoplamento sem injeção de dependência | HIGH |
| AP-10 | Escrita multi-etapa sem transação ou sem integridade referencial | HIGH |
| AP-11 | Modo debug e configuração insegura no código | HIGH |
| AP-12 | Consultas N+1 | MEDIUM |
| AP-13 | Validação ausente, inconsistente ou duplicada | MEDIUM |
| AP-14 | Duplicação de lógica e serialização | MEDIUM |
| AP-15 | Tratamento de erro genérico e não centralizado | MEDIUM |
| AP-16 | Uso de API deprecated | MEDIUM |
| AP-17 | Callbacks aninhados (callback hell) | MEDIUM |
| AP-18 | Magic numbers e strings | LOW |
| AP-19 | Nomes pouco descritivos | LOW |
| AP-20 | `print`/`console.log` no lugar de logging | LOW |
| AP-21 | Import, variável ou código morto | LOW |

---

## AP-01 Credenciais e segredos hardcoded (CRITICAL)

Segredo literal no código: `SECRET_KEY`, senha de banco, senha SMTP, chave de gateway de pagamento, token de API.

Sinais:
```bash
grep -rn -i -E "(secret|password|passwd|pwd|pass|api_?key|token|private_?key|gateway_?key)[\"']?\s*[:=]\s*[\"'][^\"']{3,}" --include=*.py --include=*.js --include=*.ts .
grep -rn -E "pk_live_|sk_live_|AKIA[0-9A-Z]{16}" .
```
Também conta: segredo devolvido numa resposta (ex.: `/health` que retorna `secret_key`), que é AP-01 e AP-06 ao mesmo tempo. Reporte como AP-01 e cite AP-06 no texto.

Falsos positivos: senhas de seed de desenvolvimento para usuários fictícios são MEDIUM, não CRITICAL, desde que fiquem só no seed. Valores lidos de `os.environ`/`process.env` não contam.

Correção: playbook T-01.

## AP-02 SQL injection por concatenação (CRITICAL)

Valor vindo do usuário entra na string SQL por concatenação, f-string, `%` ou template literal.

Sinais:
```bash
grep -rn -E "execute\(\s*[\"'].*[\"']\s*\+|execute\(\s*f[\"']|execute\([^,)]*%\s" --include=*.py .
grep -rn -E "\"(SELECT|INSERT|UPDATE|DELETE)[^\"]*\"\s*\+|'(SELECT|INSERT|UPDATE|DELETE)[^']*'\s*\+" --include=*.py --include=*.js .
grep -rn -E "\`(SELECT|INSERT|UPDATE|DELETE)[^\`]*\\$\{" --include=*.js --include=*.ts .
```
Montagem dinâmica de `WHERE` (`query += " AND nome LIKE '%" + termo + "%'"`) também conta. `str(id)` concatenado continua sendo injeção se o valor vem de input não tipado.

Falsos positivos: placeholders (`?`, `%s` passado como segundo argumento, `:nome`), ORMs com filtros (`filter_by`, `.like(f"%{q}%")` no SQLAlchemy é parametrizado).

Um finding só, com todas as ocorrências em `Locations`.

Correção: T-02.

## AP-03 God Class / God File (CRITICAL)

Uma unidade concentra três ou mais destas responsabilidades: definição de rotas, acesso a banco (SQL, schema, seed), regra de negócio, integração externa (pagamento, e-mail), formatação de resposta. Ou um arquivo de "models" que contém regra de negócio, SQL e formatação de vários domínios diferentes.

Sinais: classe com nome genérico (`AppManager`, `Manager`, `Utils`, `Helper`) que recebe `app` e registra rotas e também executa SQL; arquivo com mais de ~250 linhas cobrindo várias entidades; um método com mais de ~50 linhas ou mais de 3 níveis de aninhamento.

Correção: T-03.

## AP-04 Endpoint perigoso sem autenticação (CRITICAL)

Rota que exige privilégio e não verifica identidade nem permissão. Entram aqui cinco grupos, e cada um vira location do mesmo finding:

1. Manutenção e administração: executar SQL arbitrário, resetar ou semear o banco, limpar cache.
2. Relatórios da operação: faturamento, vendas, resumo geral, métricas de todos os usuários.
3. Gestão de usuários e dados de terceiros: listar todos os usuários, ver o cadastro de outro usuário, alterar ou apagar usuário, listagens globais com dados pessoais de clientes.
4. Escalada de privilégio: o cadastro público ou a atualização aceita do corpo da requisição um campo de papel (`role`, `tipo`, `perfil`, `is_admin`) e grava o valor recebido.
5. Credencial falsa: login que devolve token fixo, previsível ou que nada valida (`"fake-jwt-token-" + id`, `"token-" + email`).

Sinais:
```bash
grep -rn -E "/admin|reset|/query|execute\(\s*(query|sql|dados)" --include=*.py --include=*.js .
grep -rn -i -E "relatorio|report|summary|financ|/usuarios|/users" --include=*.py --include=*.js .
grep -rn -E "\b(role|tipo|perfil|is_admin)\b" --include=*.py --include=*.js .   # depois leia o handler: o valor vem do corpo?
grep -rn -i -E "fake|token['\"]?\s*[:=].*\+" --include=*.py --include=*.js .
```
Para cada rota encontrada, verifique se há decorator ou middleware de auth. Rota de negócio comum (catálogo de produtos, CRUD de tarefas, checkout) não entra neste finding; a ausência de autenticação nelas pode ser registrada como observação no relatório, sem mudar o contrato.

Falso positivo: rota atrás de middleware de autenticação com checagem de papel.

Correção: T-13. Este finding é sempre corrigido na Fase 3; "not fixed" não é resposta aceita para ele.

## AP-05 Senha em texto puro ou hash fraco (CRITICAL)

Senha gravada sem hash, com MD5/SHA1 sem salt, ou com "criptografia" caseira (base64, loop de substring).

Sinais:
```bash
grep -rn -E "md5\(|sha1\(|hashlib\.(md5|sha1)|createHash\(['\"](md5|sha1)" .
grep -rn -i -E "base64|btoa\(" --include=*.js --include=*.py .
grep -rn -i -E "senha\s*=\s*'\"?\s*\+|AND senha =|pass(word)?\s*=\s*\?" .
```
Compare como a senha é gravada no cadastro e como é conferida no login. Comparação direta `senha = ?` no SQL indica texto puro.

Correção: T-06.

## AP-06 Exposição de dados sensíveis em resposta ou log (CRITICAL)

Resposta da API inclui senha, hash de senha, segredo ou configuração interna; log imprime número de cartão, senha ou chave.

Sinais: `to_dict()` ou dicionário de serialização com `password`/`senha`/`pass`; `SELECT *` de usuários devolvido direto; `console.log`/`print` com `card`, `cc`, `senha`, `key`.

Correção: T-12 (serialização) e T-01 (segredos).

## AP-07 Regra de negócio em rota/controller (HIGH)

A função que trata a requisição calcula, decide e persiste: valida regras de domínio, calcula totais e descontos, decide status, dispara notificações e monta a resposta, tudo no mesmo corpo.

Sinais: handler com mais de ~30 linhas; `if` de regra de negócio (faixas de desconto, transição de status, cálculo de atraso) dentro do handler; handler que chama banco diretamente (`db.session`, `cursor.execute`, `this.db.run`) em vez de um model/serviço.

Correção: T-04.

## AP-08 Estado global mutável (HIGH)

Variável de módulo alterada em runtime e compartilhada entre requisições: conexão global (`db_connection = None` + `global`), cache em dicionário global, lista de notificações em memória, contadores.

Sinais:
```bash
grep -rn -E "^\s*global\s+\w+" --include=*.py .
grep -rn -E "^(let|var)\s+\w+\s*=\s*(\{\}|\[\]|0|null)" --include=*.js .
```
Inclua também instância criada no import e mutada depois (`self.notifications = []` num singleton).

Correção: T-05.

## AP-09 Acoplamento sem injeção de dependência (HIGH)

Classe ou função instancia sua própria infraestrutura (`new sqlite3.Database(...)` no construtor, `smtplib.SMTP(...)` dentro do serviço, `get_db()` chamado de dentro de cada função), o que impede trocar a implementação ou testar isolado.

Sinais: `new X(` de infraestrutura dentro de construtor de classe de domínio; import de driver de banco em controller; ausência de app factory / composition root.

Correção: T-05 (composition root) e T-03.

## AP-10 Escrita multi-etapa sem transação ou integridade (HIGH)

Operação que lê, valida e grava em várias tabelas sem transação (cabeçalho + itens + baixa de saldo; cadastro + cobrança), ou exclusão que deixa registros órfãos (deletar a entidade pai e manter os filhos).

Sinais: vários `INSERT`/`UPDATE` seguidos com um único `commit` no fim e `return` de erro no meio do caminho; checagem de estoque separada da baixa; `DELETE` de entidade pai sem tratar filhos; mensagem como "ficaram sujos no banco".

Correção: T-09.

## AP-11 Modo debug e configuração insegura no código (HIGH)

`debug=True`, `DEBUG = True` ou `app.run(debug=True, host="0.0.0.0")` fixos no código; CORS liberado para qualquer origem sem configuração; porta fixa. O debugger do Werkzeug exposto em `0.0.0.0` permite execução de código remoto.

Sinais:
```bash
grep -rn -E "debug\s*=\s*True|DEBUG\"?\]?\s*=\s*True|host\s*=\s*[\"']0\.0\.0\.0" .
grep -rn -E "CORS\(app\)|cors\(\)" .
```

Correção: T-01.

## AP-12 Consultas N+1 (MEDIUM)

Uma consulta para a lista e mais uma (ou duas) por item dentro do laço.

Sinais: `execute`/`query`/`db.get`/`.query.get(` dentro de `for`/`forEach`; acesso a relacionamento lazy dentro de laço (`len(parent.children)`, `item.owner.name`); contagem por item (`Child.query.filter_by(parent_id=p.id).count()` dentro do laço); várias `COUNT(*)` separadas que um `GROUP BY` resolveria.

Correção: T-07.

## AP-13 Validação ausente, inconsistente ou duplicada (MEDIUM)

Rota de escrita sem validação de tipo/presença; validação de criação diferente da de atualização (create exige campos que update aceita vazios); mesma lista de valores válidos repetida em vários arquivos; `request.get_json()` usado sem checar `None`.

Correção: T-04 (validação no model/schema) e T-14.

## AP-14 Duplicação de lógica e serialização (MEDIUM)

O mesmo bloco aparece em dois ou mais lugares: montagem manual de dicionário com os mesmos campos, cálculo de "atrasado", checagem de status, a mesma query.

Sinais: blocos de 5+ linhas iguais ou quase iguais; função utilitária ou método de model que já existe (`to_dict`, um validador, um `is_<estado>()`) mas não é usado, e a lógica é reescrita na rota.

Correção: T-12 e T-04.

## AP-15 Tratamento de erro genérico e não centralizado (MEDIUM)

`except:` sem tipo, `except Exception` que devolve `str(e)` ao cliente, callback que ignora `err`, cada rota com seu próprio `try/except` repetido, ausência de error handler global.

Sinais:
```bash
grep -rn -E "except\s*:|except Exception as e:" --include=*.py .
grep -rn -E "\"erro\":\s*str\(e\)|'error':\s*str\(e\)" --include=*.py .
grep -rn -E "\(err(,|\))" --include=*.js . # depois confira se err é tratado
```

Correção: T-08.

## AP-16 Uso de API deprecated (MEDIUM)

Chamada a API marcada como obsoleta pela linguagem ou pela biblioteca na versão instalada. Sempre confirme a versão no manifesto e, quando possível, rode com avisos ligados (`python -W always`, `node --trace-deprecation`).

| Stack | Deprecated | Equivalente moderno |
|---|---|---|
| Python 3.12+ | `datetime.utcnow()`, `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)`, `datetime.fromtimestamp(ts, timezone.utc)` |
| SQLAlchemy 2.x | `Model.query.get(id)` | `db.session.get(Model, id)` |
| SQLAlchemy 2.x | `Model.query.filter(...)` em código novo (legado, ainda funciona) | `db.session.execute(db.select(Model).where(...))` |
| Flask 2.3+ | `@app.before_first_request` | lógica no `create_app` |
| Flask 2.2+ | `app.json_encoder` / `JSONEncoder` customizado | `app.json` provider |
| Werkzeug 2.1+ | `safe_str_cmp` | `hmac.compare_digest` |
| Python | `imp`, `distutils`, `asyncio.get_event_loop()` fora de loop | `importlib`, `setuptools`, `asyncio.run()` |
| Node.js | `new Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Node.js | `url.parse()` | `new URL()` |
| Node.js | `crypto.createCipher()` | `crypto.createCipheriv()` |
| Node.js | `fs.exists()` | `fs.existsSync()` ou `fs.promises.access()` |
| Express 4.16+ | `body-parser` separado para JSON | `express.json()` |
| Express 4 | `req.param(name)` | `req.params`, `req.query`, `req.body` |
| Express 4 | `res.send(status)` com número, `res.json(status, body)` | `res.status(s).send()` / `res.status(s).json(body)` |
| Express 5 | `app.del()` | `app.delete()` |

Um finding por API, com todas as ocorrências. Se nenhuma for encontrada, escreva no relatório "No deprecated API usage found" com a lista do que foi checado.

Correção: T-11.

## AP-17 Callbacks aninhados (MEDIUM)

Três ou mais níveis de callback para uma sequência de operações de banco, com contadores manuais de pendências (`pending--; if (pending === 0) res.json(...)`) e erros ignorados nos níveis internos.

Sinais: indentação crescente com `function(err, ...)` / `(err, row) =>` aninhados; variáveis `xxxPending`.

Correção: T-10.

## AP-18 Magic numbers e strings (LOW)

Número ou string com significado de negócio solto no código: faixas de preço ou desconto, limites de tamanho (`len(x) > 200`), listas de status repetidas, regra de aprovação por prefixo ou tamanho de string, nível numérico tratado como "alto" sem nome.

Correção: T-14.

## AP-19 Nomes pouco descritivos (LOW)

Variáveis de uma ou duas letras fora de laço curto (`u`, `x`, `d`, `tmp`), campos de API abreviados sem necessidade, `self = this` em JavaScript, nomes que mentem (função chamada de criptografia que só codifica, módulo `utils` com regra de negócio).

Mudar nome de campo da API quebra o contrato: nesse caso, renomeie só internamente e mantenha o campo externo.

Correção: T-14.

## AP-20 `print`/`console.log` no lugar de logging (LOW)

Mensagens operacionais com `print`/`console.log`, sem nível nem contexto, às vezes simulando efeitos colaterais (`print("ENVIANDO EMAIL...")`).

Correção: T-15.

## AP-21 Import, variável ou código morto (LOW)

Imports não usados (`import os, sys, json, time`), variáveis exportadas e nunca lidas (`totalRevenue`), funções utilitárias sem chamador, constantes declaradas e ignoradas.

Sinais: para cada import, `grep -c` do nome no próprio arquivo; para cada função de utils, `grep -rn "nome_da_funcao("` no projeto.

Correção: remover, ou passar a usar quando a função resolve uma duplicação (AP-14).
