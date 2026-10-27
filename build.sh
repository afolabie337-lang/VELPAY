#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py createsuperuser --noinput --email $DJANGO_SUPERUSER_EMAIL --phone_number $DJANGO_SUPERUSER_PHONE || true