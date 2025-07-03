#!/bin/bash
set -e

REMOTE_USER=root
REMOTE_HOST=starburger-root
REMOTE_DIR=/opt/star-burger

echo "Создаём архив проекта"
tar czf star-burger.tar.gz \
  --exclude=star-burger.tar.gz \
  --exclude=.env \
  --exclude=media \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.venv \
  --exclude=.git \
  --exclude=.idea \
  .

echo "Копируем архив на сервер"
scp star-burger.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:/tmp/

echo "Разворачиваем проект на сервере"
ssh ${REMOTE_USER}@${REMOTE_HOST} <<EOF
  set -e
  cd /opt
  if [ -d ${REMOTE_DIR} ]; then
    rm -rf ${REMOTE_DIR}_old || true
    mv ${REMOTE_DIR} ${REMOTE_DIR}_old
  fi
  mkdir -p ${REMOTE_DIR}
  tar xzf /tmp/star-burger.tar.gz -C ${REMOTE_DIR}
  cp -n ${REMOTE_DIR}_old/.env ${REMOTE_DIR}/ || true
  cp -r ${REMOTE_DIR}_old/media ${REMOTE_DIR}/ || true
  cd ${REMOTE_DIR}

  echo "Останавливаем старые контейнеры"
  docker compose -f docker-compose.yml -f docker-compose.prod.yml down

  echo "Собираем новые образы"
  docker compose -f docker-compose.yml -f docker-compose.prod.yml build

  echo "Запускаем контейнеры"
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
EOF

echo "Удаляем временный архив..."
rm star-burger.tar.gz

echo "Деплой завершён успешно."
