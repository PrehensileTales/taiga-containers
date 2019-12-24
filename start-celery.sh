#!/bin/bash

set -e

export C_FORCE_ROOT=1

if [ -z "${TAIGA_CELERY_PROCESSES}" ]; then
  echo "TAIGA_CELERY_PROCESSES not set, defaulting to 4!"
  TAIGA_CELERY_PROCESSES=4
fi

taiga/bin/celery -A taiga worker --concurrency ${TAIGA_CELERY_PROCESSES} -l INFO --uid apache
