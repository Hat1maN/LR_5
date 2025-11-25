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
git clone <https://github.com/Hat1maN/LR_3>
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

# LR_5: Django Brands App with Docker and PostgreSQL

Это приложение для управления брендами (CRUD, XML-upload, поиск). Докеризовано с PostgreSQL.

## Требования
- Docker и Docker Compose
- Python 3.10+ (для локальной разработки)

## Запуск в разработке
1. Клонируйте репозиторий: `git clone https://github.com/Hat1maN/LR_5.git`
2. Создайте `.env` (см. пример в инструкции).
3. Запустите: `docker-compose up -d --build`
4. Примените миграции: `docker-compose exec web python manage.py migrate`
5. Создайте superuser: `docker-compose exec web python manage.py createsuperuser`
6. Доступ: http://localhost:8000 (admin: /admin/)

## Запуск в production
- В `.env` установите DEBUG=False, сильный SECRET_KEY.
- Добавьте reverse-proxy (nginx) для static/media.
- Запустите: `docker-compose -f docker-compose.yml up -d`

## Миграция данных из SQLite
1. Экспорт: `python manage.py dumpdata brands_app.Brand > data.json`
2. В Docker: `docker-compose exec web python manage.py loaddata data.json`

## Структура
- `brands_app/`: Основное приложение.
- `Dockerfile`: Для web.
- `docker-compose.yml`: Оркестрация.
- Volumes: Для DB, static, media.

Функционал: Добавление брендов (DB/XML), поиск (AJAX), CRUD, просмотр.