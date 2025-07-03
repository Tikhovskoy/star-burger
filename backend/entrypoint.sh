#!/bin/bash
set -e

echo "Применяем миграции..."
python manage.py migrate

echo "Собираем статику..."
python manage.py collectstatic --noinput

echo "Запускаем Gunicorn..."
gunicorn -b 0.0.0.0:8000 star_burger.wsgi:application
