FROM python:3.13-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# تثبيت متطلبات النظام (بما فيها netcat للانتظار)
RUN apt-get update \
  && apt-get install -y build-essential libpq-dev gettext netcat-openbsd \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip  

# تثبيت مكتبات بايثون
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# 🛑🛑 الإضافة الحاسمة: نسخ كود المشروع بالكامل إلى داخل الحاوية 🛑🛑
COPY . /app

# إعداد سكربتات التشغيل
COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./docker/local/django/start.sh /start.sh
RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/entrypoint.sh"]