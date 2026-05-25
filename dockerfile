FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости для Edge (без apt-key)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && wget -q -O - https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list \
    && apt-get update && apt-get install -y microsoft-edge-stable \
    && rm -rf /var/lib/apt/lists/*

# Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаём .env из примера если нет
RUN test -f .env || cp .env.example .env

EXPOSE 8000

CMD ["python", "simple_web_api.py"]