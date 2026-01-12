# Usa uma versão leve do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Evita arquivos .pyc e logs em buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto para dentro do container
COPY . .

# Cria a pasta instance (apenas por garantia, o volume vai sobrepor)
RUN mkdir -p instance

# Expõe a porta 5005
EXPOSE 5005

# Comando para iniciar o servidor
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5005", "run:app"]