import requests
from bs4 import BeautifulSoup
import json
import time

# --- Configurações ---
API_FILE_NAME = "eventos.json"
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3

# --- Funções Auxiliares ---

def obter_soup(url):
    """Baixa e parseia o HTML de uma URL, tratando erros."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"    Erro ao acessar {url}: {e}")
        return None

def limpar_texto(texto):
    """Remove espaços extras e linhas em branco."""
    return ' '.join(texto.split()) if texto else ""

def completar_url(url_relativa, base_url):
    """Garante que uma URL seja absoluta."""
    if not url_relativa: return None
    if url_relativa.startswith('http'): return url_relativa
    if url_relativa.startswith('/'): return f"{base_url}{url_relativa}"
    return None

def raspar_detalhes_funcultural(url_detalhes):
    """Raspa descrição e imagens da página de detalhes."""
    soup_detalhes = obter_soup(url_detalhes)
    if not soup_detalhes: return "", []

    descricao_completa = ""
    lista_imagens_conteudo = []
    conteudo = soup_detalhes.find('article', class_='noticia-conteudo')

    if conteudo:
        paragrafos = conteudo.find_all('p')
        textos_paragrafos = [limpar_texto(p.text) for p in paragrafos]
        descricao_completa = '\n\n'.join(filter(None, textos_paragrafos))

        imagens = conteudo.find_all('img')
        for img in imagens:
            src = img.get('src')
            url_imagem = completar_url(src, URL_BASE_FUNCULTURAL)
            if url_imagem:
                lista_imagens_conteudo.append(url_imagem)

    return descricao_completa, lista_imagens_conteudo

# --- NOVA FUNÇÃO: Processa um par de blocos ---
def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    """Extrai dados de um par (imagem+texto) e busca detalhes."""
    img_tag = bloco_img.find('img')
    src_banner_relativo = img_tag['src'] if img_tag else None
    link_imagem_banner = completar_url(src_banner_relativo, URL_BASE_FUNCULTURAL)

    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo_texto = limpar_texto(titulo_tag.text) if titulo_tag else "Título não encontrado"

    link_tag = bloco_txt.find('a')
    link_evento_relativo = link_tag['href'] if link_tag else None
    link_evento_completo = completar_url(link_evento_relativo, URL_BASE_FUNCULTURAL)

    if not link_evento_completo or not link_imagem_banner:
         print(f"    Aviso: Ignorando item sem link ou imagem ({titulo_texto})")
         return None # Retorna None se faltar informação essencial

    print(f"    Processando: {titulo_texto}")
    descricao_completa, imagens_do_conteudo = raspar_detalhes_funcultural(link_evento_completo)
    time.sleep(0.3) # Pausa após buscar detalhes

    descricao_final = descricao_completa
    if not descricao_final:
         desc_tag_curta = bloco_txt.find('div', class_='descricao-noticia')
         descricao_final = limpar_texto(desc_tag_curta.text) if desc_tag_curta else ""

    return {
        "titulo": titulo_texto,
        "descricao": descricao_final,
        "imagem_url": link_imagem_banner,
        "link_evento": link_evento_completo,
        "fonte": "Funcultural",
        "imagens_conteudo": imagens_do_conteudo
    }

# --- Função principal de raspagem (AGORA MAIS SIMPLES) ---
def raspar_funcultural():
    """Raspa as N primeiras páginas da lista de notícias da Funcultural."""
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

            # Chama a nova função para processar o par
            evento = processar_par_blocos_funcultural(bloco_img, bloco_txt)
            if evento: # Adiciona apenas se a função retornar um evento válido
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