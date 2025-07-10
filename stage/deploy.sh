#!/bin/bash
set -e

echo "Деплой Star Burger"

echo "Шаг 1. Сборка фронтенда (Parcel)"
docker build -t starburger-frontend -f frontend/Dockerfile .

echo "Шаг 2. Копируем бандлы в bundles/"
docker rm -f frontend-temp || true
docker create --name frontend-temp starburger-frontend
docker cp frontend-temp:/app/bundles/. ./bundles/
docker rm frontend-temp

echo "Шаг 3. Сборка Django-статики"
docker compose -f docker-compose.yml -f stage/docker-compose.yml run --rm backend python manage.py collectstatic --noinput

echo "Шаг 4. Применяем миграции"
docker compose -f docker-compose.yml -f stage/docker-compose.yml run --rm backend python manage.py migrate

echo "Шаг 5. Запускаем контейнеры"
docker compose -f docker-compose.yml -f stage/docker-compose.yml up -d --build

echo "Деплой завершён"
