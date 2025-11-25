# 1. Базовый образ
FROM python:3.10-slim

# 2. Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends

# 3. Создаем папку приложения
WORKDIR /app

# 4. Копируем зависимости
COPY requirements.txt /app/

# 5. Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем проект внутрь контейнера
COPY . /app/

# 7. Команда по умолчанию (запуск сервера)
CMD ["gunicorn", "brands_project.wsgi:application", "--bind", "0.0.0.0:8000"]
