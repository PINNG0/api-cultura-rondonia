import requests
from bs4 import BeautifulSoup, Tag
import json
import time
import re
import os
import unicodedata
import hashlib

# Configurações
API_DIR = "api_output"                 # saída local dos JSON
API_INDEX_FILE = os.path.join(API_DIR, "eventos_index.json")
API_LIST_FILE = os.path.join(API_DIR, "eventos.json")
URL_BASE_FUNCULTURAL = "https://funcultural.portovelho.ro.gov.br"
URL_NOTICIAS_FUNCULTURAL = f"{URL_BASE_FUNCULTURAL}/noticias"
NUMERO_DE_PAGINAS_FUNCULTURAL = 3
EVENTOS_URL_VISTAS = set()             # evita duplicação entre páginas

os.makedirs(API_DIR, exist_ok=True)

# ---------- Normalização e ID ----------
def normalize_text(s):
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'<[^>]*>', '', s)             # remove tags HTML simples
    s = s.replace('\xa0', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def generate_id(ev):
    # Gera id determinístico baseado apenas no título e no link (alinha com dedupe)
    key = (ev.get("titulo", "") + "|" + ev.get("link_evento", "")).strip()
    key_norm = normalize_text(key)
    return hashlib.sha1(key_norm.encode("utf-8")).hexdigest()

# ---------- HTTP / utilitários ----------
def obter_soup(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; scraper/1.0)"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return None

def completar_url(url_relativa, base_url):
    if not url_relativa:
        return None
    url_relativa = url_relativa.strip()
    # já é absoluta
    if url_relativa.startswith('http://') or url_relativa.startswith('https://'):
        return url_relativa.replace('http://', 'https://')
    # relativa absoluta ao host
    if url_relativa.startswith('/'):
        base = base_url.rstrip('/')
        return f"{base}{url_relativa}"
    # caminho relativo sem slash inicial
    base = base_url.rstrip('/')
    return f"{base}/{url_relativa}"

def limpar_texto(texto):
    texto = re.sub(r'(Fotos|Foto|Texto):\s*[^.\n]+', '', texto, flags=re.IGNORECASE)
    texto = texto.replace('\xa0', ' ')
    texto = re.sub(r'\s{2,}', ' ', texto).strip()
    return texto

# ---------- Helpers de parsing (funções pequenas para reduzir complexidade) ----------
def is_tag(element):
    return isinstance(element, Tag)

def extract_image_from_wrapper(element):
    img_tag = element.find('img')
    if img_tag and img_tag.get('src'):
        return completar_url(img_tag.get('src'), URL_BASE_FUNCULTURAL)
    return None

def should_remove_element(element):
    if not is_tag(element):
        return True
    if element.name in ['script', 'style', 'noscript']:
        return True
    if element.name == 'p' and not element.get_text(strip=True):
        return True
    return False

# ---------- Processamento do conteúdo do artigo ----------
def pre_processar_html_conteudo(conteudo):
    """
    Remove wrappers previsíveis, extrai imagens encontradas em wrappers
    e retorna lista de URLs de imagens encontradas no conteúdo.
    Também decompõe (remove) esses wrappers do conteúdo para evitar duplicação.
    """
    lista_imagens_conteudo = []
    for elemento in list(conteudo.children):  # lista para evitar alteração durante iteração
        if not is_tag(elemento):
            continue
        classes = elemento.get('class', [])
        # wrapper de imagem usado em alguns templates
        if classes and 'artigo-img-wrap' in classes:
            url = extract_image_from_wrapper(elemento)
            if url:
                lista_imagens_conteudo.append(url)
            elemento.decompose()
            continue
        if should_remove_element(elemento):
            elemento.decompose()
            continue
    return lista_imagens_conteudo

def build_text_block(element):
    """
    Retorna dicionário com hash, block e flag se é subtitle.
    Ignora blocos muito curtos (menos de ~5 palavras).
    Mantém o conteúdo HTML original (decode_contents) para preservar imagens inline quando for o bloco grande.
    """
    texto_html = element.decode_contents().strip()
    texto_limpo = limpar_texto(element.get_text(strip=True))
    if not texto_limpo or len(texto_limpo.split()) < 5:
        return None
    trecho_hash = re.sub(r'[\W_]+', '', texto_limpo.lower())[:80]
    is_subtitle = element.name in ['h2', 'h3'] or bool(element.find(['strong', 'em']))
    return {
        "hash": trecho_hash,
        "block": {"type": "SUBTITLE" if is_subtitle else "PARAGRAPH", "content": texto_html},
        "plain": texto_limpo,
        "is_subtitle": is_subtitle
    }

def intercalate_images(blocos, imagens):
    """
    Intercala imagens entre parágrafos: insere uma imagem (como bloco PARAGRAPH com tag img)
    a cada dois parágrafos não-subtitle. Mantém a ordem das imagens restantes ao fim.
    """
    result = []
    img_i = 0
    para_count = 0
    for item in blocos:
        result.append(item["block"])
        if not item["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imagens):
                # insere como bloco HTML com tag img para manter compatibilidade com o app que espera HTML
                img_html = f'<img src="{imagens[img_i]}" />'
                result.append({"type": "PARAGRAPH", "content": img_html})
                img_i += 1
    while img_i < len(imagens):
        img_html = f'<img src="{imagens[img_i]}" />'
        result.append({"type": "PARAGRAPH", "content": img_html})
        img_i += 1
    return result

def classificar_blocos_de_texto(conteudo, lista_imagens_conteudo):
    """
    Constrói blocos a partir de <p>, <div>, <h2>, <h3>.
    Se detectar um "bloco grande" (um único elemento que contém praticamente todo o texto),
    retornará somente esse bloco (mantendo imagens inline). Caso contrário, retorna blocos fragmentados
    intercalados com imagens extraídas.
    """
    temp_blocks = []
    seen_hashes = set()
    # busca elementos relevantes na ordem do DOM
    for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3'], recursive=False):
        built = build_text_block(elemento)
        if not built:
            continue
        if built["hash"] in seen_hashes:
            continue
        seen_hashes.add(built["hash"])
        temp_blocks.append(built)

    # Se não encontrou blocos detectáveis por esse critério, tenta varredura profunda como fallback
    if not temp_blocks:
        for elemento in conteudo.find_all(['p', 'div', 'h2', 'h3']):
            built = build_text_block(elemento)
            if not built:
                continue
            if built["hash"] in seen_hashes:
                continue
            seen_hashes.add(built["hash"])
            temp_blocks.append(built)

    # Se ainda vazio, devolve imagens encontradas em wrappers (cada uma como bloco)
    if not temp_blocks and lista_imagens_conteudo:
        result = []
        for img in lista_imagens_conteudo:
            img_html = f'<img src="{img}" />'
            result.append({"type": "PARAGRAPH", "content": img_html})
        return result

    # Determina se existe um bloco que representa o conteúdo "agregado/grande"
    # Critério: bloco com texto limpo muito maior que a média / segundo maior.
    lengths = [len(b["plain"]) for b in temp_blocks]
    if lengths:
        max_len = max(lengths)
        sorted_lengths = sorted(lengths, reverse=True)
        second_len = sorted_lengths[1] if len(sorted_lengths) > 1 else 0
        avg_len = sum(lengths) / len(lengths)
        # LIMIAR: se o maior bloco tem > 600 caracteres ou é > 1.6x o segundo maior e > 300, consideramos agregado
        if max_len >= 600 or (max_len >= 300 and max_len > 1.6 * max(second_len, avg_len)):
            # encontra o bloco que tem max_len e retorna apenas ele (preservando seu HTML que pode conter img)
            for b in temp_blocks:
                if len(b["plain"]) == max_len:
                    # garantir que imagens extraídas ainda sejam adicionadas ao final apenas se não estão inline no bloco
                    bloco_unico = [b["block"]]
                    # verifica se o bloco contém <img>; se não contiver e houver imagens extraídas, adiciona-as depois
                    if '<img' not in (b["block"]["content"] or "").lower():
                        for img in lista_imagens_conteudo:
                            img_html = f'<img src="{img}" />'
                            bloco_unico.append({"type": "PARAGRAPH", "content": img_html})
                    return bloco_unico

    # Caso não seja bloco grande: converte temp_blocks em lista intercalada com imagens
    return intercalate_images(temp_blocks, lista_imagens_conteudo)


# ---------------- PARTE 2 (raspagem de lista e detalhes) ----------------

def raspar_detalhes_funcultural(url_detalhes):
    soup_detalhes = obter_soup(url_detalhes)
    if not soup_detalhes:
        return []
    conteudo = soup_detalhes.find('article', class_='noticia-conteudo')
    if not conteudo:
        # fallback: tentar buscar por .content ou .article-content
        conteudo = soup_detalhes.find('div', class_='content') or soup_detalhes.find('div', class_='article-content')
        if not conteudo:
            return []
    lista_imagens_conteudo = pre_processar_html_conteudo(conteudo)
    blocos_finais = classificar_blocos_de_texto(conteudo, lista_imagens_conteudo)
    return blocos_finais

# ---------- Construção de cada evento (paginação) ----------
def processar_par_blocos_funcultural(bloco_img, bloco_txt):
    img_tag = bloco_img.find('img')
    src_banner_relativo = img_tag['src'] if img_tag and img_tag.get('src') else None
    link_imagem_banner = completar_url(src_banner_relativo, URL_BASE_FUNCULTURAL)

    titulo_tag = bloco_txt.find('div', class_='titulo-noticia-pesquisa')
    titulo_texto = titulo_tag.get_text(strip=True) if titulo_tag else "Título não encontrado"

    link_tag = bloco_txt.find('a')
    link_evento_relativo = link_tag['href'] if link_tag and link_tag.get('href') else None
    link_evento_completo = completar_url(link_evento_relativo, URL_BASE_FUNCULTURAL)

    if not link_evento_completo:
        return None

    # evita duplicação entre páginas por URL
    if link_evento_completo in EVENTOS_URL_VISTAS:
        print(f"Evento já visto, pulando: {titulo_texto}")
        return None
    EVENTOS_URL_VISTAS.add(link_evento_completo)

    print(f"Processando: {titulo_texto}")
    blocos_de_conteudo = raspar_detalhes_funcultural(link_evento_completo)
    time.sleep(0.3)
    if not blocos_de_conteudo:
        return None

    # imagem opcional: se não houver banner válido, aceita None (não impede dedupe)
    return {
        "titulo": normalize_text(titulo_texto),
        "blocos_conteudo": blocos_de_conteudo,
        "imagem_url": link_imagem_banner or "",
        "link_evento": link_evento_completo,
        "fonte": "Funcultural"
    }

def raspar_funcultural():
    print(f"Iniciando raspagem (Páginas 1 a {NUMERO_DE_PAGINAS_FUNCULTURAL})...")
    lista_de_eventos_total = []

    for page_num in range(1, NUMERO_DE_PAGINAS_FUNCULTURAL + 1):
        url_pagina_atual = f"{URL_NOTICIAS_FUNCULTURAL}?page={page_num}"
        print(f" Raspando página: {url_pagina_atual}")
        soup_lista = obter_soup(url_pagina_atual)
        if not soup_lista:
            continue

        blocos_de_dados = soup_lista.find_all('div', class_='resultado-pesquisa')
        eventos_nesta_pagina = 0

        # Emparelhar blocos: percorre em passos de 2 quando a estrutura for par, mas tenta fallback se não estiver
        i = 0
        while i < len(blocos_de_dados):
            bloco_img = blocos_de_dados[i]
            bloco_txt = None
            if i + 1 < len(blocos_de_dados):
                bloco_txt = blocos_de_dados[i + 1]
                i += 2
            else:
                # fallback: tentar extrair link/título do mesmo bloco se não houver par
                bloco_txt = blocos_de_dados[i]
                i += 1

            if not bloco_txt:
                continue

            evento = processar_par_blocos_funcultural(bloco_img, bloco_txt)
            if evento:
                lista_de_eventos_total.append(evento)
                eventos_nesta_pagina += 1

        print(f" Página {page_num}: {eventos_nesta_pagina} eventos processados.")
        if page_num < NUMERO_DE_PAGINAS_FUNCULTURAL:
            time.sleep(1)

    print(f"Total antes de dedupe: {len(lista_de_eventos_total)}")

    # dedupe final e geração de id (chave usada: titulo + link_evento)
    unique_map = {}
    for ev in lista_de_eventos_total:
        chave = (ev.get("titulo", "") + "|" + ev.get("link_evento", "")).strip()
        chave_norm = normalize_text(chave)
        h = hashlib.sha1(chave_norm.encode('utf-8')).hexdigest()
        if h in unique_map:
            print(f" Ignorando duplicado: {ev.get('titulo')}")
            continue
        ev["titulo"] = normalize_text(ev.get("titulo", ""))
        ev["imagem_url"] = ev.get("imagem_url", "")
        ev["link_evento"] = ev.get("link_evento", "")
        ev["blocos_conteudo"] = ev.get("blocos_conteudo", [])
        ev["id"] = generate_id(ev)
        unique_map[h] = ev

    eventos_unicos = list(unique_map.values())
    print(f"Total após dedupe: {len(eventos_unicos)}")

    # salva index leve e arquivos individuais (verifica existência antes de escrever)
    index_list = []
    for ev in eventos_unicos:
        ev_summary = {
            "id": ev["id"],
            "titulo": ev["titulo"],
            "imagem_url": ev.get("imagem_url", ""),
            "link_evento": ev.get("link_evento", ""),
            "fonte": ev.get("fonte", "")
        }
        index_list.append(ev_summary)
        filename = os.path.join(API_DIR, f"{ev['id']}.json")
        try:
            if os.path.exists(filename):
                print(f" Arquivo já existe, pulando: {filename}")
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(ev, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f" Erro ao salvar {filename}: {e}")

    try:
        with open(API_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_list, f, ensure_ascii=False, indent=2)
        print(f" Index salvo: {API_INDEX_FILE} ({len(index_list)} itens).")
    except IOError as e:
        print(f" Erro ao salvar index {API_INDEX_FILE}: {e}")

    try:
        with open(API_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(eventos_unicos, f, ensure_ascii=False, indent=2)
        print(f" Lista completa salva: {API_LIST_FILE}")
    except IOError as e:
        print(f" Erro ao salvar lista completa {API_LIST_FILE}: {e}")

    return eventos_unicos

def main():
    print("Iniciando robô agregador de cultura...")
    # reset EVENTOS_URL_VISTAS ao iniciar run para evitar vazamento entre execuções
    global EVENTOS_URL_VISTAS
    EVENTOS_URL_VISTAS = set()
    eventos_totais = raspar_funcultural()
    print(f"Sucesso! API local criada com {len(eventos_totais)} eventos na pasta '{API_DIR}'.")

if __name__ == "__main__":
    main()
