import requests
from bs4 import BeautifulSoup
import json
import time
import re

# --- Configurações ---
API_FILE_NAME = "eventos.json"
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3 

# --- Funções Auxiliares ---

def obter_soup(url):
    """Baixa e parseia o HTML de uma URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"    Erro ao acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    """Garante que uma URL seja absoluta."""
    if not url_relativa: return None
    if url_relativa.startswith('http'): return url_relativa
    if url_relativa.startswith('/'): return f"{base_url}{url_relativa}"
    return None

def limpar_descricao(texto):
    """Remove padrões de créditos de foto e limpa espaços extras."""
    # Remove padrões de crédito
    texto = re.sub(r'(Fotos|Texto):\s*[^.\n]+', '', texto, flags=re.IGNORECASE)
    # Remove espaços duplicados
    texto = re.sub(r'\s{2,}', ' ', texto).strip()
    return texto

# --- Função Principal de Raspagem ---

def raspar_detalhes_funcultural(url_detalhes):
    """Raspa descrição e URLs de imagens do conteúdo, limpando o HTML problemático."""
    soup_detalhes = obter_soup(url_detalhes)
    if not soup_detalhes: return "", []

    lista_imagens_conteudo = []
    descricao_completa = ""
    
    conteudo = soup_detalhes.find('article', class_='noticia-conteudo')
    
    if conteudo:
        # 1. Extrai Imagens e Pré-processamento (Resolve Colagem)
        for elemento in conteudo.find_all(True): # Itera sobre TODAS as tags
            # Lógica para remover a tag de imagem e extrair a URL
            if elemento.get('class') and 'artigo-img-wrap' in elemento.get('class'):
                img_tag = elemento.find('img')
                if img_tag and img_tag.get('src'):
                     url_imagem = completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
                     if url_imagem:
                        lista_imagens_conteudo.append(url_imagem)
                elemento.decompose() # Remove a tag flutuante

            # Lógica para Tags de Formatação: Substitui por seu texto + ESPAÇO
            elif elemento.name in ['strong', 'em', 'span', 'b', 'i']:
                # Substitui a tag pelo seu texto + um espaço para forçar a separação
                elemento.replace_with(elemento.get_text(strip=True) + ' ')

        # 2. Extração Final do Texto (Agora Limpo e Ordenado)
        textos_paragrafos = []
        
        # Agora, iteramos sobre os parágrafos e divs que restaram
        for bloco in conteudo.find_all(['p', 'div']): 
            paragrafo_limpo = bloco.get_text(strip=True)
            if paragrafo_limpo:
                textos_paragrafos.append(paragrafo_limpo)

        # Junta tudo com o separador \n\n (que será convertido em <br> no Android)
        descricao_bruta = '\n\n'.join(textos_paragrafos)

        # 3. Limpeza Final
        descricao_completa = limpar_descricao(descricao_bruta)

    return descricao_completa, lista_imagens_conteudo

def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    """Extrai dados e busca detalhes para um par de blocos."""
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
    descricao_completa, imagens_do_conteudo = raspar_detalhes_funcultural(link_evento_completo)
    time.sleep(0.3) 

    descricao_final = descricao_completa
    if not descricao_final:
         desc_tag_curta = bloco_txt.find('div', class_='descricao-noticia')
         descricao_final = desc_tag_curta.text.strip() if desc_tag_curta else ""

    return {
        "titulo": titulo_texto,
        "descricao": descricao_final,
        "imagem_url": link_imagem_banner,
        "link_evento": link_evento_completo,
        "fonte": "Funcultural",
        "imagens_conteudo": imagens_do_conteudo
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