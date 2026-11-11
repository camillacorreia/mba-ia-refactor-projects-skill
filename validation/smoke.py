"""
Smoke test independente da skill: roda uma sequência de requisições contra a API
e grava, para cada uma, o status HTTP e as chaves do JSON de resposta.

Uso:
    python validation/smoke.py <spec.json> <base_url> <saida.json>

O spec é uma lista de passos {"name", "method", "path", "body"?, "save"?}.
"save" guarda um valor da resposta (caminho com pontos, ex.: "dados.id") numa
variável que os passos seguintes usam como {{nome}} no path ou no body.
Só usa a biblioteca padrão, para rodar com qualquer Python 3.
"""
import json
import re
import sys
import urllib.error
import urllib.request


def dig(obj, path):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def render(value, env):
    text = json.dumps(value)
    for key, val in env.items():
        text = text.replace("{{" + key + "}}", str(val))
    return json.loads(text)


def shape(body):
    """Resumo estável da resposta: chaves do topo e, se houver lista, chaves do primeiro item."""
    if isinstance(body, dict):
        return {"type": "object", "keys": sorted(body.keys())}
    if isinstance(body, list):
        first = body[0] if body else None
        return {"type": "list", "len": len(body), "item_keys": sorted(first.keys()) if isinstance(first, dict) else None}
    return {"type": "text"}


def call(base, step):
    data = json.dumps(step["body"]).encode() if "body" in step else None
    req = urllib.request.Request(base + step["path"], data=data, method=step["method"])
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read().decode()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        body = raw
    return status, body


def main():
    spec_path, base, out_path = sys.argv[1:4]
    steps = json.load(open(spec_path, encoding="utf-8"))
    env, results = {}, []
    for step in steps:
        step = render(step, env)
        status, body = call(base, step)
        if "save" in step and isinstance(body, (dict, list)):
            for var, path in step["save"].items():
                env[var] = dig(body, path)
        results.append({"name": step["name"], "request": f'{step["method"]} {step["path"]}', "status": status, "shape": shape(body)})
        print(f'{status}  {step["method"]:6} {step["path"]:40} {step["name"]}')
    json.dump(results, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
