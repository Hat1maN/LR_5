# 1. Базовый образ
FROM python:3.10-slim

# 2. Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 3. Создаем папку приложения
WORKDIR /app

# 4. Копируем зависимости
COPY requirements.txt /app/

# 5. Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 6. Копируем проект внутрь контейнера
COPY . /app/

# 7. Собираем статические файлы (для продакшена)
RUN python manage.py collectstatic --noinput

# 8. Команда по умолчанию (миграции + запуск сервера)
CMD ["sh", "-c", "python manage.py migrate && gunicorn brands_project.wsgi:application --bind 0.0.0.0:8000"]