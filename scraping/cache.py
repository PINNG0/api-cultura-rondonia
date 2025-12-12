"""
Cache local para HTML.

Responsável por:
- Salvar HTML baixado para evitar requisições repetidas
- Ler HTML do cache quando disponível
- Controlar expiração do cache
"""

import os
import time
import hashlib

CACHE_DIR = ".cache/html"
os.makedirs(CACHE_DIR, exist_ok=True)

# Expiração do cache em segundos (1 dia)
CACHE_TTL = 60 * 60 * 24


def _hash_url(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def cache_path(url):
    return os.path.join(CACHE_DIR, _hash_url(url) + ".html")


def save_html(url, content):
    path = cache_path(url)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_html(url):
    path = cache_path(url)
    if not os.path.exists(path):
        return None

    # Verifica expiração
    if time.time() - os.path.getmtime(path) > CACHE_TTL:
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
