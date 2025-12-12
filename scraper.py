"""
Script principal do projeto Funcultural Scraper.

Responsável por:
- Oferecer uma interface de linha de comando (CLI)
- Executar a raspagem de eventos
- Arquivar eventos antigos
- Gerar o HTML final
- Controlar o nível de logs (modo normal e modo debug)
"""

import argparse
import logging
import json
import os

from scraping.runner import scrape_all
from scraping.archiver import ArquivadorEventos
from scraping.html_generator import gerar_html
from scraping.logging_config import configurar_logging


# ---------------------------------------------------------
# Salva eventos no arquivo principal
# ---------------------------------------------------------
def salvar_eventos(eventos, caminho="docs/api_output/eventos.json"):
    """
    Salva a lista de eventos no arquivo JSON principal.
    """
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)

    logging.info("✅ %d eventos salvos em %s", len(eventos), caminho)


# ---------------------------------------------------------
# Comando: raspagem de eventos
# ---------------------------------------------------------
def comando_atualizar():
    """
    Executa a raspagem de eventos e atualiza o arquivo eventos.json.
    """
    logging.info("🚀 Iniciando raspagem de eventos...")
    eventos = scrape_all()
    salvar_eventos(eventos)
    logging.info("✅ Raspagem concluída.")


# ---------------------------------------------------------
# Comando: arquivar eventos antigos
# ---------------------------------------------------------
def comando_arquivar():
    """
    Executa o processo de arquivamento de eventos antigos.
    """
    logging.info("📦 Arquivando eventos antigos...")
    ArquivadorEventos().arquivar()
    logging.info("✅ Arquivamento concluído.")


# ---------------------------------------------------------
# Comando: gerar HTML final
# ---------------------------------------------------------
def comando_gerar_html():
    """
    Gera o HTML final a partir do arquivo eventos.json.
    """
    logging.info("🖥️ Gerando HTML final...")

    caminho = "docs/api_output/eventos.json"
    if not os.path.exists(caminho):
        logging.error("❌ eventos.json não encontrado. Rode --atualizar primeiro.")
        return

    with open(caminho, "r", encoding="utf-8") as f:
        eventos = json.load(f)

    gerar_html(eventos)
    logging.info("✅ HTML gerado com sucesso.")


# ---------------------------------------------------------
# Comando: executar tudo em sequência
# ---------------------------------------------------------
def comando_tudo():
    """
    Executa raspagem, arquivamento e geração de HTML em sequência.
    """
    comando_atualizar()
    comando_arquivar()
    comando_gerar_html()


# ---------------------------------------------------------
# Função principal da CLI
# ---------------------------------------------------------
def main():
    """
    Interpreta os argumentos da linha de comando e
    executa o comando solicitado pelo usuário.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Ferramenta CLI para o scraper da Funcultural.\n\n"
            "Como usar:\n"
            "  python scraper.py --atualizar\n"
            "  python scraper.py --arquivar\n"
            "  python scraper.py --gerar-html\n"
            "  python scraper.py --tudo\n"
            "  python scraper.py --tudo --debug\n\n"
            "Observação:\n"
            "  No Windows, sempre execute usando 'python scraper.py ...'.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Executa o scraping e atualiza eventos.json"
    )
    parser.add_argument(
        "--arquivar",
        action="store_true",
        help="Arquiva eventos antigos"
    )
    parser.add_argument(
        "--gerar-html",
        action="store_true",
        help="Gera o HTML final"
    )
    parser.add_argument(
        "--tudo",
        action="store_true",
        help="Executa scraping + arquivamento + HTML"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativa modo debug (logs detalhados)"
    )

    args = parser.parse_args()

    # Ativa modo debug via flag ou variável de ambiente
    modo_debug = args.debug or os.getenv("DEBUG") == "1"
    configurar_logging(debug=modo_debug)

    if modo_debug:
        logging.debug("Modo debug ativado.")

    # Executa o comando solicitado
    if args.atualizar:
        comando_atualizar()
    elif args.arquivar:
        comando_arquivar()
    elif args.gerar_html:
        comando_gerar_html()
    elif args.tudo:
        comando_tudo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
