"""
Script principal do scraper da Funcultural.

Responsável por:
- Executar a raspagem de eventos
- Detectar mudanças nos dados
- Salvar arquivos JSON e atualizar index.html
- Arquivar eventos antigos
- Realizar commit automático (se necessário)
"""

import os
import json
import hashlib
import subprocess
import atexit
import logging

from scraping.runner import scrape_all
from scraping.storage import save_only
from scraping.config import LOCKFILE
from scraping.archiver import ArquivadorEventos
from scraping.html_generator import gerar_html_arquivos_por_ano
from scraping.logging_config import configurar_logging


# ---------------------------------------------------------
# Arquivos que devem ser adicionados ao Git
# ---------------------------------------------------------
FILES_TO_COMMIT = [
    "docs/api_output/eventos.json",
    "docs/api_output/arquivo/*.json",
    "docs/index.html",
    ".cache/hash_eventos.txt",
]


# ---------------------------------------------------------
# Verifica se está rodando no ambiente GitHub Actions
# ---------------------------------------------------------
def rodando_no_github():
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


# ---------------------------------------------------------
# Gera hash determinístico dos eventos
# ---------------------------------------------------------
def gerar_hash_eventos(eventos):
    payload = json.dumps(eventos, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------
# Executa git add, commit e push
# ---------------------------------------------------------
def commit_and_push(commit_message, files):
    try:
        for f in files:
            subprocess.run(["git", "add", f], check=True)

        result = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)

        if result.returncode != 0:
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push"], check=True)
            logging.info("✅ Commit e push automáticos concluídos com sucesso.")
            return True
        else:
            logging.info("✔ Nenhum arquivo alterado. Pulando commit.")
            return False

    except subprocess.CalledProcessError as e:
        logging.error("❌ Erro ao executar comando Git: %s", e)
        return False


# ---------------------------------------------------------
# Remove o lock automaticamente ao sair (mesmo em erro ou CTRL+C)
# ---------------------------------------------------------
def remove_lock():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)


atexit.register(remove_lock)


# ---------------------------------------------------------
# Execução principal
# ---------------------------------------------------------
if __name__ == "__main__":
    configurar_logging()
    ignorar_lock = rodando_no_github()

    # Lockfile só é respeitado em ambiente local
    if os.path.exists(LOCKFILE) and not ignorar_lock:
        logging.warning("⚠️ Já está rodando. Abortando.")
        exit(1)

    if not ignorar_lock:
        with open(LOCKFILE, "w", encoding="utf-8") as f:
            f.write("running")

    logging.info("🚀 Iniciando raspagem de eventos...")

    try:
        # 1. Raspagem
        eventos = scrape_all()
        logging.info("✅ Raspagem concluída. Eventos coletados: %d", len(eventos))

        # 2. Verificação de mudanças
        logging.info("🔎 Verificando mudanças nos dados...")
        novo_hash = gerar_hash_eventos(eventos)
        hash_path = ".cache/hash_eventos.txt"
        os.makedirs(".cache", exist_ok=True)

        antigo_hash = None
        if os.path.exists(hash_path):
            with open(hash_path, "r", encoding="utf-8") as f:
                antigo_hash = f.read().strip()

        mudou_eventos = antigo_hash != novo_hash

        # 3. Salvamento e arquivamento
        logging.info("💾 Salvando arquivos de eventos...")
        save_only(eventos)

        logging.info("🧹 Arquivando eventos antigos...")
        ArquivadorEventos().arquivar()

        # 4. Atualização do index.html
        logging.info("🧩 Atualizando index.html...")
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
                    logging.info("✅ index.html atualizado!")
                else:
                    logging.info("✔ index.html sem mudanças.")
            else:
                logging.warning("⚠️ Marcador <!-- anos --> não encontrado no index.html.")
        else:
            logging.warning("⚠️ index.html não encontrado.")

        # 5. Commit automático (somente local)
        if mudou_eventos or index_modificado:
            logging.info("📌 Mudanças detectadas. Preparando para commit...")

            with open(hash_path, "w", encoding="utf-8") as f:
                f.write(novo_hash)

            if not ignorar_lock:
                commit_and_push("Dados de eventos atualizados (Execução Local)", FILES_TO_COMMIT)
            else:
                logging.info("📤 Execução no CI/CD. O Actions fará o commit.")
        else:
            logging.info("🟡 Nenhuma mudança detectada. Nenhuma ação de commit necessária.")

        logging.info("🎉 Processo finalizado com sucesso.")

    finally:
        # O remove_lock já está registrado no atexit, então aqui é só reforço
        if os.path.exists(LOCKFILE) and not ignorar_lock:
            os.remove(LOCKFILE)
