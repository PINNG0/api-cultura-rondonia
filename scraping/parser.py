"""
Parser de conteúdo da Funcultural.

Responsável por:
- Normalizar textos (remover HTML, espaços, caracteres especiais)
- Extrair texto limpo de elementos HTML
- Construir blocos estruturados (parágrafos e subtítulos)
"""

import re
import unicodedata


# ---------------------------------------------------------
# Normaliza texto:
# - remove HTML
# - normaliza unicode
# - remove múltiplos espaços
# ---------------------------------------------------------
def norm_text(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"<[^>]*>", "", s)      # remove tags HTML
    s = s.replace("\xa0", " ")         # remove NBSP
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------
# Remove HTML e retorna texto simples
# ---------------------------------------------------------
def clean_text_simple(html):
    if not html:
        return ""

    text = re.sub(r"(?s)<[^>]+>", " ", html)  # remove tags
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------
# Constrói um bloco estruturado a partir de um elemento HTML
# ---------------------------------------------------------
def build_block(elem):
    html = elem.decode_contents().strip()
    plain = clean_text_simple(elem.get_text(strip=True))

    # ignora blocos muito curtos (ruído)
    if not plain or len(plain.split()) < 5:
        return None

    # detecta subtítulos
    is_title = (
        elem.name in ["h2", "h3"] or
        bool(elem.find(["strong", "em"]))
    )

    return {
        "type": "SUBTITLE" if is_title else "PARAGRAPH",
        "content": html,
        "plain": plain,
        "is_subtitle": is_title
    }
