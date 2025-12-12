"""
Normalização e contagem de tags dos eventos.

Responsável por:
- Padronizar tags vindas do site (remover duplicações, símbolos, conectivos)
- Contar a frequência de cada tag normalizada
"""

import re
from collections import Counter


# ---------------------------------------------------------
# Normaliza uma tag:
# - converte para minúsculas
# - separa por espaços, vírgulas, hífens e barras
# - remove palavras vazias e o "e"
# - remove duplicatas
# - ordena e junta novamente
# ---------------------------------------------------------
def normalizar_tag(tag: str) -> str:
    if not tag:
        return ""

    tag = tag.lower().strip()

    # separa por espaço, vírgula, hífen, barra etc.
    palavras = re.split(r"[\s,/-]+", tag)

    # remove vazios e conectivo "e"
    palavras = [p for p in palavras if p and p != "e"]

    # remove duplicatas e ordena
    palavras = sorted(set(palavras))

    return " e ".join(palavras)


# ---------------------------------------------------------
# Conta quantas vezes cada tag normalizada aparece
# ---------------------------------------------------------
def contar_tags(eventos: list) -> Counter:
    normalizadas = []

    for ev in eventos:
        tag = ev.get("tag_evento", "").strip()
        if not tag:
            continue

        normalizadas.append(normalizar_tag(tag))

    return Counter(normalizadas)
