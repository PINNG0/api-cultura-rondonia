import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 🔹 Faz requisição e retorna o conteúdo como BeautifulSoup
def get_soup(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception:
        return None

# 🔹 Completa URLs relativas
def complete_url(relative_url):
    base = "https://funcultural.portovelho.ro.gov.br"
    return urljoin(base, relative_url)
