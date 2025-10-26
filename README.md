# 🏛️ Cultura Rondônia - Agregador de Eventos

Este é um projeto acadêmico para a disciplina de Programação para Dispositivos Móveis. O objetivo é desenvolver um aplicativo Android nativo que sirva como um agregador de eventos culturais e notícias para o estado de Rondônia, com foco inicial em Porto Velho.

O aplicativo resolve o problema da informação fragmentada, onde eventos públicos são divulgados em múltiplos portais (como o da Funcultural e da Sejucel), mas não são centralizados em um único local de fácil acesso para o cidadão.

## 🚀 Arquitetura do Projeto

Este projeto é dividido em duas partes principais:

1.  **Backend (O Robô Scraper):** Um script em Python (`scraper.py`) que visita periodicamente os sites de notícias culturais (Funcultural, Sejucel) e "raspa" os dados (títulos, imagens, descrições).
2.  **API (O JSON):** O robô consolida os dados encontrados em um único arquivo `eventos.json`, que é hospedado no GitHub (via Pages ou Raw) para servir como uma API RESTful gratuita.
3.  **Frontend (O App Android):** O aplicativo nativo (em Java) consome este `eventos.json` usando Retrofit, exibindo os dados em uma interface limpa com destaques e listas.

## 🛠️ Tecnologias Utilizadas

### Backend (Scraper)
* **Python 3**
* **Requests:** Para fazer as requisições HTTP e baixar o HTML.
* **BeautifulSoup4:** Para fazer o *parsing* do HTML e extrair os dados.

### Frontend (Aplicativo Android)
* **Java**
* **Android SDK**
* **Retrofit:** Para o consumo da API (JSON).
* **Glide:** Para carregamento e cache de imagens (os banners dos eventos).
* **RecyclerView:** Para exibir as listas de "Destaques" (horizontal) e "Próximos Eventos" (vertical).
* **CardView:** Para o design dos itens da lista.

## 🏁 Status do Projeto

* [x] **Backend:** Scraper da Funcultural completo.
* [ ] **Backend:** Adicionar scraper da Sejucel.
* [x] **API:** JSON hospedado com sucesso no GitHub.
* [x] **App:** Estrutura base do Android (Retrofit, Adapters, Layouts) implementada.
* [ ] **App:** Teste de integração (API -> App) pendente.
* [ ] **App:** Implementar tela de detalhes do evento.

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
