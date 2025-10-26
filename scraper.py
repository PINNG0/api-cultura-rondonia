import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

# --- Configurações ---
API_FILE_NAME = "eventos.json"
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3 

# --- Funções Auxiliares Comuns ---

def obter_soup(url):
    """Baixa e parseia o HTML de uma URL, tratando erros de conexão."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"    Erro ao acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    """Garante que uma URL seja absoluta e usa HTTPS para compatibilidade Android."""
    if not url_relativa: return None
    
    if url_relativa.startswith('http'): 
        return url_relativa.replace('http://', 'https://')
        
    if url_relativa.startswith('/'):
        base_url_https = base_url.replace('http://', 'https://')
        return f"{base_url_https}{url_relativa}"
        
    return None

def limpar_texto(texto):
    """Remove padrões de créditos de foto e limpa espaços duplicados."""
    texto = re.sub(r'(Fotos|Texto):\s*[^.\n]+', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\s{2,}', ' ', texto).strip()
    return texto

# --- Funções de Processamento do Conteúdo (BLOCO A BLOCO) ---

def pre_processar_html_conteudo(conteudo):
    """Extrai URLs de imagem e limpa tags de formatação no conteúdo."""
    lista_imagens_conteudo = []

    for elemento in conteudo.find_all(True):
        # 1. Lógica para extrair imagens e remover divs flutuantes
        if elemento.get('class') and 'artigo-img-wrap' in elemento.get('class'):
            img_tag = elemento.find('img')
            if img_tag and img_tag.get('src'):
                url_imagem = completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
                if url_imagem:
                    lista_imagens_conteudo.append(url_imagem)
            elemento.decompose() # Remove a div flutuante
        
        # 2. Lógica para Tags de Formatação: Adiciona espaço ao redor
        elif elemento.name in ['strong', 'em', 'span', 'b', 'i']:
            elemento.replace_with(elemento.get_text(strip=True) + ' ')
    
    return lista_imagens_conteudo

def classificar_blocos_de_texto(conteudo, lista_imagens_conteudo):
    """Itera e classifica blocos, inserindo imagens (intercalação)."""
    blocos_finais = []
    textos_vistos_hash = set()
    imagem_index = 0
    paragrafo_contador = 0

    for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3']): 
        texto_html = elemento.decode_contents().strip()
        
        if texto_html:
            texto_limpo = limpar_texto(elemento.get_text(strip=True))

            # Filtro 1: Remove blocos curtos
            if len(texto_limpo.split()) < 5:
                continue
                
            # Filtro 2: Remoção de Duplicação por Hash
            trecho_hash = re.sub(r'[\W_]+', '', texto_limpo.lower())[:50] 
            
            is_duplicate = False
            for seen_hash in textos_vistos_hash:
                if trecho_hash.startswith(seen_hash): # Simplificação do filtro de duplicação
                    is_duplicate = True
                    break
            
            if is_duplicate:
                continue 

            # Classificação
            is_subtitle = len(texto_limpo) < 60 and texto_limpo.isupper() 
            
            # Adiciona o bloco
            blocos_finais.append({
                "type": "SUBTITLE" if is_subtitle else "PARAGRAPH",
                "content": texto_html
            })
            textos_vistos_hash.add(trecho_hash)
            
            # Intercalação de Imagens (Insere imagem a cada 2 parágrafos)
            if not is_subtitle:
                paragrafo_contador += 1
                if paragrafo_contador % 2 == 0 and imagem_index < len(lista_imagens_conteudo):
                    blocos_finais.append({
                        "type": "IMAGE_URL",
                        "content": lista_imagens_conteudo[imagem_index]
                    })
                    imagem_index += 1
        
    # Adiciona imagens restantes no final
    while imagem_index < len(lista_imagens_conteudo):
        blocos_finais.append({
            "type": "IMAGE_URL",
            "content": lista_imagens_conteudo[imagem_index]
        })
        imagem_index += 1
        
    return blocos_finais

def raspar_detalhes_funcultural(url_detalhes):
    """Coordena a raspagem de detalhes (Complexidade 21 -> Reduzida)."""
    soup_detalhes = obter_soup(url_detalhes)
    if not soup_detalhes: return []

    conteudo = soup_detalhes.find('article', class_='noticia-conteudo')
    if not conteudo: return []
    
    # 1. Pré-processamento e Extração de Imagens
    lista_imagens_conteudo = pre_processar_html_conteudo(conteudo)
    
    # 2. Classificação e Intercalação de Blocos
    blocos_finais = classificar_blocos_de_texto(conteudo, lista_imagens_conteudo)
        
    return blocos_finais

def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    """Extrai dados e busca detalhes para um par de blocos (Complexidade 36 -> Reduzida)."""
    
    # Extração de Título e Banner
    img_tag = bloco_img.find('img')
    src_banner_relativo = img_tag['src'] if img_tag else None
    link_imagem_banner = completar_url(src_banner_relativo, URL_BASE_FUNCULTURAL)

    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo_texto = titulo_tag.text.strip() if titulo_tag else "Título não encontrado"

    link_tag = bloco_txt.find('a')
    link_evento_relativo = link_tag['href'] if link_tag else None
    link_evento_completo = completar_url(link_evento_relativo, URL_BASE_FUNCULTURAL)

    if not link_evento_completo or not link_imagem_banner: return None

    print(f"    Processando: {titulo_texto}")
    
    # Chama a função principal de extração de blocos
    blocos_de_conteudo = raspar_detalhes_funcultural(link_evento_completo)
    time.sleep(0.3) 

    return {
        "titulo": titulo_texto,
        "blocos_conteudo": blocos_de_conteudo,
        "imagem_url": link_imagem_banner,
        "link_evento": link_evento_completo,
        "fonte": "Funcultural"
    }

def raspar_funcultural():
    """Gerencia a raspagem de múltiplas páginas da Funcultural."""
    print(f"Iniciando raspagem da Funcultural (Páginas 1 a {NUMERO_DE_PAGINAS_FUNCULTURAL})...")
    lista_de_eventos_total = []

    for page_num in range(1, NUMERO_DE_PAGINAS_FUNCULTURAL + 1):
        url_pagina_atual = f"{URL_NOTICIAS_FUNCULTURAL}?page={page_num}"
        print(f"  Raspando página: {url_pagina_atual}")
        soup_lista = obter_soup(url_pagina_atual)
        if not soup_lista: continue

        blocos_de_dados = soup_lista.find_all('div', class_='resultado-pesquisa')
        eventos_nesta_pagina = 0

        for i in range(0, len(blocos_de_dados), 2):
            bloco_img = blocos_de_dados[i]
            if i + 1 >= len(blocos_de_dados): continue
            bloco_txt = blocos_de_dados[i+1]

            evento = processar_par_blocos_funcultural(bloco_img, bloco_txt)
            if evento:
                lista_de_eventos_total.append(evento)
                eventos_nesta_pagina += 1

        print(f"    Página {page_num}: {eventos_nesta_pagina} eventos processados.")
        if page_num < NUMERO_DE_PAGINAS_FUNCULTURAL: time.sleep(1)

    print(f"Funcultural (Total): {len(lista_de_eventos_total)} eventos encontrados.")
    return lista_de_eventos_total

# --- Execução Principal ---
def main():
    print("Iniciando robô agregador de cultura...")
    eventos_totais = raspar_funcultural()

    try:
        with open(API_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(eventos_totais, f, ensure_ascii=False, indent=4)
        print(f"\nSucesso! API '{API_FILE_NAME}' atualizada com {len(eventos_totais)} eventos.")
    except IOError as e:
        print(f"\nErro ao salvar '{API_FILE_NAME}': {e}")

if __name__ == "__main__":
    main()