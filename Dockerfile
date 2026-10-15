# Всероссийская Федерация Литрбола (ВФЛ)
# Официальный образ для бесплатного деплоя (Render, Koyeb, Railway, VPS)
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для сборки и Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Порт по умолчанию для WebApp
ENV PORT=8080
EXPOSE 8080

RUN chmod +x start.sh

CMD ["./start.sh"]
