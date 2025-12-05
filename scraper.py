from scraping.runner import scrape_all
from scraping.storage import save_only
from scraping.config import LOCKFILE
from scraping.archiver import ArquivadorEventos
from scraping.html_generator import gerar_html_arquivos_por_ano
import os
import json
import hashlib
import subprocess # 💡 Adicionando subprocess para comandos Git

# Arquivos que devem ser adicionados ao Git.
# ATENÇÃO: Ajuste este caminho se seus JSONs estiverem em outro lugar.
FILES_TO_COMMIT = [
    "docs/api_output/eventos.json",
    "docs/api_output/arquivo/*.json",
    "docs/index.html",
    ".cache/hash_eventos.txt"
]

# Função auxiliar para verificar se o ambiente é o GitHub Actions
def rodando_no_github():
    # Retorna True se as variáveis de ambiente do GitHub Actions estiverem presentes
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"

# Função para gerar hash (Mantida, mas não usada no bloco principal)
def gerar_hash_eventos(eventos):
    # Serializa os dados de forma determinística
    payload = json.dumps(eventos, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def commit_and_push(commit_message, files):
    """
    Executa os comandos git add, commit e push.
    """
    try:
        # Adiciona os arquivos à área de stage
        for f in files:
            subprocess.run(["git", "add", f], check=True)
            
        # Verifica se há algo para commitar
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
        
        if result.returncode != 0:
            # Commita e envia
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Commit e Push automáticos concluídos com sucesso!")
            return True
        else:
            print("✔ Nenhum arquivo alterado. Pulando commit.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando Git: {e}")
        return False


if __name__ == "__main__":
    # Verifica se deve ignorar o lockfile (sempre True no CI/CD)
    ignorar_lock = rodando_no_github()

    # Verifica se há um lockfile (evita execuções simultâneas locais)
    if os.path.exists(LOCKFILE) and not ignorar_lock:
        print("⚠️ Já está rodando. Abortando.")
        exit(1)

    print("🚀 Iniciando raspagem de eventos...")

    try:
        # Cria lockfile, ignorando se for o ambiente CI/CD
        if not ignorar_lock:
            with open(LOCKFILE, 'w') as f:
                f.write("running")

        # 1. Executa a raspagem
        eventos = scrape_all()
        print(f"✅ Raspagem concluída. Eventos coletados: {len(eventos)}")

        # --- LÓGICA DE DETECÇÃO DE MUDANÇAS ---
        print("🔎 Verificando mudanças nos dados...")
        novo_hash = gerar_hash_eventos(eventos)
        hash_path = ".cache/hash_eventos.txt"
        os.makedirs(".cache", exist_ok=True)
        
        antigo_hash = None
        if os.path.exists(hash_path):
            with open(hash_path, "r", encoding="utf-8") as f:
                antigo_hash = f.read().strip()

        mudou_eventos = antigo_hash != novo_hash

        # 2. Salva JSONs e Arquiva (Sempre salva para o CI/CD verificar, ou se mudou)
        print("💾 Salvando arquivos...")
        save_only(eventos) 

        print("🧹 Arquivando eventos antigos...")
        ArquivadorEventos().arquivar()
        
        # 3. Atualiza index.html (Define se houve modificação)
        print("🧩 Atualizando index.html...")
        index_path = "docs/index.html"
        index_modificado = False
        
        # --- LÓGICA DE GERAÇÃO HTML ---
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
        # --- FIM LÓGICA GERAÇÃO HTML ---

        # 4. AÇÃO FINAL: Commit Automático APENAS se for execução local
        if mudou_eventos or index_modificado:
            print("📌 Mudanças detectadas. Preparando para commit...")
            
            # Salva o novo hash antes de commitar (se o commit falhar, o hash não é salvo)
            with open(hash_path, "w", encoding="utf-8") as f:
                f.write(novo_hash)
            
            # Se não estiver no GitHub Actions, executa o commit local
            if not ignorar_lock:
                commit_and_push("Dados de eventos atualizados (Execução Local)", FILES_TO_COMMIT)
            else:
                 print("📤 Execução no CI/CD. O Actions fará o commit.")
        
        else:
            print("🟡 Nenhuma mudança detectada. Nenhuma ação de commit necessária.")
            
        print("🎉 Processo finalizado com sucesso!")

    finally:
        # Remove lockfile, se existir
        if os.path.exists(LOCKFILE) and not ignorar_lock:
            os.remove(LOCKFILE)