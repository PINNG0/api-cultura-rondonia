from time import sleep
from scraping.config import URL_NOTICIAS, EVENTOS_URL_VISTAS
from scraping.fetch import get_soup
from scraping.processor import classify_blocks, preproc_content
from scraping.parser import norm_text, gen_id

def scrape_details(url):
    soup = get_soup(url)
    if not soup:
        return []
    article = soup.find('article', class_='noticia-conteudo') or \
              soup.find('div', class_='content') or \
              soup.find('div', class_='article-content')
    if not article:
        return []
    imgs = preproc_content(article)
    return classify_blocks(article, imgs)

def process_single_block(bloco):
    # Extrai imagem
    img_tag = bloco.find('img')
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else ""

    # Extrai título
    title_tag = bloco.find('div', class_='titulo-noticia-pesquisa')
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    # Extrai link
    link_tag = bloco.find('a')
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = link_rel.strip() if link_rel else None

    if not link or link in EVENTOS_URL_VISTAS:
        return None
    EVENTOS_URL_VISTAS.add(link)

    # Extrai data
    date_tag = bloco.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    # Raspagem do conteúdo detalhado
    blocks = scrape_details(link)
    sleep(0.25)
    if not blocks:
        return None

    return {
        "titulo": norm_text(title),
        "blocos_conteudo": blocks,
        "imagem_url": banner_rel,
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
        print(f"🔍 Blocos encontrados: {len(results)}")
        if not results:
            print("⚠️ Nenhum resultado encontrado nesta página.")
            break

        eventos_pagina = []
        for bloco in results:
            ev = process_single_block(bloco)
            if ev:
                eventos_pagina.append(ev)

        print(f"✅ Página {pagina} concluída. Eventos coletados: {len(eventos_pagina)}")
        all_events.extend(eventos_pagina)

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
