import requests
from bs4 import BeautifulSoup, Tag
import json, time, re, os, unicodedata, hashlib

# Config
API_DIR = os.path.abspath("api_output")
API_INDEX_FILE = os.path.join(API_DIR, "eventos_index.json")
API_LIST_FILE = os.path.join(API_DIR, "eventos.json")
LOCKFILE = os.path.join(API_DIR, ".running.lock")
URL_BASE = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS = f"{URL_BASE}/noticias"
NUM_PAGES = 3
EVENTOS_URL_VISTAS = set()
os.makedirs(API_DIR, exist_ok=True)

# Utilitários curtos
def norm_text(s):
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'<[^>]*>', '', s)
    s = s.replace('\xa0',' ')
    return re.sub(r'\s+', ' ', s).strip()

def gen_id(ev):
    key = (ev.get("titulo","") + "|" + ev.get("link_evento","")).strip()
    return hashlib.sha1(norm_text(key).encode('utf-8')).hexdigest()

def get_soup(url):
    try:
        h = {"User-Agent":"Mozilla/5.0 (scraper)"}
        r = requests.get(url, timeout=10, headers=h)
        r.raise_for_status()
        return BeautifulSoup(r.content, 'html.parser')
    except requests.RequestException as e:
        print("Erro acessar:", url, e)
        return None

def complete_url(u, base=URL_BASE):
    if not u: return None
    u = u.strip()
    if u.startswith('http://') or u.startswith('https://'):
        return u.replace('http://','https://')
    base = base.rstrip('/')
    return f"{base}{u}" if u.startswith('/') else f"{base}/{u}"

def clean_text_simple(html):
    if not html: return ""
    t = re.sub(r'(?s)<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', t).strip()

# Conteúdo: extrair imagens wrappers e limpar nós inúteis
def preproc_content(article):
    imgs = []
    for child in list(article.children):
        if not isinstance(child, Tag): continue
        classes = child.get('class', [])
        if classes and 'artigo-img-wrap' in classes:
            img = child.find('img')
            if img and img.get('src'):
                imgs.append(complete_url(img.get('src')))
            child.decompose(); continue
        if child.name in ['script','style','noscript']: child.decompose(); continue
        if child.name == 'p' and not child.get_text(strip=True): child.decompose(); continue
    return imgs

def build_block(elem):
    html = elem.decode_contents().strip()
    plain = clean_text_simple(elem.get_text(strip=True))
    if not plain or len(plain.split()) < 5: return None
    is_title = elem.name in ['h2','h3'] or bool(elem.find(['strong','em']))
    return {"type": "SUBTITLE" if is_title else "PARAGRAPH", "content": html, "plain": plain, "is_subtitle": is_title}

def interleave_images(blocks, imgs):
    out = []; img_i = 0; para_count = 0
    for b in blocks:
        out.append({"type": b["type"], "content": b["content"]})
        if not b["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imgs):
                out.append({"type":"PARAGRAPH","content":f'<img src="{imgs[img_i]}" />'}); img_i += 1
    while img_i < len(imgs):
        out.append({"type":"PARAGRAPH","content":f'<img src="{imgs[img_i]}" />'}); img_i += 1
    return out

def classify_blocks(article, imgs):
    blocks = []
    seen = set()
    for e in article.find_all(['p','div','h2','h3'], recursive=False):
        b = build_block(e)
        if not b: continue
        h = re.sub(r'[\W_]+','', b["plain"].lower())[:80]
        if h in seen: continue
        seen.add(h); blocks.append(b)
    if not blocks:
        for e in article.find_all(['p','div','h2','h3']):
            b = build_block(e)
            if not b: continue
            h = re.sub(r'[\W_]+','', b["plain"].lower())[:80]
            if h in seen: continue
            seen.add(h); blocks.append(b)
    if not blocks and imgs:
        return [{"type":"PARAGRAPH","content":f'<img src="{i}" />'} for i in imgs]
    lengths = [len(b["plain"]) for b in blocks]
    if lengths:
        max_len = max(lengths)
        sorted_l = sorted(lengths, reverse=True)
        second = sorted_l[1] if len(sorted_l) > 1 else 0
        avg = sum(lengths)/len(lengths)
        if max_len >= 600 or (max_len >= 300 and max_len > 1.6 * max(second, avg)):
            for b in blocks:
                if len(b["plain"]) == max_len:
                    single = [{"type": b["type"], "content": b["content"]}]
                    if '<img' not in (b["content"] or "").lower():
                        for i in imgs: single.append({"type":"PARAGRAPH","content":f'<img src="{i}" />'})
                    return single
    return interleave_images(blocks, imgs)

# Detalhes
def scrape_details(url):
    soup = get_soup(url)
    if not soup: return []
    article = soup.find('article', class_='noticia-conteudo') or soup.find('div', class_='content') or soup.find('div', class_='article-content')
    if not article: return []
    imgs = preproc_content(article)
    return classify_blocks(article, imgs)

# Lista/paginação
def process_pair(img_block, txt_block):
    img_tag = img_block.find('img') if img_block else None
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else None
    banner = complete_url(banner_rel)
    title_tag = txt_block.find('div', class_='titulo-noticia-pesquisa') if txt_block else None
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"
    link_tag = txt_block.find('a') if txt_block else None
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = complete_url(link_rel)
    if not link: return None
    if link in EVENTOS_URL_VISTAS: 
        print("Já visto:", title); return None
    EVENTOS_URL_VISTAS.add(link)
    print("Processando:", title)
    blocks = scrape_details(link)
    time.sleep(0.25)
    if not blocks: return None
    return {"titulo": norm_text(title), "blocos_conteudo": blocks, "imagem_url": banner or "", "link_evento": link, "fonte": "Funcultural"}

def scrape_all():
    print("Iniciando raspagem")
    all_events = []
    for p in range(1, NUM_PAGES+1):
        url = f"{URL_NOTICIAS}?page={p}"
        print("Página:", url)
        soup = get_soup(url); 
        if not soup: continue
        results = soup.find_all('div', class_='resultado-pesquisa')
        i = 0; page_count = 0
        while i < len(results):
            img_b = results[i]
            txt_b = results[i+1] if i+1 < len(results) else results[i]
            i += 2 if i+1 < len(results) else 1
            ev = process_pair(img_b, txt_b)
            if ev: all_events.append(ev); page_count += 1
        print("Processados na página:", page_count)
        if p < NUM_PAGES: time.sleep(1)
    print("Total antes dedupe:", len(all_events))
    # dedupe final por titulo+link
    unique = {}
    for ev in all_events:
        key = norm_text((ev.get("titulo","") + "|" + ev.get("link_evento","")).strip())
        h = hashlib.sha1(key.encode('utf-8')).hexdigest()
        if h in unique:
            print("Ignorando duplicado:", ev.get("titulo"))
            continue
        ev["titulo"] = norm_text(ev.get("titulo",""))
        ev["id"] = gen_id(ev)
        unique[h] = ev
    events = list(unique.values())
    print("Total após dedupe:", len(events))
    return events

# Salva apenas arquivos agregados
def save_only(events, remove_individual=True):
    index = []
    for ev in events:
        index.append({"id": ev["id"], "titulo": ev["titulo"], "imagem_url": ev.get("imagem_url",""), "link_evento": ev.get("link_evento",""), "fonte": ev.get("fonte","")})
    # opcional: remover arquivos individuais SHA .json antigos
    if remove_individual:
        for fn in os.listdir(API_DIR):
            if re.fullmatch(r'[0-9a-f]{40}\.json', fn):
                try: os.remove(os.path.join(API_DIR, fn))
                except OSError: pass
    # escrever index e lista agregada
    try:
        with open(API_INDEX_FILE, 'w', encoding='utf-8') as f: json.dump(index, f, ensure_ascii=False, indent=2)
        with open(API_LIST_FILE, 'w', encoding='utf-8') as f: json.dump(events, f, ensure_ascii=False, indent=2)
        print("Salvo:", API_LIST_FILE, "e", API_INDEX_FILE)
    except IOError as e:
        print("Erro salvar arquivos:", e)

# Execução segura com lock
def main():
    print("Start")
    if os.path.exists(LOCKFILE):
        print("Outra instância em execução. Abortando."); return
    open(LOCKFILE, 'w').close()
    try:
        evs = scrape_all()
        save_only(evs, remove_individual=True)
        print("Concluído. Eventos:", len(evs))
    finally:
        try: os.remove(LOCKFILE)
        except OSError: pass

if __name__ == "__main__":
    main()
