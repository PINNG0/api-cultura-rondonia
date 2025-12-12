import re
from collections import Counter

def normalizar_tag(tag: str) -> str:
  
    tag = tag.lower().strip()

    # separa por espaço, vírgula, hífen, barra etc.
    palavras = re.split(r'[\s,/-]+', tag)

    # remove palavras vazias e o "e"
    palavras = [p for p in palavras if p and p != "e"]

    # remove duplicadas e ordena
    palavras = sorted(set(palavras))

    # monta a tag final
    return " e ".join(palavras)


def contar_tags(eventos: list) -> Counter:
    normalizadas = []

    for ev in eventos:
        tag = ev.get("tag_evento", "").strip()
        if not tag:
            continue

        tag_norm = normalizar_tag(tag)
        normalizadas.append(tag_norm)

    return Counter(normalizadas)
