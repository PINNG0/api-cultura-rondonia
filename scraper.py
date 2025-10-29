import requests
from bs4 import BeautifulSoup, Tag
import json, time, re, os, unicodedata, hashlib
import subprocess
from datetime import datetime, timedelta

# Configura diretórios e URLs
API_DIR = os.path.abspath("api_output")
API_INDEX_FILE = os.path.join(API_DIR, "eventos_index.json")
API_LIST_FILE = os.path.join(API_DIR, "eventos.json")
LOCKFILE = os.path.join(API_DIR, ".running.lock")
URL_BASE = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS = f"{URL_BASE}/noticias"
EVENTOS_URL_VISTAS = set()
os.makedirs(API_DIR, exist_ok=True)

# Normaliza texto removendo tags e espaços
def norm_text(s):
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'<[^>]*>', '', s)
    s = s.replace('\xa0',' ')
    return re.sub(r'\s+', ' ', s).strip()

# Gera hash único para cada evento
def gen_id(ev):
    key = (ev.get("titulo","") + "|" + ev.get("link_evento","")).strip()
    return hashlib.sha1(norm_text(key).encode('utf-8')).hexdigest()

# Obtém HTML da página
def get_soup(url):
    try:
        h = {"User-Agent":"Mozilla/5.0 (scraper)"}
        r = requests.get(url, timeout=10, headers=h)
        r.raise_for_status()
        return BeautifulSoup(r.content, 'html.parser')
    except requests.RequestException as e:
        print("Erro acessar:", url, e)
        return None

# Corrige URLs relativas
def complete_url(u, base=URL_BASE):
    if not u: return None
    u = u.strip()
    if u.startswith('http://') or u.startswith('https://'):
        return u.replace('http://','https://')
    base = base.rstrip('/')
    return f"{base}{u}" if u.startswith('/') else f"{base}/{u}"

# Remove tags HTML simples
def clean_text_simple(html):
    if not html: return ""
    t = re.sub(r'(?s)<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', t).strip()

# Extrai imagens e limpa elementos inúteis
def preproc_content(article):
    imgs = []
    # Itera sobre os filhos diretos do <article>
    for child in list(article.children):
        
        # CRÍTICO: PULA ELEMENTOS QUE NÃO SÃO TAGS HTML (ex: strings residuais)
        if not isinstance(child, Tag): 
            continue
        
        classes = child.get('class', [])

        # 1. Extrai imagens de DIVs de wrapping e remove a DIV
        if classes and 'artigo-img-wrap' in classes:
            img = child.find('img')
            if img and img.get('src'):
                imgs.append(complete_url(img.get('src')))
            child.decompose() # Remove a DIV de imagem para não processar como texto
            continue
            
        # 2. Remove parágrafos vazios ou apenas com quebra de linha
        if child.name == 'p' and not child.get_text(strip=True): 
            child.decompose()
            continue
            
        # 3. Limpeza de scripts que podem ter tags <p> internas
        if child.name in ['script','style','noscript']: child.decompose(); continue
        
    return imgs

# Cria bloco de conteúdo com tipo e texto limpo
def build_block(elem):
    html = elem.decode_contents().strip()
    plain = clean_text_simple(elem.get_text(strip=True))
    if not plain or len(plain.split()) < 5: return None
    is_title = elem.name in ['h2','h3'] or bool(elem.find(['strong','em']))
    return {"type": "SUBTITLE" if is_title else "PARAGRAPH", "content": html, "plain": plain, "is_subtitle": is_title}

# Insere imagens entre parágrafos
def interleave_images(blocks, imgs):
    out = []; img_i = 0; para_count = 0
    for b in blocks:
        out.append({"type": b["type"], "content": b["content"]})
        if not b["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imgs):
                out.append({"type":"IMAGE_URL","content":imgs[img_i]}); img_i += 1
    while img_i < len(imgs):
        out.append({"type":"IMAGE_URL","content":imgs[img_i]}); img_i += 1
    return out

# Classifica blocos
def classify_blocks(article, imgs):
    blocks = []
    seen = set()
    for e in article.find_all(['p','div','h2','h3'], recursive=False):
        b = build_block(e)
        if not b: continue
        h = re.sub(r'[\W_]+','', b["plain"].lower())[:80]
        if h in seen: continue
        seen.add(h); blocks.append(b)

    # Fallback para conteúdo mais profundo se o primeiro nível falhar
    if not blocks:
        for e in article.find_all(['p','div','h2','h3']):
            b = build_block(e)
            if not b: continue
            h = re.sub(r'[\W_]+','', b["plain"].lower())[:80]
            if h in seen: continue
            seen.add(h); blocks.append(b)

    if not blocks and imgs:
        return [{"type":"IMAGE_URL","content":i} for i in imgs]

    # Lógica de agrupamento de blocos grandes (mantida)
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
                        for i in imgs: single.append({"type":"IMAGE_URL","content":i})
                    return single

    return interleave_images(blocks, imgs)

# Raspagem detalhada de uma notícia
def scrape_details(url):
    soup = get_soup(url)
    if not soup: return []
    article = soup.find('article', class_='noticia-conteudo') or soup.find('div', class_='content') or soup.find('div', class_='article-content')
    if not article: return []
    imgs = preproc_content(article)
    return classify_blocks(article, imgs)

# Processa par imagem + texto
def process_pair(img_block, txt_block):
    img_tag = img_block.find('img') if img_block else None
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else None
    banner = complete_url(banner_rel)
    title_tag = txt_block.find('div', class_='titulo-noticia-pesquisa') if txt_block else None
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"
    link_tag = txt_block.find('a') if txt_block else None
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = complete_url(link_rel)
    
    # NOVO: Extrai o texto da data de exibição (ex: "há 1 semana")
    date_tag = txt_block.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    if not link: return None
    if link in EVENTOS_URL_VISTAS: 
        print("Já visto:", title); return None
    EVENTOS_URL_VISTAS.add(link)
    
    print("Processando:", title)
    blocks = scrape_details(link)
    time.sleep(0.25)
    if not blocks: return None
    
    return {
        "titulo": norm_text(title), 
        "blocos_conteudo": blocks, 
        "imagem_url": banner or "", 
        "link_evento": link, 
        "fonte": "Funcultural",
        "data_exibicao": data_exibicao # <-- CAMPO ADICIONADO
    }

# Raspagem de todas as páginas
def scrape_all():
    print("Iniciando raspagem")
    all_events = []
    pagina = 1

    while True:
        url = f"{URL_NOTICIAS}?page={pagina}"
        print("Página:", url)
        soup = get_soup(url)
        
        # Lógica de parada (se não houver soup ou a paginação sumir)
        pagination = soup.find('ul', class_='pagination') if soup else None
        if not soup or (pagination and len(pagination.find_all('li')) <= 1): break

        results = soup.find_all('div', class_='resultado-pesquisa')
        if not results:
            print("Nenhum resultado na página", pagina)
            break

        i = 0; page_count = 0
        while i < len(results):
            img_b = results[i]
            txt_b = results[i+1] if i+1 < len(results) else results[i]
            i += 2 if i+1 < len(results) else 1
            
            ev = process_pair(img_b, txt_b)
            if ev: all_events.append(ev); page_count += 1

        print("Processados na página:", page_count)
        
        # CRÍTICO: Checa se deve parar de iterar nas páginas
        next_page = soup.select_one(f'ul.pagination a[href*="page={pagina + 1}"]')
        if not next_page and pagina >= 3: # Limita a 3 páginas se não encontrar botão "próximo"
            break
            
        pagina += 1
        time.sleep(1)

    print("Total antes dedupe:", len(all_events))
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

# Salva arquivos e copia para docs/ e pages/
def save_only(events, remove_individual=True):
    # Lógica de save e push (mantida como a última versão)
    # ...
    
    os.makedirs(API_DIR, exist_ok=True)

    with open(API_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    # Note que o índice (index) também é atualizado
    index = [{"id": ev["id"], "titulo": ev["titulo"], "imagem_url": ev["imagem_url"], "link_evento": ev["link_evento"], "fonte": ev["fonte"], "data_exibicao": ev["data_exibicao"]} for ev in events]
    with open(API_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print("Salvo:", API_LIST_FILE, "e", API_INDEX_FILE)

    # Copia para docs/api_output
    try:
        docs_dir = os.path.abspath("docs/api_output")
        os.makedirs(docs_dir, exist_ok=True)
        for fname in ["eventos.json", "eventos_index.json"]:
            src = os.path.join(API_DIR, fname)
            dst = os.path.join(docs_dir, fname)
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
        print("Arquivos copiados para:", docs_dir)
    except Exception as e:
        print("Erro ao copiar para docs/api_output:", e)

    # Copia para pages/
    try:
        pages_dir = os.path.abspath("pages")
        os.makedirs(pages_dir, exist_ok=True)
        for fname in ["eventos.json", "eventos_index.json"]:
            src = os.path.join(API_DIR, fname)
            dst = os.path.join(pages_dir, fname)
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
        print("Arquivos copiados para:", pages_dir)
    except Exception as e:
        print("Erro ao copiar para pages/:", e)

# Commit e push automático local
def run_git_operations():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Atualiza dados raspados localmente, incluindo data de exibição"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Commit e push automático concluído.")
    except Exception as e:
        print("Erro ao enviar para o Git:", e)

# Executa tudo
if __name__ == "__main__":
    if os.path.exists(LOCKFILE):
        print("Já está rodando. Abortando.")
        exit(1)
    try:
        with open(LOCKFILE, 'w') as f: f.write("running")
        eventos = scrape_all()
        save_only(eventos)
        print("Concluído. Eventos:", len(eventos))
        run_git_operations()
    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)