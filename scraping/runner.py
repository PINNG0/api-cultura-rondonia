from time import sleep
from scraping.config import URL_NOTICIAS, EVENTOS_URL_VISTAS
from scraping.fetch import get_soup
from scraping.processor import classify_blocks, preproc_content
from scraping.parser import norm_text, gen_id

def scrape_details(url):
    print(f"🔗 Acessando detalhes: {url}")
    soup = get_soup(url)
    if not soup:
        print("⚠️ Erro ao carregar detalhes.")
        return []
    article = soup.find('article', class_='noticia-conteudo') or \
              soup.find('div', class_='content') or \
              soup.find('div', class_='article-content')
    if not article:
        print("⚠️ Conteúdo principal não encontrado.")
        return []
    imgs = preproc_content(article)
    return classify_blocks(article, imgs)

def process_pair(img_block, txt_block):
    img_tag = img_block.find('img') if img_block else None
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else None

    title_tag = txt_block.find('div', class_='titulo-noticia-pesquisa') if txt_block else None
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    link_tag = txt_block.find('a') if txt_block else None
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = link_rel.strip() if link_rel else None

    if not link or link in EVENTOS_URL_VISTAS:
        return None
    EVENTOS_URL_VISTAS.add(link)

    date_tag = txt_block.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    blocks = scrape_details(link)
    sleep(0.25)
    if not blocks:
        return None

    print(f"✅ Evento coletado: {title}")
    return {
        "titulo": norm_text(title),
        "blocos_conteudo": blocks,
        "imagem_url": banner_rel or "",
        "link_evento": link,
        "fonte": "Funcultural",
        "data_exibicao": data_exibicao
    }

def scrape_all():
    all_events = []
    pagina = 1

    while True:
        print(f"\n🔎 Raspando página {pagina}...")
        url = f"{URL_NOTICIAS}?page={pagina}"
        soup = get_soup(url)

        pagination = soup.find('ul', class_='pagination') if soup else None
        if not soup or (pagination and len(pagination.find_all('li')) <= 1):
            print("🚫 Fim da paginação ou erro ao carregar página.")
            break

        results = soup.find_all('div', class_='resultado-pesquisa')
        if not results:
            print("⚠️ Nenhum resultado encontrado nesta página.")
            break

        i = 0
        while i < len(results):
            img_b = results[i]
            txt_b = results[i+1] if i+1 < len(results) else results[i]
            i += 2 if i+1 < len(results) else 1
            ev = process_pair(img_b, txt_b)
            if ev:
                all_events.append(ev)

        next_page = soup.select_one(f'ul.pagination a[href*="page={pagina + 1}"]')
        if not next_page and pagina >= 3:
            print("📄 Última página alcançada.")
            break
        pagina += 1
        sleep(1)

    # 🔸 Remove duplicatas por hash
    unique = {}
    for ev in all_events:
        h = gen_id(ev)
        if h in unique:
            continue
        ev["id"] = h
        unique[h] = ev

    print(f"\n🎉 Total de eventos únicos coletados: {len(unique)}")
    return list(unique.values())
