import os

def gerar_html_arquivos_por_ano(pasta="docs/api_output/arquivo"):
    arquivos = sorted(os.listdir(pasta), reverse=True)
    linhas = ['<h2>Arquivos por ano</h2>', '<ul>']
    for nome in arquivos:
        if nome.startswith("eventos_de_") and nome.endswith(".json"):
            ano = nome.replace("eventos_de_", "").replace(".json", "")
            caminho = f"api_output/arquivo/{nome}"
            linhas.append(f'  <li><a href="{caminho}">Eventos de {ano}</a></li>')
    linhas.append('</ul>')
    return "\n".join(linhas)
