#!/bin/bash
set -e

echo "Деплой Star Burger"

echo "Сборка фронтенда (Parcel)"
docker build -t starburger-frontend -f frontend/Dockerfile .

echo "Копируем бандлы в bundles/"
docker create --name frontend-temp starburger-frontend
docker cp frontend-temp:/app/bundles/. ./bundles/
docker rm frontend-temp

echo "Сборка и запуск backend"
docker compose -f docker-compose.yml -f stage/docker-compose.yml up -d --build

echo "Применяем миграции"
docker compose -f docker-compose.yml -f stage/docker-compose.yml exec backend python manage.py migrate

echo "Собираем Django-статику"
docker compose -f docker-compose.yml -f stage/docker-compose.yml exec backend python manage.py collectstatic --noinput

echo "Деплой завершён"
