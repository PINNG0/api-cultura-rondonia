🎭 MuvRO — Guia Cultural de Rondônia

Aplicativo acadêmico desenvolvido para a disciplina de Programação para Dispositivos Móveis, com o objetivo de centralizar eventos e notícias culturais do estado de Rondônia, oferecendo ao cidadão uma plataforma moderna e acessível.

🌐 Problema

Eventos culturais são divulgados separadamente em portais como Funcultural e Sejucel, dificultando o acesso do público.

O MuvRO resolve isso ao:

✔️ Coletar dados automaticamente
✔️ Organizar conteúdo
✔️ Exibir tudo em uma experiência intuitiva

🚀 Arquitetura do Projeto

A solução segue um modelo de múltiplas camadas, apoiado por automação CI/CD, Docker e atualização contínua de dados.

🔹 1. Backend — Scraper & Pipeline

Tecnologias e funções:

Python — desenvolvimento do robô coletor

Raspagem periódica de portais culturais

Limpeza de HTML, deduplicação e ordenação por timestamp

Geração automática de arquivos:

eventos.json

eventos_index.json

Commit e push automatizado para o repositório

Infraestrutura utilizada:

Docker — empacotamento do ambiente de scraping

GitHub Actions — agendamento, execução e deploy dos dados

Snyk — inspeção de pacotes Python (SaaS security)

🔹 2. API Pública

JSON publicado via GitHub Pages

Serve como API REST gratuita, consumida pelo app

🔹 3. Aplicativo Android — Frontend

Desenvolvido em Java

Utiliza MVVM para separação de responsabilidades

Componentes principais:

✔️ ViewModel + Repository
✔️ Retrofit — consumo remoto
✔️ Room Database — cache e modo offline
✔️ CoordinatorLayout + AppBarLayout
✔️ RecyclerView (destaques horizontais + lista vertical)
✔️ Glide — imagem e cache

✨ Funcionalidades do Aplicativo

✔️ Lista de eventos ordenada por data
✔️ Cache offline com Room
✔️ Sistema de favoritos
✔️ Busca integrada via SearchView
✔️ Compartilhamento direto via Intent
✔️ UI com recolhimento dinâmico do cabeçalho

🔧 Pipeline e DevOps

O workflow (.github/workflows/scrape_events.yml) implementa:

Execução automática do scraper

Build e execução da imagem Docker

Análise de segurança SaaS

Commit e publicação dos arquivos JSON via Pages

📌 Status do Projeto
Recurso	Status
Scraper Funcultural	✔️
Scraper Sejucel	🚧
API / JSON via Pages	✔️
Retrofit + MVVM + Room	✔️
Ordenação por data	✔️
Busca integrada	✔️
Favoritos	✔️
Compartilhamento	✔️
Tela de detalhes	🚧
📄 Licença

Distribuído sob a MIT License.
Consulte o arquivo LICENSE para mais informações.
