from scraping.runner import scrape_all
from scraping.storage import save_only, run_git_operations
from scraping.config import LOCKFILE
import os

if __name__ == "__main__":
    if os.path.exists(LOCKFILE):
        print("Já está rodando. Abortando.")
        exit(1)
    try:
        with open(LOCKFILE, 'w') as f:
            f.write("running")

        eventos = scrape_all()
        save_only(eventos)
        print("Concluído. Eventos:", len(eventos))

        run_git_operations()

    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
