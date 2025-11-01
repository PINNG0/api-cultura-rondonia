from scraping.runner import scrape_all
from scraping.storage import save_only, run_git_operations
from scraping.config import LOCKFILE
import os

if __name__ == "__main__":
    if os.path.exists(LOCKFILE):
        print("⚠️ Já está rodando. Abortando.")
        exit(1)

    print("🚀 Iniciando raspagem de eventos...")

    try:
        with open(LOCKFILE, 'w') as f:
            f.write("running")

        eventos = scrape_all()
        print(f"✅ Raspagem concluída. Eventos coletados: {len(eventos)}")

        print("💾 Salvando arquivos...")
        save_only(eventos)

        print("📤 Enviando para o GitHub...")
        run_git_operations()

        print("🎉 Processo finalizado com sucesso!")

    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
    