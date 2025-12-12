from time import sleep
from urllib.parse import urljoin
from scraping.config import URL_NOTICIAS, EVENTOS_URL_VISTAS
from scraping.fetch import get_soup
from scraping.processor import classify_blocks, preproc_content
from scraping.parser import norm_text, gen_id
from scraping.tags import contar_tags


def scrape_details(url):
    soup = get_soup(url)
    if not soup:
        return []

    article = (
        soup.find('article', class_='noticia-conteudo')
        or soup.find('div', class_='content')
        or soup.find('div', class_='article-content')
    )

    if not article:
        return []

    imgs = preproc_content(article)
    return classify_blocks(article, imgs)


def process_single_block(bloco):
    # extrai imagem
    img_tag = bloco.find('img')
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else ""

    # extrai título
    title_tag = bloco.find('div', class_='titulo-noticia-pesquisa')
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    # extrai tag
    tag_tag = bloco.find('div', class_='tag-noticia')
    tag_evento = tag_tag.get_text(strip=True) if tag_tag else "Sem tag"

    # extrai link
    link_tag = bloco.find('a')
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = urljoin(URL_NOTICIAS, link_rel.strip()) if link_rel else None

    if not link or link in EVENTOS_URL_VISTAS:
        return None

    EVENTOS_URL_VISTAS.add(link)

    # extrai data
    date_tag = bloco.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    # coleta conteúdo detalhado
    blocks = scrape_details(link)
    sleep(0.25)

    if not blocks:
        return None

    return {
        "titulo": norm_text(title),
        "tag_evento": norm_text(tag_evento),
        "blocos_conteudo": blocks,
        "imagem_url": banner_rel,
        "link_evento": link,
        "fonte": "Funcultural",
        "data_exibicao": data_exibicao
    }


def load_page(pagina):
    # baixa página da listagem
    url = f"{URL_NOTICIAS}?page={pagina}"
    return get_soup(url)


def extract_results(soup):
    # pega blocos de eventos
    return soup.find_all('div', class_='resultado-pesquisa')


def should_stop_pagination(soup):
    # verifica fim da paginação
    if not soup:
        return True
    pagination = soup.find('ul', class_='pagination')
    return pagination and len(pagination.find_all('li')) <= 1


def get_next_page(soup, pagina):
    # verifica se existe próxima página
    return soup.select_one(f'ul.pagination a[href*="page={pagina + 1}"]')


def dedupe_events(all_events):
    # remove duplicados por hash
    unique = {}
    for ev in all_events:
        h = gen_id(ev)
        if h not in unique:
            ev["id"] = h
            unique[h] = ev
    return list(unique.values())


def scrape_all():
    all_events = []
    pagina = 1

    while True:
        soup = load_page(pagina)

        if should_stop_pagination(soup):
            break

        results = extract_results(soup)
        if not results:
            break

        eventos_pagina = [
            ev for bloco in results if (ev := process_single_block(bloco))
        ]

        all_events.extend(eventos_pagina)

        if not get_next_page(soup, pagina) and pagina >= 3:
            break

        pagina += 1
        sleep(1)

    eventos_unicos = dedupe_events(all_events)

    # gera estatísticas de tags
    tags = contar_tags(eventos_unicos)

    print("\nTags normalizadas encontradas:")
    for tag, qtd in tags.most_common():
        print(f"{tag}: {qtd}")

    return eventos_unicos
