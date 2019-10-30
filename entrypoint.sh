#!/bin/bash

set -e


cd /srv/taiga/taiga-back
source taiga/bin/activate

if [ -z "$1" ]; then
  exec /srv/taiga/start-app.sh
fi

if [ "$1" == "app" ]; then
  exec /srv/taiga/start-app.sh "${@:2}"
fi

if [ "$1" == "celery" ]; then
  exec /srv/taiga/start-celery.sh "${@:2}"
fi

if [ "$1" == "events" ]; then
  exec /srv/taiga/start-events.sh "${@:2}"
fi

echo "Unknown component $1, must be one of 'app', 'celery', or 'events'"
