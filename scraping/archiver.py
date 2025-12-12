"""
Arquivador de eventos da Funcultural.

Responsável por:
- Identificar o ano real de cada evento
- Interpretar datas explícitas e relativas
- Separar eventos por ano
- Arquivar eventos antigos em arquivos individuais
- Manter apenas os eventos do ano atual em eventos.json
"""

import json
import os
import re
import logging
from datetime import datetime, timedelta
from scraping.date_extractor import extrair_datas


class ArquivadorEventos:
    """
    Organiza e arquiva eventos com base nas datas encontradas
    no campo data_exibicao e no conteúdo detalhado.
    """

    def __init__(
        self,
        caminho_principal="docs/api_output/eventos.json",
        pasta_arquivo="docs/api_output/arquivo"
    ):
        self.caminho_principal = caminho_principal
        self.pasta_arquivo = pasta_arquivo
        self.ano_atual = datetime.now().year

    # ---------------------------------------------------------
    # Extrai o ano correto do evento
    # ---------------------------------------------------------
    def extrair_ano(self, data_str, blocos_conteudo=None):
        """
        Determina o ano real do evento usando:
        1. Datas explícitas no campo data_exibicao
        2. Datas explícitas dentro dos blocos de conteúdo
        3. Datas relativas (ex: "há 3 meses")
        4. Fallback: ano atual
        """

        agora = datetime.now()

        # 1. Datas explícitas no campo data_exibicao
        datas = extrair_datas(data_str)
        if datas:
            return datas[0].year

        # 2. Datas explícitas dentro dos blocos de conteúdo
        textos = []

        if blocos_conteudo:
            for bloco in blocos_conteudo:
                if isinstance(bloco, str):
                    textos.append(bloco)
                elif isinstance(bloco, dict):
                    conteudo = bloco.get("conteudo")
                    if isinstance(conteudo, str):
                        textos.append(conteudo)

        if textos:
            texto_completo = " ".join(textos)
            datas = extrair_datas(texto_completo)
            if datas:
                return datas[0].year

        # 3. Datas relativas ("há X meses")
        match = re.search(r"há (\d+) (ano|anos|mês|meses|dia|dias)", data_str)
        if match:
            valor = int(match.group(1))
            unidade = match.group(2)

            if "ano" in unidade:
                return agora.year - valor

            if "mês" in unidade:
                novo_mes = agora.month - valor
                novo_ano = agora.year
                while novo_mes <= 0:
                    novo_mes += 12
                    novo_ano -= 1
                return novo_ano

            if "dia" in unidade:
                nova_data = agora - timedelta(days=valor)
                return nova_data.year

        # 4. Fallback seguro
        return agora.year

    # ---------------------------------------------------------
    # Arquiva eventos antigos e mantém apenas os do ano atual
    # ---------------------------------------------------------
    def arquivar(self):
        logging.info("📦 Iniciando processo de arquivamento...")

        if not os.path.exists(self.caminho_principal):
            logging.warning("⚠️ Arquivo eventos.json não encontrado.")
            return

        with open(self.caminho_principal, "r", encoding="utf-8") as f:
            eventos = json.load(f)

        eventos_atuais = []
        eventos_por_ano = {}

        for ev in eventos:

            # Ignora itens inválidos (ex: números, strings, None)
            if not isinstance(ev, dict):
                logging.warning("⚠️ Evento inválido ignorado: %s", ev)
                continue

            ano = self.extrair_ano(
                ev.get("data_exibicao", ""),
                ev.get("blocos_conteudo", [])
            )

            if ano == self.ano_atual:
                eventos_atuais.append(ev)
            else:
                eventos_por_ano.setdefault(ano, []).append(ev)

        os.makedirs(self.pasta_arquivo, exist_ok=True)

        for ano, lista in eventos_por_ano.items():
            caminho_ano = os.path.join(self.pasta_arquivo, f"eventos_de_{ano}.json")
            with open(caminho_ano, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False, indent=2)
            logging.info("📁 Arquivado %d eventos em eventos_de_%d.json", len(lista), ano)

        with open(self.caminho_principal, "w", encoding="utf-8") as f:
            json.dump(eventos_atuais, f, ensure_ascii=False, indent=2)

        logging.info("✅ Mantidos %d eventos de %d em eventos.json", len(eventos_atuais), self.ano_atual)
        logging.info("📂 Arquivamento concluído.")
