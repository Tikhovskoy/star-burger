#!/bin/bash
set -e

echo "Сборка collectstatic"
docker compose -f production/docker-compose.yml run --rm backend python manage.py collectstatic --noinput

echo "Миграции"
docker compose -f production/docker-compose.yml run --rm backend python manage.py migrate

echo "Запуск контейнеров"
docker compose -f production/docker-compose.yml up -d --build

echo "Готово"
