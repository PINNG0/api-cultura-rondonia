"""
Módulo de armazenamento do scraper.

Responsável por:
- Salvar os eventos coletados em arquivos JSON
- Gerar um índice resumido
"""

import json
import os
from scraping.config import API_DIR, API_LIST_FILE, API_INDEX_FILE


# ---------------------------------------------------------
# Salva os eventos em JSON e gera o índice
# ---------------------------------------------------------
def save_only(eventos):
    os.makedirs(API_DIR, exist_ok=True)

    # salva lista completa
    with open(API_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)

    # índice resumido
    index = {
        "quantidade_eventos": len(eventos),
        "links": [e["link_evento"] for e in eventos]  # substitui ids
    }

    with open(API_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
