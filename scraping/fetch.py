"""
Módulo de fetch da Funcultural.

Responsável por:
- Fazer requisições HTTP com segurança
- Retornar o HTML como BeautifulSoup
- Resolver URLs relativas para URLs absolutas
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# ---------------------------------------------------------
# Faz requisição HTTP e retorna o HTML como BeautifulSoup
# ---------------------------------------------------------
def get_soup(url):
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )

        # resposta inválida
        if resp.status_code != 200:
            return None

        return BeautifulSoup(resp.text, "html.parser")

    except requests.RequestException:
        # falha de rede, timeout, DNS, etc.
        return None

    except Exception:
        # qualquer erro inesperado
        return None


# ---------------------------------------------------------
# Converte URLs relativas para absolutas
# ---------------------------------------------------------
def complete_url(relative_url):
    base = "https://funcultural.portovelho.ro.gov.br"
    return urljoin(base, relative_url)
