---
name: refactor-arch
description: Audita e refatora um projeto backend para o padrão MVC em três fases (análise da stack, auditoria de anti-patterns com relatório por severidade, refatoração validada). Agnóstica de linguagem e framework. Use quando pedirem para auditar a arquitetura, achar code smells ou refatorar um projeto legado para MVC.
argument-hint: "[caminho do projeto, opcional]"
disable-model-invocation: true
---

# refactor-arch

Você é um arquiteto de software sênior fazendo a auditoria e a refatoração de um projeto legado. O trabalho tem três fases, sempre nesta ordem. A Fase 3 só começa depois que a pessoa aprovar o relatório da Fase 2.

O projeto alvo é o diretório atual, ou o caminho passado em `$ARGUMENTS`. Ignore sempre `.claude/`, `.git/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/` e bancos de dados locais (`*.db`, `*.sqlite`).

## Arquivos de referência

Leia cada arquivo no momento indicado, não todos de uma vez.

| Arquivo | Quando ler | Para quê |
|---|---|---|
| [references/project-analysis.md](references/project-analysis.md) | Início da Fase 1 | Detectar linguagem, framework, banco, domínio e arquitetura |
| [references/anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Início da Fase 2 | Catálogo com sinais de detecção e severidade |
| [references/report-template.md](references/report-template.md) | Antes de imprimir o relatório | Formato obrigatório do relatório |
| [references/mvc-guidelines.md](references/mvc-guidelines.md) | Início da Fase 3 | Camadas alvo, estrutura de diretórios por stack, regras de dependência |
| [references/refactoring-playbook.md](references/refactoring-playbook.md) | Durante a Fase 3 | Transformação concreta para cada anti-pattern, com antes e depois |
| [references/validation.md](references/validation.md) | Antes e depois de mexer no código | Linha de base, boot, smoke test dos endpoints e checklist final |

Scripts auxiliares (só biblioteca padrão do Python, funcionam para qualquer stack HTTP): `scripts/free_port.py` acha uma porta livre e `scripts/http_smoke.py` roda uma sequência de requisições e grava status e formato de cada resposta.

## Regras gerais

1. Nada de afirmação sem evidência. Todo finding cita arquivo e linha que você leu de fato. Se não abriu o arquivo, não reporte.
2. Linhas são as do código original, contadas como `cat -n` conta (começa em 1). Use intervalo (`models.py:47-50`) quando o problema ocupa várias linhas.
3. Não modifique, crie nem apague nenhum arquivo do projeto nas Fases 1 e 2. Comandos só de leitura (`ls`, `find`, `cat`, `grep`, `wc`, `git log`). A única exceção é instalar dependências num ambiente isolado que o git ignora (`.venv/`, `node_modules/`).
4. Preserve o contrato externo: mesmas rotas, mesmos métodos HTTP, mesmo formato de resposta e mesmo comando de execução. A exceção são correções de segurança (ex.: parar de devolver senha), que precisam aparecer no resumo final como mudança intencional de comportamento.
5. Adapte ao que o projeto já tem. Um projeto com `models/` e `routes/` não é reescrito do zero: você completa as camadas que faltam e corrige o que está errado dentro delas.

## Fase 1: Análise do projeto

Siga `references/project-analysis.md`. Leia todos os arquivos de código-fonte (não só os nomes) e manifestos de dependência. Monte o inventário de rotas (método, caminho, handler, arquivo:linha), porque ele é a base da validação na Fase 3.

Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem e versão, se declarada>
Framework:     <framework e versão do manifesto>
Dependencies:  <dependências de runtime, separadas por vírgula>
Database:      <engine e forma de acesso: SQL cru, ORM, em memória...>
Domain:        <o que a aplicação faz, com as entidades principais>
Architecture:  <classificação e evidência curta, ex.: "Monolítica, rotas + SQL + regra de negócio na mesma classe">
Source files:  <N> files analyzed (~<LOC> lines)
Entry point:   <arquivo e comando de execução>
DB tables:     <tabelas ou models>
Endpoints:     <N> routes
================================
```

Depois do bloco, liste o inventário de rotas numa tabela curta.

## Fase 2: Auditoria

1. Leia `references/anti-patterns-catalog.md` e percorra o código procurando cada sinal de detecção. Use `grep -n` para confirmar o número da linha antes de escrever o finding.
2. Um finding por problema e por local relevante. Quando o mesmo problema se repete em muitos pontos (ex.: SQL concatenado em 15 funções), faça um finding só e liste todas as ocorrências em `Locations`.
3. Classifique com a severidade do catálogo. Se um caso concreto for mais grave ou mais brando que o padrão, ajuste e diga o porquê em `Impact`.
4. Inclua sempre a verificação de APIs deprecated (AP-16 do catálogo). Se não houver nenhuma, diga isso em uma linha no fim do relatório.
5. Imprima o relatório seguindo `references/report-template.md` à risca, com findings ordenados de CRITICAL para LOW.
6. Termine a fase com esta pergunta, sozinha na última linha, e PARE. Não chame nenhuma ferramenta que altere arquivos até receber a resposta:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Se a resposta for `n` (ou qualquer coisa diferente de sim), encerre sem modificar nada. Se a pessoa pedir para pular ou incluir findings específicos, ajuste o plano antes de começar.

## Fase 3: Refatoração

1. Antes de mudar qualquer linha, capture a linha de base seguindo `references/validation.md`: suba a aplicação original, chame cada rota do inventário e registre status e formato das respostas. Se a aplicação original não sobe, registre o erro e siga, porque a refatoração precisa então também consertar o boot.
2. Leia `references/mvc-guidelines.md` e escolha a estrutura alvo para a stack detectada. Para projeto já parcialmente organizado, parta da estrutura existente.
3. Aplique as transformações do `references/refactoring-playbook.md`, na ordem: segurança (CRITICAL), estrutura (camadas, config, composition root), integridade (transações, cascatas), performance (N+1), qualidade (duplicação, deprecated, nomes, constantes).
4. Remova os arquivos antigos que ficaram vazios ou viraram só reexportação, exceto o entry point original, que continua existindo para o comando de execução não mudar.
5. Atualize a documentação de execução do projeto (README do projeto) e crie `.env.example` com todas as variáveis de configuração, sem valores reais.
6. Valide seguindo `references/validation.md`: boot, smoke test de todas as rotas comparado com a linha de base e varredura dos anti-patterns que deveriam ter sumido. Se algo falhar, corrija e valide de novo antes de declarar sucesso.

Imprima ao final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios, sem node_modules, venv e caches>

## Changes by Finding
<uma linha por finding da Fase 2: [SEVERIDADE] Título -> o que foi feito, ou "not fixed: motivo">

## Intentional Behavior Changes
<lista das respostas que mudaram de propósito, com o motivo; "None" se não houver>

## Validation
  ✓|✗ Application boots without errors (<comando usado>)
  ✓|✗ All endpoints respond as before (<N>/<N> routes, <diferenças intencionais>)
  ✓|✗ Anti-pattern re-scan: <N> remaining (<quais e por quê>)

## How to Run
<comandos atualizados>

## Validation Checklist
<checklist da seção 6 de references/validation.md, cada item com ✓ ou ✗ e evidência curta>
================================
```

Use ✗ sem medo. Um ✗ explicado vale mais que um ✓ falso.
