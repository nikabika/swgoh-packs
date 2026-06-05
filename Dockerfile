FROM python:3.11-slim

# Установка системных зависимостей для curl_cffi
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libssl-dev \
    libffi-dev \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .

# Установка Python-пакетов
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY bot.py .

# Запуск бота
CMD ["python", "bot.py"]
