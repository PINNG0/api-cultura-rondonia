"""
Configurações gerais do scraper da Funcultural.

Contém:
- URLs base utilizadas pelo scraper
- Caminhos de saída para os arquivos JSON gerados
- Nome do lockfile para evitar execuções simultâneas
"""

# ---------------------------------------------------------
# URL base da listagem de notícias
# ---------------------------------------------------------
URL_NOTICIAS = "https://funcultural.portovelho.ro.gov.br/noticias"


# ---------------------------------------------------------
# Diretórios e arquivos de saída da API gerada
# ---------------------------------------------------------
API_DIR = "docs/api_output"

API_LIST_FILE = f"{API_DIR}/eventos.json"   # lista completa de eventos
API_INDEX_FILE = f"{API_DIR}/index.json"    # índice resumido


# ---------------------------------------------------------
# Lockfile para impedir múltiplas execuções simultâneas
# ---------------------------------------------------------
LOCKFILE = "scraper.lock"
