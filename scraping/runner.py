"""
Runner principal do scraper da Funcultural.

Responsável por:
- Carregar páginas da listagem de notícias
- Extrair blocos de eventos
- Processar cada evento individualmente
- Coletar conteúdo detalhado da página interna
- Normalizar dados e retornar a lista final de eventos
"""

from time import sleep
from urllib.parse import urljoin
from scraping.config import URL_NOTICIAS
from scraping.fetch import get_soup
from scraping.processor import classify_blocks, preproc_content
from scraping.parser import norm_text
from scraping.tags import contar_tags


# ---------------------------------------------------------
# Coleta o conteúdo detalhado da página interna do evento
# ---------------------------------------------------------
def scrape_details(url):
    soup = get_soup(url)
    if not soup:
        return []

    # O site sempre usa essa estrutura para o conteúdo
    article = soup.find('article', class_='noticia-conteudo')
    if not article:
        return []

    imgs = preproc_content(article)
    return classify_blocks(article, imgs)


# ---------------------------------------------------------
# Processa um único bloco da listagem (um card de evento)
# ---------------------------------------------------------
def process_single_block(bloco):
    # imagem do card
    img_tag = bloco.find('img')
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else ""

    # título
    title_tag = bloco.find('div', class_='titulo-noticia-pesquisa')
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    # tag/categoria
    tag_tag = bloco.find('div', class_='tag-noticia')
    tag_evento = tag_tag.get_text(strip=True) if tag_tag else "Sem tag"

    # link para a página interna
    link_tag = bloco.find('a')
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = urljoin(URL_NOTICIAS, link_rel.strip()) if link_rel else None

    if not link:
        return None

    # data de exibição
    date_tag = bloco.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    # conteúdo detalhado
    blocks = scrape_details(link)
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


# ---------------------------------------------------------
# Carrega uma página da listagem
# ---------------------------------------------------------
def load_page(pagina):
    return get_soup(f"{URL_NOTICIAS}?page={pagina}")


# ---------------------------------------------------------
# Extrai os blocos de eventos da página
# ---------------------------------------------------------
def extract_results(soup):
    return soup.find_all('div', class_='resultado-pesquisa')


# ---------------------------------------------------------
# Verifica se existe próxima página
# ---------------------------------------------------------
def get_next_page(soup, pagina):
    return soup.select_one(f'ul.pagination a[href*="page={pagina + 1}"]')


# ---------------------------------------------------------
# Runner principal — coleta todos os eventos
# ---------------------------------------------------------
def scrape_all():
    all_events = []
    pagina = 1

    while True:
        soup = load_page(pagina)
        if not soup:
            break

        results = extract_results(soup)
        if not results:
            break

        # processa todos os blocos da página
        all_events.extend(
            ev for bloco in results if (ev := process_single_block(bloco))
        )

        # limite de segurança + fim da paginação
        if pagina >= 3 or not get_next_page(soup, pagina):
            break

        pagina += 1
        sleep(0.1)  # mais rápido e suficiente

    # estatísticas de tags
    tags = contar_tags(all_events)

    print("\nTags normalizadas encontradas:")
    for tag, qtd in tags.most_common():
        print(f"{tag}: {qtd}")

    return all_events
