from scraping.runner import scrape_all
from scraping.storage import save_only, run_git_operations
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
    Gera um hash único considerando os campos principais dos eventos,
    incluindo a data de exibição.
    """
    normalizados = []
    for e in eventos:
        normalizados.append({
            "id": e.get("id"),
            "titulo": e.get("titulo"),
            "fonte": e.get("fonte"),
            "link_evento": e.get("link_evento"),
            "imagem_url": e.get("imagem_url"),
            "data_exibicao": e.get("data_exibicao"),
        })
    payload = json.dumps(normalizados, ensure_ascii=False, sort_keys=True)
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

        print("🧩 Atualizando index.html com os anos disponíveis...")
        index_path = "docs/index.html"
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                conteudo = f.read()

            html_anos = gerar_html_arquivos_por_ano()
            if "<!-- anos -->" in conteudo:
                # Remove tudo após o marcador e insere os links atualizados
                novo_conteudo = conteudo.split("<!-- anos -->")[0] + "<!-- anos -->\n" + html_anos
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(novo_conteudo)
                print("✅ HTML atualizado com os anos disponíveis.")
            else:
                print("⚠️ Marcador <!-- anos --> não encontrado no index.html.")

        # 🔎 Verifica se houve mudança (incluindo data_exibicao)
        print("🔎 Verificando mudanças...")
        novo_hash = gerar_hash_eventos(eventos)
        hash_path = ".cache/hash_eventos.txt"
        os.makedirs(".cache", exist_ok=True)

        antigo_hash = None
        if os.path.exists(hash_path):
            with open(hash_path, "r", encoding="utf-8") as f:
                antigo_hash = f.read().strip()

        if antigo_hash != novo_hash:
            print("📤 Mudança detectada. Enviando para o GitHub...")
            run_git_operations()
            with open(hash_path, "w", encoding="utf-8") as f:
                f.write(novo_hash)
        else:
            print("🟡 Nenhuma mudança detectada. Push ignorado.")

        print("🎉 Processo finalizado com sucesso!")

    finally:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
