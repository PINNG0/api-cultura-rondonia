"""
Processor de conteúdo da Funcultural.

Responsável por:
- Limpar o HTML do artigo
- Extrair blocos de texto e imagens
- Detectar padrões especiais (artigos longos, apenas imagens)
- Montar a lista final de blocos estruturados
"""

from bs4 import Tag
from scraping.fetch import complete_url
from scraping.parser import build_block
import re


# ---------------------------------------------------------
# Pré-processa o conteúdo do artigo:
# - remove elementos inúteis
# - extrai imagens destacadas
# ---------------------------------------------------------
def preproc_content(article):
    imgs = []

    # usar list() evita problemas ao remover elementos durante a iteração
    children = list(article.children)

    for child in children:
        if not isinstance(child, Tag):
            continue

        classes = child.get('class', [])

        # imagem destacada
        if 'artigo-img-wrap' in classes:
            img = child.find('img')
            if img and img.get('src'):
                imgs.append(complete_url(img['src']))
            child.decompose()
            continue  # necessário para evitar processar elemento removido

        # parágrafo vazio
        if child.name == 'p' and not child.get_text(strip=True):
            child.decompose()
            continue  # necessário

        # lixo HTML
        if child.name in ['script', 'style', 'noscript']:
            child.decompose()
           

    return imgs


# ---------------------------------------------------------
# Insere imagens entre parágrafos para melhorar leitura
# ---------------------------------------------------------
def interleave_images(blocks, imgs):
    out = []
    img_i = 0
    para_count = 0

    for b in blocks:
        out.append({"type": b["type"], "content": b["content"]})

        # insere imagem a cada 2 parágrafos
        if not b["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imgs):
                out.append({"type": "IMAGE_URL", "content": imgs[img_i]})
                img_i += 1

    # adiciona imagens restantes
    while img_i < len(imgs):
        out.append({"type": "IMAGE_URL", "content": imgs[img_i]})
        img_i += 1

    return out


# ---------------------------------------------------------
# Extrai blocos de texto do artigo (modo rápido)
# ---------------------------------------------------------
def _collect_blocks(article, seen):
    blocks = []

    for e in article.find_all(['p', 'div', 'h2', 'h3'], recursive=False):
        b = build_block(e)
        if not b:
            continue

        # hash simples para evitar duplicação
        h = re.sub(r'[\W_]+', '', b["plain"].lower())[:80]
        if h in seen:
            continue

        seen.add(h)
        blocks.append(b)

    return blocks


# ---------------------------------------------------------
# Fallback mais agressivo (caso o HTML seja irregular)
# ---------------------------------------------------------
def _fallback_collect_blocks(article, seen):
    blocks = []

    for e in article.find_all(['p', 'div', 'h2', 'h3']):
        b = build_block(e)
        if not b:
            continue

        h = re.sub(r'[\W_]+', '', b["plain"].lower())[:80]
        if h in seen:
            continue

        seen.add(h)
        blocks.append(b)

    return blocks


# ---------------------------------------------------------
# Caso especial: artigo só com imagens
# ---------------------------------------------------------
def _handle_only_images_case(blocks, imgs):
    if not blocks and imgs:
        return [{"type": "IMAGE_URL", "content": i} for i in imgs]
    return None


# ---------------------------------------------------------
# Estatísticas de tamanho dos blocos
# ---------------------------------------------------------
def _get_length_stats(blocks):
    if not blocks:
        return None, None, None, None

    lengths = [len(b["plain"]) for b in blocks]
    max_len = max(lengths)
    sorted_l = sorted(lengths, reverse=True)
    second = sorted_l[1] if len(sorted_l) > 1 else 0
    avg = sum(lengths) / len(lengths)

    return lengths, max_len, second, avg


# ---------------------------------------------------------
# Detecta artigos com um bloco muito longo (ex: releases)
# ---------------------------------------------------------
def _is_long_block(max_len, second, avg):
    if max_len is None:
        return False

    # bloco gigante
    if max_len >= 600:
        return True

    # bloco dominante
    if max_len >= 300 and max_len > 1.6 * max(second, avg):
        return True

    return False


# ---------------------------------------------------------
# Constrói resultado para artigos de bloco único
# ---------------------------------------------------------
def _build_single_block_result(blocks, max_len, imgs):
    for b in blocks:
        if len(b["plain"]) == max_len:
            single = [{"type": b["type"], "content": b["content"]}]

            # adiciona imagens se o bloco não contém <img>
            if '<img' not in (b["content"] or "").lower():
                for i in imgs:
                    single.append({"type": "IMAGE_URL", "content": i})

            return single

    return None


# ---------------------------------------------------------
# Detecta e trata artigos de bloco único
# ---------------------------------------------------------
def _detect_single_long_block(blocks, imgs):
    _, max_len, second, avg = _get_length_stats(blocks)

    if not _is_long_block(max_len, second, avg):
        return None

    return _build_single_block_result(blocks, max_len, imgs)


# ---------------------------------------------------------
# Função principal: classifica e organiza os blocos
# ---------------------------------------------------------
def classify_blocks(article, imgs):
    seen = set()

    # coleta rápida
    blocks = _collect_blocks(article, seen)

    # fallback se necessário
    if not blocks:
        blocks = _fallback_collect_blocks(article, seen)

    # caso especial: só imagens
    only_images = _handle_only_images_case(blocks, imgs)
    if only_images:
        return only_images

    # caso especial: artigo de bloco único
    long_block = _detect_single_long_block(blocks, imgs)
    if long_block:
        return long_block

    # caso geral
    return interleave_images(blocks, imgs)
