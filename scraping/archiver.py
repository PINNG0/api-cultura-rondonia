import json
import os
import re
from datetime import datetime, timedelta

class ArquivadorEventos:
    def __init__(self, caminho_principal="docs/api_output/eventos.json", pasta_arquivo="docs/api_output/arquivo"):
        self.caminho_principal = caminho_principal
        self.pasta_arquivo = pasta_arquivo
        self.ano_atual = datetime.now().year

    def extrair_ano(self, data_str):
        agora = datetime.now()

        # Expressões como "há 7 anos", "há 3 meses", "há 10 dias"
        match = re.search(r"há (\d+) (ano|anos|mês|meses|dia|dias)", data_str)
        if match:
            valor = int(match.group(1))
            unidade = match.group(2)

            if "ano" in unidade:
                return agora.year - valor
            elif "mês" in unidade:
                novo_mes = agora.month - valor
                novo_ano = agora.year
                while novo_mes <= 0:
                    novo_mes += 12
                    novo_ano -= 1
                return novo_ano
            elif "dia" in unidade:
                nova_data = agora - timedelta(days=valor)
                return nova_data.year

        # Se não conseguir interpretar, assume ano atual
        return agora.year

    def arquivar(self):
        if not os.path.exists(self.caminho_principal):
            print("⚠️ Arquivo eventos.json não encontrado.")
            return

        with open(self.caminho_principal, "r", encoding="utf-8") as f:
            eventos = json.load(f)

        eventos_atuais = []
        eventos_por_ano = {}

        for ev in eventos:
            ano = self.extrair_ano(ev.get("data_exibicao", ""))
            if not ano:
                continue
            if ano == self.ano_atual:
                eventos_atuais.append(ev)
            else:
                eventos_por_ano.setdefault(ano, []).append(ev)

        os.makedirs(self.pasta_arquivo, exist_ok=True)
        for ano, lista in eventos_por_ano.items():
            caminho_ano = os.path.join(self.pasta_arquivo, f"eventos_de_{ano}.json")
            with open(caminho_ano, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False, indent=2)
            print(f"📁 Arquivado {len(lista)} eventos em eventos_de_{ano}.json")

        with open(self.caminho_principal, "w", encoding="utf-8") as f:
            json.dump(eventos_atuais, f, ensure_ascii=False, indent=2)
        print(f"✅ Mantidos {len(eventos_atuais)} eventos de {self.ano_atual} em eventos.json")
        print("📂 Arquivamento concluído.")
