#!/bin/bash
set -e

echo "Сборка collectstatic"
docker compose run --rm backend python manage.py collectstatic --noinput

echo "Миграции"
docker compose run --rm backend python manage.py migrate

echo "Запуск контейнеров"
docker compose up -d --build

echo "Готово"
