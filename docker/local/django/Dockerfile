FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# تثبيت متطلبات النظام
# netcat-openbsd مفيد للتحقق من الاتصال، لكن ليس إلزامياً في Render
RUN apt-get update \
  && apt-get install -y build-essential libpq-dev gettext \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# نسخ وتثبيت المكتبات
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# نسخ كود المشروع
COPY . /app

# إعطاء صلاحيات لسكربتات التشغيل
COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/local/django/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

# نقطة الدخول
ENTRYPOINT ["/entrypoint.sh"]