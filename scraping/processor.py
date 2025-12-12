from bs4 import Tag
from scraping.fetch import complete_url
from scraping.parser import build_block
import re


def preproc_content(article):
    imgs = []
    for child in article.children:
        if not isinstance(child, Tag):
            continue

        classes = child.get('class', [])

        if classes and 'artigo-img-wrap' in classes:
            img = child.find('img')
            if img and img.get('src'):
                imgs.append(complete_url(img.get('src')))
            child.decompose()
            continue

        if child.name == 'p' and not child.get_text(strip=True):
            child.decompose()

        if child.name in ['script', 'style', 'noscript']:
            child.decompose()

    return imgs


def interleave_images(blocks, imgs):
    out = []
    img_i = 0
    para_count = 0

    for b in blocks:
        out.append({"type": b["type"], "content": b["content"]})

        if not b["is_subtitle"]:
            para_count += 1
            if para_count % 2 == 0 and img_i < len(imgs):
                out.append({"type": "IMAGE_URL", "content": imgs[img_i]})
                img_i += 1

    while img_i < len(imgs):
        out.append({"type": "IMAGE_URL", "content": imgs[img_i]})
        img_i += 1

    return out


def _collect_blocks(article, seen):
    blocks = []
    for e in article.find_all(['p', 'div', 'h2', 'h3'], recursive=False):
        b = build_block(e)
        if not b:
            continue

        h = re.sub(r'[\W_]+', '', b["plain"].lower())[:80]
        if h in seen:
            continue

        seen.add(h)
        blocks.append(b)

    return blocks


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


def _handle_only_images_case(blocks, imgs):
    if not blocks and imgs:
        return [{"type": "IMAGE_URL", "content": i} for i in imgs]
    return None


# ✅ NOVA VERSÃO — COMPLEXIDADE REDUZIDA
def _get_length_stats(blocks):
    lengths = [len(b["plain"]) for b in blocks]
    if not lengths:
        return None, None, None, None

    max_len = max(lengths)
    sorted_l = sorted(lengths, reverse=True)
    second = sorted_l[1] if len(sorted_l) > 1 else 0
    avg = sum(lengths) / len(lengths)

    return lengths, max_len, second, avg


def _is_long_block(max_len, second, avg):
    if max_len is None:
        return False

    if max_len >= 600:
        return True

    if max_len >= 300 and max_len > 1.6 * max(second, avg):
        return True

    return False


def _build_single_block_result(blocks, max_len, imgs):
    for b in blocks:
        if len(b["plain"]) == max_len:
            single = [{"type": b["type"], "content": b["content"]}]
            if '<img' not in (b["content"] or "").lower():
                for i in imgs:
                    single.append({"type": "IMAGE_URL", "content": i})
            return single
    return None


def _detect_single_long_block(blocks, imgs):
    _, max_len, second, avg = _get_length_stats(blocks)

    if not _is_long_block(max_len, second, avg):
        return None

    return _build_single_block_result(blocks, max_len, imgs)


def classify_blocks(article, imgs):
    seen = set()

    blocks = _collect_blocks(article, seen)

    if not blocks:
        blocks = _fallback_collect_blocks(article, seen)

    only_images = _handle_only_images_case(blocks, imgs)
    if only_images:
        return only_images

    long_block = _detect_single_long_block(blocks, imgs)
    if long_block:
        return long_block

    return interleave_images(blocks, imgs)
