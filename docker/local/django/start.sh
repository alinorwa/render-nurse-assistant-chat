#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --no-input

# Render يمرر المنفذ في متغير PORT
PORT=${PORT:-8000}
echo "Starting Daphne Server on port $PORT..."

# تشغيل Daphne
daphne -b 0.0.0.0 -p $PORT config.asgi:application