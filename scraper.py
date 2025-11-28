from scraping.runner import scrape_all
from scraping.storage import save_only
from scraping.config import LOCKFILE
from scraping.archiver import ArquivadorEventos
from scraping.html_generator import gerar_html_arquivos_por_ano
import os
import json
import hashlib

def rodando_no_github():
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"

def gerar_hash_eventos(eventos):
    """
    Gera um hash único considerando TODOS os campos relevantes do evento.
    Agora o hash é 100% determinístico mesmo em ordem diferente.
    """
    # serializa tudo com chaves ordenadas
    payload = json.dumps(eventos, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

if __name__ == "__main__":
    ignorar_lock = rodando_no_github()

    if os.path.exists(LOCKFILE) and not ignorar_lock:
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

        print("🧩 Atualizando index.html...")
        index_path = "docs/index.html"
        index_modificado = False

        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                conteudo = f.read()

            html_anos = gerar_html_arquivos_por_ano()
            if "<!-- anos -->" in conteudo:
                novo_conteudo = conteudo.split("<!-- anos -->")[0] + "<!-- anos -->\n" + html_anos
                if novo_conteudo != conteudo:
                    index_modificado = True
                    with open(index_path, "w", encoding="utf-8") as f:
                        f.write(novo_conteudo)
                    print("✅ index.html atualizado!")
                else:
                    print("✔ index.html sem mudanças.")
            else:
                print("⚠️ Marcador <!-- anos --> não encontrado no index.html.")
        else:
            print("⚠️ index.html não encontrado.")

        # ----- DETECÇÃO DE MUDANÇAS -----
        print("🔎 Verificando mudanças nos dados...")

        novo_hash = gerar_hash_eventos(eventos)
        hash_path = ".cache/hash_eventos.txt"
        os.makedirs(".cache", exist_ok=True)

        antigo_hash = None
        if os.path.exists(hash_path):
            with open(hash_path, "r", encoding="utf-8") as f:
                antigo_hash = f.read().strip()

        mudou_eventos = antigo_hash != novo_hash

        if mudou_eventos:
            print("📌 Dados dos eventos mudaram.")
        else:
            print("✔ Eventos iguais ao último hash salvo.")

        # Salva o novo hash (IMPORTANTE: sempre salvar após a execução)
        with open(hash_path, "w", encoding="utf-8") as f:
            f.write(novo_hash)

        # LOG FINAL
        if mudou_eventos or index_modificado:
            print("📤 Mudanças detectadas. O GitHub Actions irá comitar.")
        else:
            print("🟡 Nenhuma mudança detectada. O GitHub Actions não enviará commit.")

        print("🎉 Processo finalizado com sucesso!")

    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
