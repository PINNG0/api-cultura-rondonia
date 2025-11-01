import re
import unicodedata
import hashlib

def norm_text(s):
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r'<[^>]*>', '', s)
    s = s.replace('\xa0',' ')
    return re.sub(r'\s+', ' ', s).strip()

def clean_text_simple(html):
    if not html: return ""
    t = re.sub(r'(?s)<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', t).strip()

def gen_id(ev):
    key = (ev.get("titulo","") + "|" + ev.get("link_evento","")).strip()
    return hashlib.sha1(norm_text(key).encode('utf-8')).hexdigest()

def build_block(elem):
    html = elem.decode_contents().strip()
    plain = clean_text_simple(elem.get_text(strip=True))
    if not plain or len(plain.split()) < 5: return None
    is_title = elem.name in ['h2','h3'] or bool(elem.find(['strong','em']))
    return {
        "type": "SUBTITLE" if is_title else "PARAGRAPH",
        "content": html,
        "plain": plain,
        "is_subtitle": is_title
    }
