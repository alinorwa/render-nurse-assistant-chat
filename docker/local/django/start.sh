#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting Daphne Server..."
PORT=${PORT:-8000}
daphne -b 0.0.0.0 -p $PORT config.asgi:application