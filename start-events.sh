#!/bin/bash

set -e

cd /srv/taiga/taiga-events

URL="amqp://${RABBITMQ_DEFAULT_USER}:${RABBITMQ_DEFAULT_PASS}@${RABBITMQ_SERVER}/${RABBITMQ_DEFAULT_VHOST}"

echo "
{
    \"url\": \"${URL}\",
    \"secret\": \"${DJANGO_SECRET_KEY}\",
    \"webSocketServer\": {
        \"port\": ${TAIGA_EVENTS_PORT} 
    }
}
" > /srv/taiga/taiga-events/config.json

/bin/bash -c "node_modules/coffeescript/bin/coffee index.coffee"
