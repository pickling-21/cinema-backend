#!/usr/bin/env bash

set -e


chown www-data:www-data /var/log

python manage.py makemigrations --no-input

python manage.py migrate --noinput

python manage.py collectstatic --noinput

uwsgi --strict --ini /etc/app/uwsgi.ini

