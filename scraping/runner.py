"""
Runner principal do scraper da Funcultural.

Responsável por:
- Carregar páginas da listagem de notícias
- Extrair blocos de eventos
- Processar cada evento individualmente
- Coletar conteúdo detalhado da página interna
- Normalizar dados e retornar a lista final de eventos
"""

import logging
from time import sleep
from urllib.parse import urljoin

from scraping.config import URL_NOTICIAS
from scraping.fetch import get_soup
from scraping.processor import classify_blocks, preproc_content
from scraping.parser import norm_text


# ---------------------------------------------------------
# Coleta o conteúdo detalhado da página interna do evento
# ---------------------------------------------------------
def scrape_details(url):
    """
    Acessa a página interna do evento e extrai:
    - texto detalhado
    - imagens internas
    - blocos de conteúdo normalizados
    """
    logging.debug("🔍 Coletando detalhes do evento: %s", url)

    soup = get_soup(url)
    if not soup:
        logging.warning("⚠️ Falha ao carregar página interna: %s", url)
        return []

    article = soup.find('article', class_='noticia-conteudo')
    if not article:
        logging.warning("⚠️ Estrutura inesperada: artigo não encontrado em %s", url)
        return []

    # Pré-processa imagens internas
    imgs = preproc_content(article)

    # Classifica e organiza blocos de conteúdo
    return classify_blocks(article, imgs)


# ---------------------------------------------------------
# Processa um único bloco da listagem (um card de evento)
# ---------------------------------------------------------
def process_single_block(bloco):
    """
    Extrai informações básicas do card:
    - título
    - tag/categoria
    - imagem
    - link para página interna
    - data exibida
    E coleta o conteúdo detalhado da página interna.
    """
    img_tag = bloco.find('img')
    banner_rel = img_tag['src'] if img_tag and img_tag.get('src') else ""

    title_tag = bloco.find('div', class_='titulo-noticia-pesquisa')
    title = title_tag.get_text(strip=True) if title_tag else "Título não encontrado"

    tag_tag = bloco.find('div', class_='tag-noticia')
    tag_evento = tag_tag.get_text(strip=True) if tag_tag else "Sem tag"

    link_tag = bloco.find('a')
    link_rel = link_tag['href'] if link_tag and link_tag.get('href') else None
    link = urljoin(URL_NOTICIAS, link_rel.strip()) if link_rel else None

    if not link:
        logging.warning("⚠️ Card ignorado: link inválido.")
        return None

    date_tag = bloco.find('div', class_='datanot')
    data_exibicao = date_tag.get_text(strip=True) if date_tag else "Sem data"

    # Coleta conteúdo detalhado
    blocks = scrape_details(link)
    if not blocks:
        logging.warning("⚠️ Conteúdo detalhado vazio. Ignorando evento: %s", link)
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
    """
    Carrega uma página da listagem de notícias.
    """
    url = f"{URL_NOTICIAS}?page={pagina}"
    logging.info("📄 Carregando página %s", url)
    return get_soup(url)


# ---------------------------------------------------------
# Extrai os blocos de eventos da página
# ---------------------------------------------------------
def extract_results(soup):
    """
    Retorna todos os cards de eventos encontrados na página.
    """
    return soup.find_all('div', class_='resultado-pesquisa')


# ---------------------------------------------------------
# Verifica se existe próxima página
# ---------------------------------------------------------
def get_next_page(soup, pagina):
    """
    Verifica se existe link para a próxima página.
    """
    return soup.select_one(f'ul.pagination a[href*="page={pagina + 1}"]')


# ---------------------------------------------------------
# Runner principal — coleta todos os eventos
# ---------------------------------------------------------
def scrape_all():
    """
    Percorre todas as páginas da listagem e retorna
    uma lista completa de eventos normalizados.
    """
    logging.info("🚀 Iniciando coleta de eventos da Funcultural...")

    all_events = []
    pagina = 1

    while True:
        soup = load_page(pagina)
        if not soup:
            logging.warning("⚠️ Falha ao carregar página %d. Encerrando.", pagina)
            break

        results = extract_results(soup)
        if not results:
            logging.info("✅ Nenhum resultado encontrado na página %d. Encerrando.", pagina)
            break

        # Processa cada card da página
        for bloco in results:
            ev = process_single_block(bloco)
            if ev:
                all_events.append(ev)

        # Verifica se existe próxima página
        if not get_next_page(soup, pagina):
            logging.info("📌 Última página alcançada (%d).", pagina)
            break

        pagina += 1
        sleep(0.1)  # evita sobrecarregar o servidor

    logging.info("✅ Coleta concluída. Total de eventos coletados: %d", len(all_events))
    return all_events
