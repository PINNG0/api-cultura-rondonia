🎭 MuvRO — Guia Cultural de Rondônia

O MuvRO é um aplicativo acadêmico desenvolvido para a disciplina de Programação para Dispositivos Móveis, com o objetivo de centralizar eventos e notícias culturais do estado de Rondônia. Ele reúne informações que antes estavam espalhadas em diferentes portais, oferecendo ao cidadão uma plataforma moderna, acessível e sempre atualizada.

🌐 Problema
Os eventos culturais de Rondônia são divulgados separadamente em portais como Funcultural e Sejucel, dificultando o acesso do público.

O MuvRO resolve isso ao:

✔️ Coletar dados automaticamente ✔️ Padronizar e organizar o conteúdo ✔️ Exibir tudo em uma interface intuitiva ✔️ Disponibilizar uma API pública gratuita



🚀 Arquitetura do Projeto
A solução segue um modelo de múltiplas camadas, com automação CI/CD, Docker e atualização contínua dos dados.
    Scraper (Python) → Pipeline CI/CD → JSON API (GitHub Pages) → App Android (MVVM)

🔹 1. Backend — Scraper & Pipeline
✅ Tecnologias e funções
Python — robô coletor

Raspagem periódica dos portais culturais

Limpeza de HTML, deduplicação e ordenação por timestamp

Geração automática dos arquivos JSON:

eventos.json

eventos_index.json

Arquivos por ano (eventos_de_2024.json, etc.)

Commit e push automatizados

✅ Infraestrutura utilizada
Docker — empacotamento do ambiente

GitHub Actions — agendamento e deploy

Snyk — análise de segurança

🔹 2. API Pública — GitHub Pages
A API é publicada automaticamente via GitHub Pages, servindo como uma API REST gratuita.

✅ Funcionalidades da página da API
Layout moderno e responsivo

Dark mode automático

Barra de busca instantânea

Botão copiar link

Botão abrir arquivo

Cards organizados

Animações suaves

Ícones profissionais

Organização por categorias

🔹 3. Aplicativo Android — Frontend
Desenvolvido em Java, seguindo o padrão MVVM.

✅ Componentes principais
ViewModel + Repository

Retrofit — consumo remoto

Room Database — cache e modo offline

CoordinatorLayout + AppBarLayout

RecyclerView (destaques + lista)

Glide — carregamento de imagens

✨ Funcionalidades do Aplicativo
✔️ Lista de eventos ordenada por data ✔️ Cache offline com Room ✔️ Sistema de favoritos ✔️ Busca integrada ✔️ Compartilhamento via Intent ✔️ UI com cabeçalho recolhível ✔️ Consumo da API atualizada automaticamente

🔧 Pipeline e DevOps
O workflow .github/workflows/scrape_events.yml implementa:

Execução automática do scraper

Build Docker

Análise de segurança

Commit e publicação dos JSON

Deploy contínuo da API e da página

📌 Status do Projeto
        Recurso	        |Status
Scraper Funcultural	    | ✔️
Scraper Sejucel	        | 🚧
API / JSON via Pages    | ✔️
Página da API (nova UI) | ✔️
Busca na API            | ✔️
Botão copiar link	    | ✔️
Botão abrir arquivo   	| ✔️
Dark mode	            | ✔️
Retrofit + MVVM + Room	| ✔️
Ordenação por data	    | ✔️
Busca integrada	        | ✔️
Favoritos	            | ✔️
Compartilhamento	    | ✔️
Tela de detalhes	    | ✔️


  🛠️ Como rodar o projeto (Scraper)
✅ Pré-requisitos
Python 3.10+

Docker (opcional)

Git

✅ Rodando localmente
  git clone https://github.com/pinng0/api-cultura-rondonia
    cd api-cultura-rondonia
    pip install -r requirements.txt
    python scraper.py


✅ Rodando com Docker
    docker build -t muv-scraper .
    docker run muv-scraper


🌐 Como consumir a API
A API é pública e pode ser consumida por qualquer aplicação.

✅ Exemplo com Java + Retrofit
    @GET("eventos.json")
    Call<List<Evento>> getEventos();

✅ Exemplo com JavaScript
    fetch("https://pinng0.github.io/api-cultura-rondonia/api_output/eventos.json")
    .then(r => r.json())
    .then(data => console.log(data));



    📡 Endpoints disponíveis
✅ Arquivos principais


         Endpoint                |  	      Descrição
/api_output/eventos.json	       |    Lista completa de eventos
/api_output/eventos_index.json   |       Versão resumida


✅ Arquivos por ano


Ano	  |             Endpoint
2024  |	/api_output/arquivo/eventos_de_2024.json
2023	| /api_output/arquivo/eventos_de_2023.json
2022	| /api_output/arquivo/eventos_de_2022.json
2021	| /api_output/arquivo/eventos_de_2021.json
2020	| /api_output/arquivo/eventos_de_2020.json
2019	| /api_output/arquivo/eventos_de_2019.json
2018	| /api_output/arquivo/eventos_de_2018.json

📄 Licença
Distribuído sob a MIT License. Consulte o arquivo LICENSE para mais informações.
