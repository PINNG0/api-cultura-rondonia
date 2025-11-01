import json
import os
from scraping.config import API_DIR, API_LIST_FILE, API_INDEX_FILE
import subprocess

# 🔹 Salva os eventos em arquivos JSON
def save_only(eventos):
    os.makedirs(API_DIR, exist_ok=True)

    with open(API_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)

    index = {
        "quantidade_eventos": len(eventos),
        "ids": [e["id"] for e in eventos]
    }

    with open(API_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# 🔹 Executa comandos Git para versionar os dados
def run_git_operations():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Atualização automática de eventos"], check=True)

        # 🔄 Tenta sincronizar com o remoto antes de dar push
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)

    except Exception as e:
        print("Erro ao executar comandos Git:", e)
