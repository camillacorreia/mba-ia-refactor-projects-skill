# Validação (Fase 3)

A validação compara a aplicação antes e depois da refatoração com as mesmas requisições. Sem linha de base, "os endpoints continuam respondendo" vira opinião.

Guarde tudo o que a validação produz (specs, saídas, logs de servidor) fora do projeto, num diretório temporário:

```bash
WORK="${TMPDIR:-/tmp}/refactor-arch-$(basename "$PWD")"
mkdir -p "$WORK"
SKILL_DIR=".claude/skills/refactor-arch"
```

## 1. Escolher a porta

Portas comuns podem estar ocupadas (no macOS, a 5000 é do AirPlay Receiver). Nunca mate processos que você não iniciou.

```bash
PORT=$(python3 "$SKILL_DIR/scripts/free_port.py" <porta_original>)
```

Se o código original fixa a porta, use o mecanismo do framework para sobrescrever sem editar arquivo: `flask --app <modulo> run --port $PORT`, `uvicorn main:app --port $PORT`. Em Node com porta fixa no código, rode como está se a porta estiver livre; se não estiver, registre na linha de base que o original não sobe naquela máquina e valide o original numa porta livre com `node -e` carregando o módulo, ou pule a linha de base do original e explique.

## 2. Spec de requisições

A partir do inventário de rotas da Fase 1, escreva `$WORK/spec.json` com uma requisição por rota, no formato do `scripts/http_smoke.py`:

```json
[
  {"name": "listar", "method": "GET", "path": "/items"},
  {"name": "criar", "method": "POST", "path": "/items", "body": {"name": "Smoke"}, "save": {"iid": "id"}},
  {"name": "criar inválido", "method": "POST", "path": "/items", "body": {}},
  {"name": "atualizar", "method": "PUT", "path": "/items/{{iid}}", "body": {"name": "Smoke 2"}},
  {"name": "remover", "method": "DELETE", "path": "/items/{{iid}}"}
]
```

Regras da spec:

1. Toda rota do inventário aparece pelo menos uma vez, com corpo válido tirado das validações do código e dos dados de seed.
2. Para rotas de escrita, inclua também um caso inválido, para provar que a validação continua.
3. Login: inclua um login válido com usuário do seed e um inválido.
4. Use `save` para encadear ids criados, em vez de supor ids.
5. Rotas destrutivas (resetar banco, apagar tudo) vão por último.
6. Rotas protegidas pelo T-13 aparecem duas vezes: uma sem credencial e outra com `"headers": {"X-Admin-Token": "{{ADMIN_TOKEN}}"}`. O `http_smoke.py` preenche `{{ADMIN_TOKEN}}` com a variável de ambiente. Na linha de base as duas respondem igual. Depois da refatoração, a sem credencial responde 403 e a com credencial responde com o status e o formato da linha de base. Inclua também o cadastro com papel privilegiado sem credencial e o login seguido de uma rota protegida com `Authorization: Bearer {{token}}`, quando o projeto tiver login.

## 3. Linha de base (antes de editar qualquer arquivo)

```bash
# exemplo Flask
<venv>/bin/flask --app app run --port $PORT > "$WORK/before.server.log" 2>&1 &
SERVER_PID=$!
# exemplo Node
PORT=$PORT node src/app.js > "$WORK/before.server.log" 2>&1 &
SERVER_PID=$!

for i in $(seq 1 30); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.5; done
python3 "$SKILL_DIR/scripts/http_smoke.py" "$WORK/spec.json" "http://127.0.0.1:$PORT" "$WORK/before.json"
kill $SERVER_PID
```

Se o projeto tem seed separado (`python seed.py`), rode antes do boot, tanto na linha de base quanto depois. Se o banco é arquivo local, apague o arquivo gerado pela linha de base antes do boot final, para que as duas rodadas partam do mesmo estado de seed.

## 4. Depois da refatoração

1. Instale dependências novas, se adicionou alguma, e atualize o manifesto.
2. Suba a aplicação pelo comando documentado no README (ex.: `PORT=$PORT python app.py`, `PORT=$PORT npm start`). O boot precisa funcionar sem nenhuma variável de ambiente além da porta. Para o smoke, exporte também `ADMIN_TOKEN` com um valor de teste, no servidor e no `http_smoke.py`.
3. Confira o log de boot: nenhum traceback, nenhum aviso de deprecation que estava na lista do AP-16.
4. Rode a mesma spec e gere `$WORK/after.json`.
5. Compare status por status:

```bash
python3 - "$WORK/before.json" "$WORK/after.json" <<'EOF'
import json, sys
before, after = (json.load(open(p)) for p in sys.argv[1:3])
for b, a in zip(before, after):
    flag = "OK  " if b["status"] == a["status"] else "DIFF"
    print(f'{flag} {b["request"]:45} {b["status"]} -> {a["status"]}  {b["name"]}')
EOF
```

Cada `DIFF` precisa ser uma mudança intencional listada no resumo final (ex.: rota admin que agora responde 403 sem token). Qualquer outra diferença é regressão: corrija e rode de novo.

6. Compare também o formato (`shape`): chaves que sumiram só são aceitáveis se forem campos sensíveis removidos de propósito.
7. Pare os processos que você iniciou (`kill $SERVER_PID`).

## 5. Re-scan de anti-patterns

Rode de novo os comandos de detecção do catálogo para os itens CRITICAL e HIGH (AP-01, AP-02, AP-04, AP-05, AP-06, AP-08, AP-11) e para AP-16. Para o AP-04, confira rota por rota que cada location do finding tem o decorator/middleware e que o smoke mostra 403 sem credencial. O resultado esperado é zero ocorrência no código da aplicação. Ocorrências restantes entram no resumo com o motivo (ex.: senha de usuário fictício no seed, documentada).

## 6. Checklist final

Responda cada item com ✓ ou ✗ e uma evidência curta:

```
### Fase 1: Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2: Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3: Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```
