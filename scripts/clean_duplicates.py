#!/usr/bin/env python3
import json, hashlib, os
from pathlib import Path
import shutil

P = Path("api_output")
if not P.exists():
    print("Diretório api_output não encontrado.")
    raise SystemExit(1)

quar = P / "quarentena"
quar.mkdir(exist_ok=True)

seen = {}
moved = 0
for f in sorted(P.glob("*.json")):
    if f.name in ("eventos.json", "eventos_index.json"):
        continue
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        chave = (data.get("titulo","") + "|" + data.get("link_evento","")).strip()
        chave_norm = ''.join(ch for ch in chave if ch.isalnum()).lower()
        h = hashlib.sha1(chave_norm.encode('utf-8')).hexdigest()
        if h in seen:
            print("movendo duplicado para quarentena:", f.name, "-> mantido:", seen[h].name)
            shutil.move(str(f), str(quar / f.name))
            moved += 1
        else:
            seen[h] = f
    except Exception as e:
        print("skip file", f.name, e)

print(f"Concluído. Arquivos movidos para quarentena: {moved}. Total únicos preservados: {len(seen)}.")
