"""
Configuração centralizada de logging.

Responsável por:
- Criar logs no terminal (com cores simples)
- Criar logs detalhados em arquivo
- Controlar nível de log (INFO ou DEBUG)
- Padronizar formato e saída
"""

import logging
import os
import sys

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "scraper.log")


class ColorFormatter(logging.Formatter):
    """
    Adiciona cores simples aos logs do terminal.
    """
    COLORS = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m"
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


def configurar_logging(debug=False):
    """
    Configura o sistema de logs.

    Parâmetros:
    - debug (bool): ativa logs detalhados quando True.
    """
    nivel = logging.DEBUG if debug else logging.INFO
    formato = "%(asctime)s | %(levelname)s | %(message)s"

    # Remove handlers antigos para evitar duplicação
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Handler para arquivo (sempre detalhado)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(formato))

    # Handler para terminal (com cores)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(nivel)
    console_handler.setFormatter(ColorFormatter(formato))

    logging.basicConfig(
        level=nivel,
        handlers=[file_handler, console_handler]
    )

    logging.info("✅ Logging inicializado.")
