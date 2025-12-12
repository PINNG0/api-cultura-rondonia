"""
Módulo de extração de datas reais a partir de textos.

Responsável por:
- Identificar datas explícitas no formato dd/mm/yyyy
- Identificar datas por extenso (ex: "12 de agosto de 2023")
- Retornar todas as datas encontradas como objetos datetime
- Servir como base para o arquivamento inteligente de eventos
"""

import re
from datetime import datetime

# ---------------------------------------------------------
# Mapeamento de meses por extenso para número
# ---------------------------------------------------------
MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
}

# ---------------------------------------------------------
# Expressões regulares para capturar datas
# ---------------------------------------------------------
REGEX_DDMMYYYY = r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"
REGEX_EXTENSO = r"(\d{1,2}) de ([a-zç]+) de (\d{4})"


# ---------------------------------------------------------
# Extrai todas as datas possíveis de um texto
# ---------------------------------------------------------
def extrair_datas(texto):
    """
    Recebe um texto e retorna uma lista de objetos datetime
    representando todas as datas encontradas.
    """
    datas = []
    texto = texto.lower()

    # 1. Datas no formato dd/mm/yyyy
    for d, m, a in re.findall(REGEX_DDMMYYYY, texto):
        try:
            datas.append(datetime(int(a), int(m), int(d)))
        except ValueError:
            pass  # ignora datas inválidas

    # 2. Datas por extenso (ex: "12 de agosto de 2023")
    for d, mes, a in re.findall(REGEX_EXTENSO, texto):
        if mes in MESES:
            try:
                datas.append(datetime(int(a), MESES[mes], int(d)))
            except ValueError:
                pass

    return datas
