"""
Gerador de HTML para exibição dos eventos coletados.

Responsável por:
- Criar HTML limpo usando arquivos externos (CSS/JS)
- Agrupar eventos por mês
- Gerar cards organizados
- Inserir o conteúdo no template base
"""

import os
from datetime import datetime


# ---------------------------------------------------------
# Função principal: gera o HTML final
# ---------------------------------------------------------
def gerar_html(eventos, caminho="docs/index.html"):
    """
    Recebe a lista de eventos e gera o HTML final,
    substituindo {{EVENTOS_HTML}} no template base.
    """

    # Agrupa eventos por mês
    grupos = {}
    for ev in eventos:
        data = ev.get("data_exibicao", "")
        mes_ano = extrair_mes_ano(data)
        grupos.setdefault(mes_ano, []).append(ev)

    # Ordena meses (mais recente primeiro)
    grupos_ordenados = dict(sorted(
        grupos.items(),
        key=lambda x: ordenar_mes_ano(x[0]),
        reverse=True
    ))

    # Gera os cards HTML
    eventos_html = gerar_cards(grupos_ordenados)

    # Carrega o template base
    template = carregar_template_base()

    # Substitui o placeholder pelo conteúdo real
    html_final = template.replace("{{EVENTOS_HTML}}", eventos_html)

    # Garante que a pasta existe
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    # Salva o HTML final
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html_final)


# ---------------------------------------------------------
# Carrega o template base (index.html)
# ---------------------------------------------------------
def carregar_template_base():
    caminho = "docs/index.html"
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------
# Gera os cards HTML agrupados por mês
# ---------------------------------------------------------
def gerar_cards(grupos):
    html = ""

    for mes, eventos in grupos.items():
        html += f'<div class="month-title">{mes}</div>\n'

        for ev in eventos:
            html += f"""
<div class="event-card">
    <img src="{ev.get('imagem_url', '')}" alt="Imagem do evento">
    <div class="event-title">{ev.get('titulo')}</div>
    <div class="event-tag">{ev.get('tag_evento')}</div>
    <div class="event-content">
        <a href="{ev.get('link_evento')}" target="_blank">Ver detalhes</a>
    </div>
</div>
"""

    return html


# ---------------------------------------------------------
# Extrai "Janeiro 2025" a partir de "12/01/2025"
# ---------------------------------------------------------
def extrair_mes_ano(data_str):
    try:
        d, m, a = data_str.split("/")
        dt = datetime(int(a), int(m), int(d))
        return dt.strftime("%B %Y").title()
    except Exception:
        return "Outros"


# ---------------------------------------------------------
# Converte "Janeiro 2025" em número para ordenar
# ---------------------------------------------------------
def ordenar_mes_ano(mes_ano):
    try:
        return datetime.strptime(mes_ano, "%B %Y")
    except Exception:
        return datetime(1900, 1, 1)
