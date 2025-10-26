import requests
from bs4 import BeautifulSoup, Tag # CRÍTICO: Importa Tag para verificação de tipo
import json
import time
import re
import os

# --- Configurações ---
API_FILE_NAME = "eventos.json"
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3
EVENTOS_URL_VISTAS = set() # Rastreia URLs para evitar duplicação em diferentes páginas

# --- Funções Auxiliares Comuns ---

def obter_soup(url):
    """Baixa e parseia o HTML de uma URL, tratando erros de conexão."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"      Erro ao acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    """Garante que uma URL seja absoluta e usa HTTPS."""
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
    texto = texto.replace('\xa0', ' ')
    texto = re.sub(r'\s{2,}', ' ', texto).strip()
    return texto

# --- Funções de Processamento do Conteúdo (BLOCO A BLOCO) ---

def pre_processar_html_conteudo(conteudo):
    """
    Extrai URLs de imagem, remove tags vazias/lixo e prepara o HTML para classificação.
    Corrige o 'AttributeError: 'NoneType' object has no attribute 'get''.
    """
    lista_imagens_conteudo = []
    
    # Itera sobre os filhos diretos do <article>
    for elemento in list(conteudo.children):
        
        # CRÍTICO: PULA ELEMENTOS QUE NÃO SÃO TAGS HTML (ex: strings residuais)
        if not isinstance(elemento, Tag): 
            continue
        
        elemento_classes = elemento.get('class', [])

        # 1. Extrai imagens de DIVs de wrapping e remove a DIV
        if elemento_classes and 'artigo-img-wrap' in elemento_classes:
            img_tag = elemento.find('img')
            if img_tag and img_tag.get('src'):
                url_imagem = completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
                if url_imagem:
                    lista_imagens_conteudo.append(url_imagem)
            elemento.decompose() # Remove a DIV de imagem para não processar como texto
            continue
            
        # 2. Remove parágrafos vazios ou apenas com quebra de linha
        if elemento.name == 'p' and not elemento.get_text(strip=True):
            elemento.decompose()
            continue
            
        # 3. Limpeza de scripts que podem ter tags <p> internas
        if elemento.name in ['script', 'style', 'noscript']:
            elemento.decompose()
            continue
            
    return lista_imagens_conteudo

def classificar_blocos_de_texto(conteudo, lista_imagens_conteudo):
    """
    Itera sobre o conteúdo limpo, classifica (Parágrafo/Subtítulo)
    e insere as imagens de forma intercalada.
    """
    blocos_finais = []
    textos_vistos_hash = set()
    imagem_index = 0
    paragrafo_contador = 0

    # Itera sobre os elementos de texto relevantes
    for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3']): 
        
        texto_html = elemento.decode_contents().strip()
        texto_limpo = limpar_texto(elemento.get_text(strip=True))

        if not texto_limpo: 
            continue

        # Filtro: Ignora blocos muito curtos
        if len(texto_limpo.split()) < 5:
             continue
        
        # Filtro de Duplicação Simples
        trecho_hash = re.sub(r'[\W_]+', '', texto_limpo.lower())[:50] 
        if trecho_hash in textos_vistos_hash:
            continue
        
        # --- Classificação de Subtítulo (Baseada em Tags HTML) ---
        is_subtitle = elemento.name in ['h2', 'h3'] or elemento.find(['strong', 'em'])
        
        blocos_finais.append({
            "type": "SUBTITLE" if is_subtitle else "PARAGRAPH",
            "content": texto_html # Envia como HTML para o Android renderizar o destaque
        })
        textos_vistos_hash.add(trecho_hash)
        
        # --- Lógica de Intercalação de Imagens ---
        if not is_subtitle:
            paragrafo_contador += 1
            # Insere imagem após a cada 2 parágrafos
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
    """Busca o conteúdo detalhado da notícia e retorna os blocos limpos."""
    soup_detalhes = obter_soup(url_detalhes)
    if not soup_detalhes: return []

    conteudo = soup_detalhes.find('article', class_='noticia-conteudo')
    if not conteudo: return []
    
    lista_imagens_conteudo = pre_processar_html_conteudo(conteudo)
    blocos_finais = classificar_blocos_de_texto(conteudo, lista_imagens_conteudo)
        
    return blocos_finais

def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    """Extrai dados principais, busca detalhes e filtra URLs duplicadas."""
    
    img_tag = bloco_img.find('img')
    src_banner_relativo = img_tag['src'] if img_tag else None
    link_imagem_banner = completar_url(src_banner_relativo, URL_BASE_FUNCULTURAL)

    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo_texto = titulo_tag.text.strip() if titulo_tag else "Título não encontrado"

    link_tag = bloco_txt.find('a')
    link_evento_relativo = link_tag['href'] if link_tag else None
    link_evento_completo = completar_url(link_evento_relativo, URL_BASE_FUNCULTURAL)

    if not link_evento_completo or not link_imagem_banner: return None

    # Checagem de exclusividade (para evitar duplicação ao raspar várias páginas)
    if link_evento_completo in EVENTOS_URL_VISTAS:
        print(f"      Evento já visto, pulando: {titulo_texto}")
        return None
        
    EVENTOS_URL_VISTAS.add(link_evento_completo)

    print(f"      Processando: {titulo_texto}")
    
    blocos_de_conteudo = raspar_detalhes_funcultural(link_evento_completo)
    time.sleep(0.3) # Pequeno delay para evitar bloqueio

    if not blocos_de_conteudo:
        # Pula eventos sem conteúdo detalhado
        return None 

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
        print(f"   Raspando página: {url_pagina_atual}")
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

        print(f"   Página {page_num}: {eventos_nesta_pagina} eventos processados.")
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
        print(f"\nSucesso! A API '{API_FILE_NAME}' foi criada com {len(eventos_totais)} eventos.")
    except IOError as e:
        print(f"\nErro ao salvar '{API_FILE_NAME}': {e}")

if __name__ == "__main__":
    main()