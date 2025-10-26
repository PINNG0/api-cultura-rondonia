import requests
from bs4 import BeautifulSoup

# Cole aqui o link de um evento que o seu scraper gerou
URL_PROBLEMA = "https://funcultural.portovelho.ro.gov.br/artigo/51572/evento-prefeitura-de-porto-velho-realiza-a-5a-conferencia-municipal-de-cultura"

def testar_link(url):
    """Tenta baixar o HTML e imprimir o título."""
    try:
        response = requests.get(url, timeout=10)
        # Se der erro 404/500, isso vai travar o script e mostrar o problema
        response.raise_for_status() 
        print("STATUS OK (200). Conteúdo deve ter sido baixado.")
        
        # Tenta encontrar a tag <body> para confirmar que é HTML válido
        soup = BeautifulSoup(response.content, 'html.parser')
        body = soup.find('body')
        
        if body:
            print(f"SUCESSO! Tamanho do corpo do HTML: {len(str(body))} caracteres.")
            # Vamos tentar encontrar o conteúdo da descrição
            conteudo = soup.find('article', class_='noticia-conteudo')
            if conteudo:
                print("SUCESSO! Tag 'noticia-conteudo' encontrada.")
                # Imprime apenas 100 caracteres da descrição para ver se é o texto completo
                print("Trecho do Conteúdo: " + conteudo.text[:100].strip() + "...")
            else:
                print("FALHA: Não encontrou a tag <article class='noticia-conteudo'> na página.")

        else:
            print("FALHA: HTML vazio ou inválido.")
            
    except requests.exceptions.HTTPError as e:
        print(f"ERRO DE CONEXÃO: Falha ao acessar o artigo. HTTP Error: {e}")
    except Exception as e:
        print(f"ERRO DESCONHECIDO: {e}")


if __name__ == "__main__":
    testar_link(URL_PROBLEMA)