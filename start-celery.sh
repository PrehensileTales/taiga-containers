#!/bin/bash

set -e

export C_FORCE_ROOT=1

taiga/bin/celery -A taiga worker --concurrency 4 -l INFO --uid apache
