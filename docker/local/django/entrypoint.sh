#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# في Render، قد لا نحتاج لانتظار قاعدة البيانات باستخدام nc لأنها خدمة مدارة
# ولكن إذا كنا نعمل محلياً، سننتظرها.
if [ -z "${RENDER:-}" ]; then
    DB_HOST=${POSTGRES_HOST:-db}
    DB_PORT=${POSTGRES_PORT:-5432}
    
    # تحقق من وجود nc قبل استخدامه
    if command -v nc &> /dev/null; then
        echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
        while ! nc -z $DB_HOST $DB_PORT; do
          sleep 0.5
        done
        echo "PostgreSQL started"
    fi
fi

exec "$@"