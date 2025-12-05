🎭 MuvRO — Guia Cultural de Rondônia

Aplicativo acadêmico desenvolvido para a disciplina de Programação para Dispositivos Móveis, com o objetivo de centralizar eventos e notícias culturais do estado de Rondônia, oferecendo ao cidadão uma plataforma moderna e acessível.

🌐 O Problema

Eventos culturais são divulgados em portais distintos (Funcultural, Sejucel etc.) e não existe um hub único de acesso.
O MuvRO resolve essa fragmentação coletando automaticamente essas informações e exibindo-as em uma experiência simples e útil.

🚀 Arquitetura do Projeto

A solução segue um modelo de Múltiplas Camadas, apoiado por pipeline automatizado (CI/CD), Docker e atualização contínua de dados.

🔹 1. Backend — Scraper & Data Pipeline

Desenvolvido em Python

Raspagem periódica das fontes culturais

Limpeza de HTML, deduplicação e ordenação por timestamp

Geração de:

eventos.json

eventos_index.json

Commit e push automático do conteúdo atualizado

Infraestrutura e automação

Docker — empacotamento do ambiente de scraping

GitHub Actions — agendamento, execução do scraper, build da imagem

Snyk — análise SaaS de vulnerabilidades em requirements.txt

🔹 2. API Pública

JSON hospedado em GitHub Pages

Serve como uma API REST gratuita, acessível pelo app Android

🔹 3. Aplicativo Android — Frontend

Desenvolvido em Java, seguindo a arquitetura MVVM:

✔️ ViewModel e Repository para isolamento de lógica
✔️ Retrofit para consumo remoto
✔️ Room Database para cache offline-first

UI e UX

CoordinatorLayout + AppBarLayout com recolhimento total da barra superior

RecyclerView com destaques horizontais e lista vertical

Glide para carregamento e cache de imagens

✨ Funcionalidades Principais

✔️ Listagem organizada por data (novo → antigo)
✔️ Cache offline com Room
✔️ Favoritos persistentes — lista pessoal armazenada no dispositivo
✔️ Busca integrada via SearchView no toolbar
✔️ Compartilhamento direto — envia o link original do evento por Intent
✔️ Experiência fluida com recolhimento total do header durante rolagem

🔧 Pipeline e DevOps (Atendendo requisitos da disciplina)

O workflow .github/workflows/scrape_events.yml implementa:

Execução automática da raspagem (schedule e push)

Build da imagem Docker

Execução do container com o scraper

Validação via SaaS (Snyk)

Commit e publicação dos arquivos JSON via Pages

📌 Status do Projeto
Recurso	Status
Scraper Funcultural	✔️
Scraper Sejucel	🚧
JSON/API publicada via Pages	✔️
Retrofit + MVVM + Room	✔️
Ordenação por timestamp	✔️
Busca / SearchView	✔️
Favoritos	✔️
Compartilhamento de eventos	✔️
Tela de detalhes	🚧
📄 Licença

Distribuído sob a MIT License.
Consulte o arquivo LICENSE para mais informações.