import requests
from bs4 import BeautifulSoup, Tag
import json
import time
import re
import os
import unicodedata
import hashlib

# Config
API_DIR = os.path.abspath("api_output")
API_INDEX_FILE = os.path.join(API_DIR, "eventos_index.json")
API_LIST_FILE = os.path.join(API_DIR, "eventos.json")
LOCKFILE = os.path.join(API_DIR, ".running.lock")
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3
EVENTOS_URL_VISTAS = set()
os.makedirs(API_DIR, exist_ok=True)

# util
def normalize_text(s):
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'<[^>]*>', '', s)
    s = s.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', s).strip()

def generate_id(ev):
    key = (ev.get("titulo", "") + "|" + ev.get("link_evento", "")).strip()
    return hashlib.sha1(normalize_text(key).encode("utf-8")).hexdigest()

def obter_soup(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; scraper/1.0)"}
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        return BeautifulSoup(r.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Erro acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    if not url_relativa: return None
    u = url_relativa.strip()
    if u.startswith('http://') or u.startswith('https://'):
        return u.replace('http://', 'https://')
    base = base_url.rstrip('/')
    return f"{base}{u}" if u.startswith('/') else f"{base}/{u}"

def limpar_texto(texto):
    texto = re.sub(r'(Fotos|Foto|Texto):\s*[^.\n]+', '', texto, flags=re.IGNORECASE)
    texto = texto.replace('\xa0', ' ')
    return re.sub(r'\s{2,}', ' ', texto).strip()

def is_tag(element):
    return isinstance(element, Tag)

def extract_image_from_wrapper(element):
    img_tag = element.find('img')
    if img_tag and img_tag.get('src'):
        return completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
    return None

def should_remove_element(element):
    if not is_tag(element): return True
    if element.name in ['script', 'style', 'noscript']: return True
    if element.name == 'p' and not element.get_text(strip=True): return True
    return False

# content processing
def pre_processar_html_conteudo(conteudo):
    imgs = []
    for elemento in list(conteudo.children):
        if not is_tag(elemento): continue
        classes = elemento.get('class', [])
        if classes and 'artigo-img-wrap' in classes:
            url = extract_image_from_wrapper(elemento)
            if url: imgs.append(url)
            elemento.decompose()
            continue
        if should_remove_element(elemento):
            elemento.decompose()
            continue
    return imgs

def build_text_block(element):
    texto_html = element.decode_contents().strip()
    texto_limpo = limpar_texto(element.get_text(strip=True))
    if not texto_limpo or len(texto_limpo.split()) < 5:
        return None
    trecho_hash = re.sub(r'[\W_]+', '', texto_limpo.lower())[:80]
    is_subtitle = element.name in ['h2', 'h3'] or bool(element.find(['strong', 'em']))
    return {"hash": trecho_hash, "block": {"type": "SUBTITLE" if is_subtitle else "PARAGRAPH", "content": texto_html}, "plain": texto_limpo, "is_subtitle": is_subtitle}

def intercalate_images(blocos, imagens):
    out = []
    img_i = 0
    para_count = 0
    for item in blocos:
        out.append(item["block"])
        if not item["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imagens):
                out.append({"type": "PARAGRAPH", "content": f'<img src="{imagens[img_i]}" />'})
                img_i += 1
    while img_i < len(imagens):
        out.append({"type": "PARAGRAPH", "content": f'<img src="{imagens[img_i]}" />'})
        img_i += 1
    return out

def classificar_blocos_de_texto(conteudo, lista_imagens_conteudo):
    temp_blocks = []
    seen_hashes = set()
    # first-pass top-level
    for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3'], recursive=False):
        built = build_text_block(elemento)
        if not built: continue
        if built["hash"] in seen_hashes: continue
        seen_hashes.add(built["hash"])
        temp_blocks.append(built)
    # fallback deep
    if not temp_blocks:
        for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3']):
            built = build_text_block(elemento)
            if not built: continue
            if built["hash"] in seen_hashes: continue
            seen_hashes.add(built["hash"])
            temp_blocks.append(built)
    # if no text blocks, return images only
    if not temp_blocks and lista_imagens_conteudo:
        return [{"type": "PARAGRAPH", "content": f'<img src="{img}" />'} for img in lista_imagens_conteudo]
    # detect aggregated large block
    lengths = [len(b["plain"]) for b in temp_blocks]
    if lengths:
        max_len = max(lengths)
        sorted_lengths = sorted(lengths, reverse=True)
        second_len = sorted_lengths[1] if len(sorted_lengths) > 1 else 0
        avg_len = sum(lengths) / len(lengths)
        if max_len >= 600 or (max_len >= 300 and max_len > 1.6 * max(second_len, avg_len)):
            for b in temp_blocks:
                if len(b["plain"]) == max_len:
                    bloco_unico = [b["block"]]
                    # add extracted images if not inline
                    if '<img' not in (b["block"]["content"] or "").lower():
                        for img in lista_imagens_conteudo:
                            bloco_unico.append({"type": "PARAGRAPH", "content": f'<img src="{img}" />'})
                    return bloco_unico
    return intercalate_images(temp_blocks, lista_imagens_conteudo)

# details scraping
def raspar_detalhes_funcultural(url_detalhes):
    soup = obter_soup(url_detalhes)
    if not soup: return []
    conteudo = soup.find('article', class_='noticia-conteudo')
    if not conteudo:
        conteudo = soup.find('div', class_='content') or soup.find('div', class_='article-content')
        if not conteudo: return []
    imgs = pre_processar_html_conteudo(conteudo)
    return classificar_blocos_de_texto(conteudo, imgs)

# list processing
def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    img_tag = bloco_img.find('img')
    src_banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else None
    link_imagem_banner = completar_url(src_banner_rel, URL_BASE_FUNCULTURAL)
    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo_texto = titulo_tag.get_text(strip=True) if titulo_tag else "Título não encontrado"
    link_tag = bloco_txt.find('a')
    link_evento_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link_evento = completar_url(link_evento_rel, URL_BASE_FUNCULTURAL)
    if not link_evento: return None
    if link_evento in EVENTOS_URL_VISTAS:
        print(f"Evento já visto, pulando: {titulo_texto}")
        return None
    EVENTOS_URL_VISTAS.add(link_evento)
    print(f"Processando: {titulo_texto}")
    blocos = raspar_detalhes_funcultural(link_evento)
    time.sleep(0.3)
    if not blocos: return None
    return {"titulo": normalize_text(titulo_texto), "blocos_conteudo": blocos, "imagem_url": link_imagem_banner or "", "link_evento": link_evento, "fonte": "Funcultural"}

def raspar_funcultural():
    print(f"Iniciando raspagem (1..{NUMERO_DE_PAGINAS_FUNCULTURAL})")
    lista_total = []
    for page_num in range(1, NUMERO_DE_PAGINAS_FUNCULTURAL + 1):
        url_page = f"{URL_NOTICIAS_FUNCULTURAL}?page={page_num}"
        print(f" Raspando: {url_page}")
        soup = obter_soup(url_page)
        if not soup: continue
        blocos = soup.find_all('div', class_='resultado-pesquisa')
        i = 0
        eventos_pagina = 0
        while i < len(blocos):
            bloco_img = blocos[i]
            bloco_txt = blocos[i+1] if i+1 < len(blocos) else blocos[i]
            i += 2 if i+1 < len(blocos) else 1
            evento = processar_par_blocos_funcultural(bloco_img, bloco_txt)
            if evento:
                lista_total.append(evento)
                eventos_pagina += 1
        print(f" Página {page_num}: {eventos_pagina} eventos")
        if page_num < NUMERO_DE_PAGINAS_FUNCULTURAL: time.sleep(1)
    print(f"Total antes dedupe: {len(lista_total)}")
    # dedupe final
    unique_map = {}
    for ev in lista_total:
        chave_norm = normalize_text((ev.get("titulo","") + "|" + ev.get("link_evento","")).strip())
        h = hashlib.sha1(chave_norm.encode('utf-8')).hexdigest()
        if h in unique_map:
            print(f" Ignorando duplicado: {ev.get('titulo')}")
            continue
        ev["titulo"] = normalize_text(ev.get("titulo",""))
        ev["imagem_url"] = ev.get("imagem_url","")
        ev["link_evento"] = ev.get("link_evento","")
        ev["blocos_conteudo"] = ev.get("blocos_conteudo", [])
        ev["id"] = generate_id(ev)
        unique_map[h] = ev
    eventos_unicos = list(unique_map.values())
    print(f"Total após dedupe: {len(eventos_unicos)}")
    # cleanup old outputs
    for f in os.listdir(API_DIR):
        if re.fullmatch(r'[0-9a-f]{40}\.json', f):
            try: os.remove(os.path.join(API_DIR, f))
            except OSError: pass
    for p in (API_INDEX_FILE, API_LIST_FILE):
        if os.path.exists(p):
            try: os.remove(p)
            except OSError: pass
    # save files
    index_list = []
    for ev in eventos_unicos:
        index_list.append({"id": ev["id"], "titulo": ev["titulo"], "imagem_url": ev.get("imagem_url",""), "link_evento": ev.get("link_evento",""), "fonte": ev.get("fonte","")})
        filename = os.path.join(API_DIR, f"{ev['id']}.json")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(ev, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f" Erro salvar {filename}: {e}")
    try:
        with open(API_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_list, f, ensure_ascii=False, indent=2)
        print(f" Index salvo: {API_INDEX_FILE} ({len(index_list)} itens).")
    except IOError as e:
        print(f" Erro salvar index: {e}")
    try:
        with open(API_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(eventos_unicos, f, ensure_ascii=False, indent=2)
        print(f" Lista salva: {API_LIST_FILE}")
    except IOError as e:
        print(f" Erro salvar lista: {e}")
    return eventos_unicos

def main():
    print("Iniciando agregador de cultura...")
    global EVENTOS_URL_VISTAS
    EVENTOS_URL_VISTAS = set()
    if os.path.exists(LOCKFILE):
        print("Outra instância em execução. Abortando.")
        return
    open(LOCKFILE, "w").close()
    try:
        eventos = raspar_funcultural()
        print(f"Sucesso! {len(eventos)} eventos gerados em '{API_DIR}'.")
    finally:
        try: os.remove(LOCKFILE)
        except OSError: pass

if __name__ == "__main__":
    main()
