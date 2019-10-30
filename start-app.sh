#!/bin/bash

set -e

export PGPASSWORD=${POSTGRES_PASSWORD}

timeout=${DJANGO_DB_TIMEOUT}

echo -n "Waiting on postgres "
while ! nc -z -w 1 ${DJANGO_DB_HOST} ${DJANGO_DB_PORT}; do
  echo -n .
  timeout=$(($timeout-1))
  if [ ${timeout} -lt 1 ]; then
    echo 
    echo "Failed to connect to postgres"
    exit 1
  fi
done

echo succes!

if ! psql -h ${DJANGO_DB_HOST} -p ${DJANGO_DB_PORT} -U postgres ${DJANGO_DB_NAME} -q -c "\du"; then
  if ! psql -h ${DJANGO_DB_HOST} -p ${DJANGO_DB_PORT} -U postgres -c "\du" | awk '{print $1}' | grep -q "^${DJANGO_DB_USER}$"; then
    createuser -h ${DJANGO_DB_HOST} -p ${DJANGO_DB_PORT} -U postgres ${DJANGO_DB_USER}
  fi
  createdb -h ${DJANGO_DB_HOST} -p ${DJANGO_DB_PORT} -U postgres ${DJANGO_DB_NAME} -O ${DJANGO_DB_USER} --encoding='utf-8' --locale=en_US.utf8 --template=template0
  psql -h ${DJANGO_DB_HOST} -p ${DJANGO_DB_PORT} -U postgres -q -c "alter user ${DJANGO_DB_USER} with encrypted password '${DJANGO_DB_PASSWORD}';"

  python manage.py migrate --noinput
  python manage.py loaddata initial_user
  python manage.py loaddata initial_project_templates
fi

python manage.py migrate --noinput

/srv/taiga/generate-frontend-config.py > /srv/taiga/taiga-front/dist/conf.json
chown apache.apache /srv/taiga/media

if [ ! -z "${TAIGA_EVENTS_HOST}" ]; then
  sed -i "s|# Events_placeholder|ProxyPass \"/events\" \"ws://${TAIGA_EVENTS_HOST}:${TAIGA_EVENTS_PORT}/events\"|" /etc/httpd/conf.d/00taiga.conf
fi

httpd -DFOREGROUND
