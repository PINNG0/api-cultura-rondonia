import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

API_FILE_NAME = "eventos.json"
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3

def obter_soup(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    if not url_relativa: return None
    if url_relativa.startswith('http'):
        return url_relativa.replace('http://', 'https://')
    if url_relativa.startswith('/'):
        return f"{base_url.replace('http://', 'https://')}{url_relativa}"
    return f"{base_url.rstrip('/')}/{url_relativa.lstrip('/')}"

def limpar_texto(texto):
    texto = re.sub(r'(Fotos|Texto):\s*[^.\n]+', '', texto, flags=re.IGNORECASE)
    texto = texto.replace('\xa0', ' ')
    return re.sub(r'\s{2,}', ' ', texto).strip()

def pre_processar_html_conteudo(conteudo):
    imgs = []
    for e in conteudo.find_all(True):
        if e.get('class') and 'artigo-img-wrap' in e.get('class'):
            img_tag = e.find('img')
            if img_tag and img_tag.get('src'):
                url = completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
                if url: imgs.append(url)
            e.decompose()
    # remove todas as imgs restantes
    for img in conteudo.find_all('img'):
        img.decompose()
    for p in conteudo.find_all('p'):
        if not p.get_text(strip=True):
            p.decompose()
    return imgs
def classificar_blocos_de_texto(conteudo, lista_imagens):
    """
    Classifica o conteúdo do artigo em blocos de texto (SUBTITLE/PARAGRAPH)
    e intercala com blocos de imagem.
    """
    blocos, img_idx, par_cont = [], 0, 0
    # Elementos de bloco que contêm texto principal
    elementos_de_texto = conteudo.find_all(['p', 'h2', 'h3', 'blockquote', 'li'])

    for e in elementos_de_texto:
        txt_limpo = limpar_texto(e.get_text(strip=True))

        # Evita blocos muito curtos ou apenas marcadores de autoria
        if len(txt_limpo.split()) < 3 or txt_limpo.lower().startswith(("texto:", "fotos:", "fonte:")):
            continue
        
        # O uso de decode_contents() aqui pode ser problemático se houver tags
        # não fechadas ou malformadas. Usaremos get_text() para o conteúdo e formatamos.
        
        txt_html = ''.join(str(child) for child in e.children if child.name is not None)
        if not txt_html: # Se não houver tags, pega o texto puro
             txt_html = txt_limpo

        # Heurística para subtítulo: h2, h3 ou parágrafo com poucas palavras em negrito
        is_sub = (e.name in ['h2', 'h3'] or 
                  (e.name == 'p' and e.find('strong') and len(txt_limpo.split()) <= 10))
        
        blocos.append({"type": "SUBTITLE" if is_sub else "PARAGRAPH", "content": txt_html})
        
        if not is_sub:
            par_cont += 1
            # Intercalar imagem a cada 2 parágrafos
            if par_cont % 2 == 0 and img_idx < len(lista_imagens):
                blocos.append({"type": "IMAGE_URL", "content": lista_imagens[img_idx]})
                img_idx += 1
        
    # Adicionar quaisquer imagens restantes no final
    while img_idx < len(lista_imagens):
        blocos.append({"type": "IMAGE_URL", "content": lista_imagens[img_idx]})
        img_idx += 1
        
    return blocos

def raspar_detalhes_funcultural(url):
    soup = obter_soup(url)
    if not soup: return []
    conteudo = soup.find('article', class_='noticia-conteudo')
    if not conteudo: return []
    imgs = pre_processar_html_conteudo(conteudo)
    return classificar_blocos_de_texto(conteudo, imgs)

def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    img_tag = bloco_img.find('img')
    src = img_tag['src'] if img_tag else None
    link_img = completar_url(src, URL_BASE_FUNCULTURAL)
    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo = titulo_tag.text.strip() if titulo_tag else "Título não encontrado"
    link_tag = bloco_txt.find('a')
    link_evento = completar_url(link_tag['href'], URL_BASE_FUNCULTURAL) if link_tag else None
    if not link_img or not link_evento: return None
    print(f"Processando: {titulo}")
    blocos = raspar_detalhes_funcultural(link_evento)
    time.sleep(0.3)
    return {"titulo": titulo, "blocos_conteudo": blocos, "imagem_url": link_img, "link_evento": link_evento, "fonte": "Funcultural"}

def raspar_funcultural():
    print(f"Iniciando raspagem (1 a {NUMERO_DE_PAGINAS_FUNCULTURAL})...")
    total = []
    for page in range(1, NUMERO_DE_PAGINAS_FUNCULTURAL+1):
        url = f"{URL_NOTICIAS_FUNCULTURAL}?page={page}"
        print(f"Página: {url}")
        soup = obter_soup(url)
        if not soup: continue
        blocos = soup.find_all('div', class_='resultado-pesquisa')
        count = 0
        for i in range(0, len(blocos), 2):
            if i+1 >= len(blocos): continue
            e = processar_par_blocos_funcultural(blocos[i], blocos[i+1])
            if e and e["blocos_conteudo"]:
                total.append(e)
                count += 1
        print(f"Página {page}: {count} eventos processados")
        if page < NUMERO_DE_PAGINAS_FUNCULTURAL: time.sleep(1)
    print(f"Total: {len(total)} eventos")
    return total

def main():
    print("Iniciando robô...")
    eventos = raspar_funcultural()
    os.makedirs(os.path.dirname(API_FILE_NAME) or ".", exist_ok=True)
    try:
        with open(API_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(eventos, f, ensure_ascii=False, indent=4)
        print(f"API '{API_FILE_NAME}' criada com {len(eventos)} eventos")
    except IOError as e:
        print(f"Erro ao salvar: {e}")

if __name__ == "__main__":
    main()
