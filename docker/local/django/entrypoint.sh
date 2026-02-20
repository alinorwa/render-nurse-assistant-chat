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

# ✅ تنفيذ الترحيلات هنا (مهم جداً)
python manage.py migrate

# ✅ إنشاء مستخدم مشرف (مرة واحدة فقط)
python manage.py shell -c "
from apps.accounts.models import User
import os

# فقط نفذ إذا كان هذا هو Render وليس محلياً
if os.getenv('RENDER'):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='alialrubay499@gmail.com',
            password='admin123',
            full_name='user admin'
        )
        print('✅ Superuser created on Render')
    else:
        print('✅ Superuser already exists')
"

# ✅ استدعاء start.sh
exec "$@"