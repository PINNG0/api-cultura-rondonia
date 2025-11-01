from scraping.runner import scrape_all
from scraping.storage import save_only, run_git_operations
from scraping.config import LOCKFILE
from scraping.archiver import ArquivadorEventos
from scraping.html_generator import gerar_html_arquivos_por_ano
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

        print("🧹 Arquivando eventos antigos...")
        ArquivadorEventos().arquivar()

        print("🧩 Atualizando index.html com os anos disponíveis...")
        index_path = "docs/index.html"
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                conteudo = f.read()

            html_anos = gerar_html_arquivos_por_ano()
            if "<!-- anos -->" in conteudo:
                novo_conteudo = conteudo.replace("<!-- anos -->", f"<!-- anos -->\n{html_anos}")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(novo_conteudo)
                print("✅ HTML atualizado com os anos disponíveis.")
            else:
                print("⚠️ Marcador <!-- anos --> não encontrado no index.html.")

        print("📤 Enviando para o GitHub...")
        run_git_operations()

        print("🎉 Processo finalizado com sucesso!")

    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
