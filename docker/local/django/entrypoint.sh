#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# تحديد هوست قاعدة البيانات (افتراضياً db للدوكر المحلي، وسنغيره في Azure)
# هذا السطر ذكي: إذا لم نحدد POSTGRES_HOST في المتغيرات، سيفترض أنه 'db'
DB_HOST=${POSTGRES_HOST:-db}
DB_PORT=${POSTGRES_PORT:-5432}

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# حلقة انتظار حتى تستجيب قاعدة البيانات
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done

echo "PostgreSQL started"

exec "$@"