# Django XML/JSON App

## Описание
Приложение на Django для работы с данными о марках:  
- Ввод через HTML-форму с последующим сохранением в XML  
- Загрузка XML-файлов на сервер с валидацией  
- Просмотр содержимого всех XML-файлов на сайте  

Все настройки формы, сообщений и пути к файлам централизованы в `brands_app/config.py`.  
Добавление новых полей и изменение текста осуществляется только через этот файл.

## Установка и запуск

1. Клонировать репозиторий или скачать файлы:
```bash
git clone <https://github.com/Hat1maN/LR_5>
cd <LR5>
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Linux/macOS
pip install django lxml
python manage.py runserver
Перейти в браузере:
http://127.0.0.1:8000/ — форма добавления марки
http://127.0.0.1:8000/upload/ — загрузка XML
http://127.0.0.1:8000/list/ — просмотр всех XML


# ДЛЯ ЛАБЫ 5

git clone https://github.com/Hat1maN/LR_5.git
cd LR_5
# Создай файл .env
cat > .env << EOF
POSTGRES_DB=brands_db
POSTGRES_USER=brands_user
POSTGRES_PASSWORD=12345
EOF
генерация секретного ключа - python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 

либо безопасный ключ - django-insecure-+8x3d8!k#r@9q2v&f5^m*p(l_j)h7g2a1c4e6u0n8i3o5y_t9r

# Запусти проект одной командой
docker-compose up -d --build
# Проверь, что всё работает
docker-compose ps
# Открой в браузере
http://localhost:8000 или http://127.0.0.1:8000

#миграции
docker-compose exec web python manage.py migrate

#Если вообще не знаешь IP (резервный вариант)
Добавь в docker-compose.yml вот эту строчку в сервис web:
ports:
  - "0.0.0.0:8000:8000"    # вместо просто "8000:8000"

#Как остановить
docker-compose down