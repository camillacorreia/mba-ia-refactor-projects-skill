# Template do relatório de auditoria (Fase 2)

Imprima o relatório exatamente com esta estrutura. Campos entre `<>` são preenchidos; o resto é literal.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório>
Stack:   <Linguagem> + <Framework> (<banco>)
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Título curto>
ID: <AP-xx>
File: <arquivo>:<linha ou intervalo>
Locations: <outras ocorrências, "arquivo:linha, arquivo:linha"; omita se for uma só>
Description: <o que está errado, citando o trecho ou valor concreto>
Impact: <consequência concreta: o que um atacante faz, o que quebra, o que fica impossível de testar>
Recommendation: <transformação a aplicar, com o ID do playbook (T-xx)>

### [HIGH] <Título>
...

### [MEDIUM] <Título>
...

### [LOW] <Título>
...

## Deprecated APIs
<uma linha por API encontrada (já detalhadas nos findings), ou "No deprecated API usage found. Checked: <lista>">

================================
Total: <n> findings
================================
```

## Regras

1. Ordem: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, o de maior impacto primeiro.
2. `File` aponta a ocorrência principal com linha exata. Confirme com `grep -n` ou `cat -n` antes de escrever. Nunca escreva só o nome do arquivo.
3. A soma do `Summary` precisa bater com a quantidade de blocos `###` e com o `Total`.
4. `Description` cita o código real (ex.: "SECRET_KEY = 'minha-chave-super-secreta-123'"), não uma paráfrase genérica.
5. `Recommendation` diz o que fazer neste projeto, não uma definição de livro.
6. Um mesmo trecho pode violar dois anti-patterns. Reporte no de maior severidade e mencione o outro na descrição, em vez de contar duas vezes.
7. Mínimo esperado em projetos legados: 5 findings, com pelo menos 1 CRITICAL ou HIGH. Se você achou menos, releia o catálogo item por item antes de concluir.

## Exemplo de finding bem escrito

```
### [CRITICAL] SQL Injection em queries montadas por concatenação
ID: AP-02
File: library/books.py:42
Locations: library/books.py:58-61, library/members.py:17, library/members.py:88-95
Description: find_book monta "SELECT * FROM books WHERE isbn = '" + isbn + "'"; authenticate concatena email e senha na cláusula WHERE.
Impact: POST /auth com email "' OR '1'='1' --" autentica sem senha; a busca por título permite ler qualquer tabela.
Recommendation: Trocar todas as queries por placeholders com parâmetros (T-02) dentro dos novos models.
```
