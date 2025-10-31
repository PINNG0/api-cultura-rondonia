# 🏛️ Cultura Rondônia - Agregador de Eventos

Este é um projeto acadêmico para a disciplina de Programação para Dispositivos Móveis. O objetivo é desenvolver um aplicativo Android nativo que sirva como um agregador de eventos culturais e notícias para o estado de Rondônia, com foco inicial em Porto Velho.

O aplicativo resolve o problema da informação fragmentada, onde eventos públicos são divulgados em múltiplos portais (como o da Funcultural e da Sejucel), mas não são centralizados em um único local de fácil acesso para o cidadão.

---

## 🚀 Arquitetura do Projeto

Este projeto é dividido em três partes principais:

 Este projeto é dividido em três partes principais:
1. **Backend (O Robô Scraper):**  
   Script em Python (`scraper.py`) que visita periodicamente os sites de notícias culturais (Funcultural, Sejucel) e raspa os dados (títulos, imagens, descrições, data de publicação). Inclui lógica de limpeza de HTML, deduplicação, interleaving de imagens e ordenação por data.  
   Também realiza commit e push automático para o GitHub quando executado localmente.

2.  **API (O JSON):**  
   O scraper consolida os dados em `eventos.json` e `eventos_index.json`, hospedados via GitHub Pages.  
   Servem como uma API RESTful gratuita, acessível publicamente

3.  **Frontend (O App Android):**  
   Aplicativo nativo em Java que consome os dados via Retrofit.  
   Exibe os eventos em uma interface limpa com destaques, listas e ordenação por data de publicação.
    

## 🛠️ Tecnologias Utilizadas

### Backend (Scraper)
 **Python 3**
 **Requests** – Requisições HTTP
 **BeautifulSoup4** – Parsing de HTML
 **Hashlib** – Geração de IDs únicos
 **Datetime** – Interpretação de datas relativas (ex: "há 1 semana")
 **Git subprocess** – Commit e push automático local


### Frontend (Aplicativo Android)
* **Java**
* **Android SDK**
* **Retrofit:** Para o consumo da API (JSON).
* **Glide:** Para carregamento e cache de imagens (os banners dos eventos).
* **RecyclerView:** Para exibir as listas de "Destaques" (horizontal) e "Próximos Eventos" (vertical).
* **CardView:** Para o design dos itens da lista.
**Ordenação por data** – Eventos mais recentes primeiro

## 🏁 Status do Projeto

- [x] **Backend:** Scraper da Funcultural completo com data de publicação
- [ ] **Backend:** Adicionar scraper da Sejucel
- [x] **API:** JSON hospedado com sucesso no GitHub Pages
- [x] **App:** Estrutura base do Android (Retrofit, Adapters, Layouts) implementada
- [x] **App:** Ordenação por data de publicação
- [ ] **App:** Tela de detalhes do evento
- [x] **App:** Filtro por palavra-chave ou tipo de evento

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
