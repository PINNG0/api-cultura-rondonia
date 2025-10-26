import requests
from bs4 import BeautifulSoup
import json
import time # Importa a biblioteca time

# URL da nossa API (o arquivo que vamos gerar)
API_FILE_NAME = "eventos.json"

# URLS DOS SITES QUE VAMOS RASPAR
URL_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br/noticias"
# URL base do site, para consertar os links das imagens
BASE_URL_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"

# Quantas páginas queremos raspar? (1, 2, 3...)
NUMERO_DE_PAGINAS_FUNCULTURAL = 3 

def raspar_funcultural():
    print(f"Iniciando raspagem da Funcultural (Páginas 1 a {NUMERO_DE_PAGINAS_FUNCULTURAL})...")
    
    lista_de_eventos_total = [] # Lista para guardar eventos de TODAS as páginas

    # --- LOOP PELAS PÁGINAS ---
    for page_num in range(1, NUMERO_DE_PAGINAS_FUNCULTURAL + 1):
        
        # Monta a URL da página atual
        url_pagina_atual = f"{URL_FUNCULTURAL}?page={page_num}"
        print(f"  Raspando página: {url_pagina_atual}")

        try:
            # 1. Visita o site
            html = requests.get(url_pagina_atual)
            html.raise_for_status() 

            # 2. "Lê" o HTML
            soup = BeautifulSoup(html.content, 'html.parser')

            # 3. Encontra os blocos
            blocos_de_dados = soup.find_all('div', class_='resultado-pesquisa')
            
            eventos_nesta_pagina = 0 # Contador para esta página

            # 4. Processa os blocos em pares (igual antes)
            for i in range(0, len(blocos_de_dados), 2):
                bloco_img = blocos_de_dados[i]
                if i + 1 >= len(blocos_de_dados): continue
                bloco_txt = blocos_de_dados[i+1]

                # 5. Extrai os dados (igual antes)
                img_tag = bloco_img.find('img')
                if not img_tag: continue
                link_imagem = img_tag['src']
                
                titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
                if not titulo_tag: continue
                titulo_texto = titulo_tag.text.strip()
                
                desc_tag = bloco_txt.find('div', class_='descricao-noticia')
                descricao = desc_tag.text.strip() if desc_tag else ""
                
                link_tag = bloco_txt.find('a')
                link_evento = link_tag['href'] if link_tag else ""

                # 6. Monta o objeto "Evento" (igual antes)
                evento = {
                    "titulo": titulo_texto,
                    "descricao": descricao,
                    "imagem_url": f"{BASE_URL_FUNCULTURAL}{link_imagem}",
                    "link_evento": f"{BASE_URL_FUNCULTURAL}{link_evento}",
                    "fonte": "Funcultural"
                }
                
                # Adiciona na lista TOTAL
                lista_de_eventos_total.append(evento)
                eventos_nesta_pagina += 1
                # Descomente a linha abaixo se quiser ver os títulos sendo encontrados
                # print(f"    Encontrado: {titulo_texto}")

            print(f"    Página {page_num}: {eventos_nesta_pagina} eventos encontrados.")

            # --- PAUSA EDUCADA ---
            # Espera 1 segundo antes de ir para a próxima página
            # para não sobrecarregar o site da Funcultural.
            time.sleep(1) 

        except requests.exceptions.RequestException as e:
            print(f"  Erro ao acessar a página {page_num} da Funcultural: {e}")
            # Continua para a próxima página mesmo se uma falhar
            continue 

    print(f"Funcultural (Total): {len(lista_de_eventos_total)} eventos encontrados em {NUMERO_DE_PAGINAS_FUNCULTURAL} páginas.")
    return lista_de_eventos_total

# --- FUNÇÃO PRINCIPAL ---
def main():
    print("Iniciando robô agregador de cultura...")
    eventos_totais = []
    
    # Adiciona os eventos da Funcultural (agora com paginação)
    eventos_totais.extend(raspar_funcultural())
    
    # (Aqui nós adicionaremos a chamada para 'raspar_sejucel()' no futuro)
    
    # Salva o arquivo JSON
    with open(API_FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(eventos_totais, f, ensure_ascii=False, indent=4)
    
    print(f"\nSucesso! A 'API' foi criada em '{API_FILE_NAME}' com {len(eventos_totais)} eventos.")

# --- RODA A FUNÇÃO PRINCIPAL ---
if __name__ == "__main__":
    main()