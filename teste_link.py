"""
Script auxiliar para testar manualmente um link de evento.

Responsável por:
- Baixar o HTML de um link específico
- Validar se o conteúdo é acessível
- Verificar se a estrutura esperada existe
"""

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# Link a ser testado (cole aqui qualquer link problemático)
# ---------------------------------------------------------
URL_PROBLEMA = (

)


# ---------------------------------------------------------
# Testa o link e imprime informações úteis para debug
# ---------------------------------------------------------
def testar_link(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print("✅ STATUS OK (200). Conteúdo baixado com sucesso.")

        soup = BeautifulSoup(response.content, "html.parser")
        body = soup.find("body")

        if not body:
            print("❌ FALHA: HTML vazio ou inválido.")
            return

        print(f"📄 Tamanho do HTML: {len(str(body))} caracteres.")

        conteudo = soup.find("article", class_="noticia-conteudo")
        if conteudo:
            print("✅ Tag <article class='noticia-conteudo'> encontrada.")
            trecho = conteudo.get_text(strip=True)[:120]
            print(f"📝 Trecho do conteúdo: {trecho}...")
        else:
            print("❌ FALHA: Tag <article class='noticia-conteudo'> não encontrada.")

    except requests.exceptions.HTTPError as e:
        print(f"❌ ERRO HTTP: {e}")
    except Exception as e:
        print(f"❌ ERRO DESCONHECIDO: {e}")


# ---------------------------------------------------------
# Execução direta
# ---------------------------------------------------------
if __name__ == "__main__":
    testar_link(URL_PROBLEMA)
