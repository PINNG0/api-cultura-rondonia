"""
Módulo de fetch da Funcultural.

Responsável por:
- Fazer requisições HTTP com segurança
- Retornar o HTML como BeautifulSoup
- Resolver URLs relativas para URLs absolutas
- Utilizar cache local para acelerar o scraper
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraping.cache import load_html, save_html


# ---------------------------------------------------------
# Faz requisição HTTP e retorna o HTML como BeautifulSoup
# ---------------------------------------------------------
def get_soup(url):
    # 1. tenta carregar do cache
    cached = load_html(url)
    if cached:
        logging.info("📦 Cache HIT: %s", url)
        return BeautifulSoup(cached, "html.parser")

    logging.info("🌐 Cache MISS: baixando %s", url)

    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )

        if resp.status_code != 200:
            logging.warning("⚠️ Resposta inválida (%s) para %s", resp.status_code, url)
            return None

        html = resp.text

        # salva no cache
        save_html(url, html)

        return BeautifulSoup(html, "html.parser")

    except requests.RequestException as e:
        logging.error("❌ Erro de rede ao acessar %s: %s", url, e)
        return None

    except Exception as e:
        logging.error("❌ Erro inesperado ao acessar %s: %s", url, e)
        return None


# ---------------------------------------------------------
# Converte URLs relativas para absolutas
# ---------------------------------------------------------
def complete_url(relative_url):
    base = "https://funcultural.portovelho.ro.gov.br"
    return urljoin(base, relative_url)
