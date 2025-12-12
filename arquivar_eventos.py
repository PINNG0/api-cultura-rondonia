"""
Script auxiliar para arquivar eventos antigos.

Responsável por:
- Executar diretamente o arquivador
- Útil para rodar manualmente ou via cron
"""

from scraping.archiver import ArquivadorEventos

if __name__ == "__main__":
    ArquivadorEventos().arquivar()
