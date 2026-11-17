"""
Compara o smoke do projeto original (spec base) com o do refatorado (spec -auth).

Uso:
    python validation/compare_auth.py <spec-auth.json> <before.json> <after.json>

Regras:
- passo com "expect": o status depois precisa ser esse (ex.: 403 sem credencial);
- passo com "base": status e formato precisam bater com o passo de mesmo nome
  na linha de base; diferenças aparecem como DIFF para serem justificadas.
"""
import json
import sys

spec, before, after = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:4])
base = {r["name"]: r for r in before}
ok = diff = fail = 0
for step, res in zip(spec, after):
    if "expect" in step:
        good = res["status"] == step["expect"]
        tag = "OK  " if good else "FAIL"
        ok, fail = ok + good, fail + (not good)
        print(f'{tag} {res["request"]:38} esperado {step["expect"]}, veio {res["status"]}  {res["name"]}')
        continue
    b = base[step["base"]]
    same = b["status"] == res["status"] and b["shape"] == res["shape"]
    if same:
        ok += 1
        print(f'OK   {res["request"]:38} {b["status"]} -> {res["status"]}  {res["name"]}')
    else:
        diff += 1
        extra = ""
        if b["shape"] != res["shape"] and b["shape"].get("keys") is not None and res["shape"].get("keys") is not None:
            gone = sorted(set(b["shape"]["keys"]) - set(res["shape"]["keys"]))
            new = sorted(set(res["shape"]["keys"]) - set(b["shape"]["keys"]))
            extra = f"  chaves -{gone} +{new}"
        print(f'DIFF {res["request"]:38} {b["status"]} -> {res["status"]}  {res["name"]}{extra}')
print(f"\n{ok} OK, {diff} DIFF, {fail} FAIL de {len(after)} requisições")
