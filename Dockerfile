# Dockerfile

# Usa a imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia e instala as dependências (requer requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do seu projeto para o contêiner
COPY . /app

# Comando de execução: Roda o seu arquivo principal para iniciar o scraping
# O arquivo 'scraper.py' deve ser capaz de iniciar a raspagem e salvar o JSON.
CMD ["python", "scraper.py"]